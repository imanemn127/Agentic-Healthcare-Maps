"""
LLM extraction of structured healthcare fields from raw facility records.
Reads data/raw_facilities.xlsx → writes data/extracted_facilities.jsonl.

Provider priority: Gemini (if key works) → Groq (fallback or --provider groq).
Set GROQ_API_KEY in .env to enable Groq.

Flags:
  --limit N              Process only first N records
  --force                Clear checkpoint and reprocess all
  --provider gemini|groq Force a specific provider
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
GROQ_KEY     = os.getenv("GROQ_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
GROQ_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")

RAW_PATH = Path("data/raw_facilities.xlsx")
OUT_PATH = Path("data/extracted_facilities.jsonl")

EXTRACT_PROMPT = """\
You are a healthcare data analyst. Given a raw Indian healthcare facility record, \
extract the following fields and return ONLY a JSON object (no markdown, no explanation).

IMPORTANT for capability fields (has_icu, has_emergency_trauma, etc.):
- Use true if the record mentions or implies the capability (e.g. "emergency" → has_emergency_trauma: true)
- Use false if it's a PHC, dispensary, or small clinic (these typically lack ICU/surgery)
- Use null ONLY if the facility type is completely unknown and there is no hint at all
- For hospitals and nursing homes, make a best-guess based on bed count and type — do NOT default to null

Fields to extract:
- facility_name: string (cleaned, expand abbreviations like Govt→Government, Hosp→Hospital)
- facility_type: one of [hospital, clinic, PHC, CHC, nursing_home, diagnostic_center, unknown]
- city: string
- district: string
- state: string (full official name, e.g. "Uttar Pradesh" not "U.P.")
- beds_count: integer or null (parse "~120" or "approx 50" as integers)
- ownership: one of [government, private, trust, NGO, unknown]
- is_operational: true/false/null
- has_icu: true/false/null
- has_emergency_trauma: true/false/null
- has_oncology: true/false/null
- has_dialysis: true/false/null
- has_anesthesiologist: true/false/null
- supports_appendectomy: true/false/null
- part_time_doctors: true/false/null
- trust_score: float 0.0-1.0 (your confidence in the record quality)
- evidence_sentences: list of verbatim or near-verbatim phrases from the input supporting key fields

Raw record:
{raw}
"""


# ── Gemini ────────────────────────────────────────────────────────────────────

_gemini_client = None

def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_KEY)
    return _gemini_client


def _call_gemini(prompt):
    client = _get_gemini()
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text


# ── Groq ──────────────────────────────────────────────────────────────────────

_groq_client = None

def _get_groq():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_KEY)
    return _groq_client


def _call_groq(prompt):
    client = _get_groq()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return resp.choices[0].message.content


# ── Unified caller with auto-fallback ─────────────────────────────────────────

_force_groq = False  # flipped to True once Gemini quota is hit


def call_llm(prompt):
    global _force_groq

    if not _force_groq and GEMINI_KEY:
        try:
            return _call_gemini(prompt), "gemini"
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                if GROQ_KEY:
                    print("\n[Gemini quota] Switching to Groq for remaining records.")
                    _force_groq = True
                else:
                    print("\n[QUOTA EXHAUSTED] Add GROQ_API_KEY to .env and re-run.")
                    raise SystemExit(1)
            else:
                print(f"  [gemini error] {e}")
                time.sleep(2)
                return "", "error"

    if GROQ_KEY:
        try:
            return _call_groq(prompt), "groq"
        except Exception as e:
            print(f"  [groq error] {e}")
            time.sleep(3)
            return "", "error"

    print("ERROR: No LLM provider available. Set GEMINI_API_KEY or GROQ_API_KEY in .env.")
    raise SystemExit(1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def load_done_ids():
    done = set()
    if OUT_PATH.exists():
        with open(OUT_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done.add(json.loads(line)["row_id"])
                    except (KeyError, json.JSONDecodeError):
                        pass
    return done


def append_record(record):
    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def make_stub(row_id, raw):
    return {
        "row_id":                row_id,
        "facility_name":         raw.get("facility_name") or "Unknown",
        "facility_type":         "unknown",
        "city":                  raw.get("city") or "",
        "district":              raw.get("district") or "",
        "state":                 raw.get("state") or "",
        "beds_count":            None,
        "ownership":             "unknown",
        "is_operational":        None,
        "has_icu":               None,
        "has_emergency_trauma":  None,
        "has_oncology":          None,
        "has_dialysis":          None,
        "has_anesthesiologist":  None,
        "supports_appendectomy": None,
        "part_time_doctors":     None,
        "trust_score":           0.0,
        "evidence_sentences":    ["[extraction failed]"],
        "extraction_mode":       "failed",
    }


def extract_one(row):
    row_id = int(row.get("row_id", 0))
    prompt = EXTRACT_PROMPT.format(raw=json.dumps(row, ensure_ascii=False, default=str))
    text, provider = call_llm(prompt)
    if not text:
        return make_stub(row_id, row)
    result = parse_json(text)
    if not result:
        return make_stub(row_id, row)
    result["row_id"] = row_id
    result.setdefault("evidence_sentences", [])
    result.setdefault("trust_score", 0.5)
    result["extraction_mode"] = provider
    return result


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",    type=int,    default=None)
    parser.add_argument("--force",    action="store_true")
    parser.add_argument("--provider", choices=["gemini", "groq"], default=None)
    args = parser.parse_args()

    global _force_groq
    if args.provider == "groq":
        _force_groq = True
        if not GROQ_KEY:
            print("ERROR: --provider groq requires GROQ_API_KEY in .env")
            return

    if not GEMINI_KEY and not GROQ_KEY:
        print("ERROR: Set GEMINI_API_KEY or GROQ_API_KEY in .env")
        return

    if args.force and OUT_PATH.exists():
        OUT_PATH.unlink()
        print("Checkpoint cleared.")

    print(f"Reading {RAW_PATH} ...")
    df = pd.read_excel(RAW_PATH, engine="openpyxl")
    if args.limit:
        df = df.head(args.limit)

    done_ids = load_done_ids()
    pending  = df[~df["row_id"].isin(done_ids)]
    print(f"Total: {len(df)} | Done: {len(done_ids)} | Pending: {len(pending)}")

    if pending.empty:
        print("Nothing to do. Use --force to reprocess.")
        return

    rows = pending.where(pd.notnull(pending), None).to_dict("records")
    for row in tqdm(rows, desc="Extracting"):
        result = extract_one(row)
        append_record(result)
        time.sleep(2)  # ~30 req/min for Groq free tier

    print(f"Done. Checkpoint total: {len(load_done_ids())}")


if __name__ == "__main__":
    main()
