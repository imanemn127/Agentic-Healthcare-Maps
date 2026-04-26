"""
Trust scoring: rule-based checks + LLM validation → final_trust_score.
Reads data/extracted_facilities.jsonl → writes data/scored_facilities.jsonl.

Uses Gemini by default; falls back to Groq if quota exhausted.
--no-llm flag skips LLM validation entirely (rule-based only).
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
GROQ_KEY     = os.getenv("GROQ_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
GROQ_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")

IN_PATH  = Path("data/extracted_facilities.jsonl")
OUT_PATH = Path("data/scored_facilities.jsonl")

W_RULE = 0.5
W_LLM  = 0.5

VALIDATE_PROMPT = """\
You are a medical data auditor. Review this extracted Indian healthcare facility record for internal consistency.

Check for issues like:
- PHC or small clinic claiming ICU / surgery capability
- Closed facility claiming active emergency services
- Bed count inconsistent with facility type
- Government name but private ownership

Record:
{record}

Return ONLY a JSON object:
{{
  "consistency_score": <float 0.0-1.0>,
  "contradictions": ["list of specific issues, or empty list"]
}}
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
    resp = _get_gemini().models.generate_content(model=GEMINI_MODEL, contents=prompt)
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
    resp = _get_groq().chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return resp.choices[0].message.content


# ── Unified caller ────────────────────────────────────────────────────────────

_force_groq = False


def call_llm(prompt):
    global _force_groq

    if not _force_groq and GEMINI_KEY:
        try:
            return _call_gemini(prompt)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                if GROQ_KEY:
                    print("\n[Gemini quota] Switching to Groq.")
                    _force_groq = True
                else:
                    print("\n[QUOTA EXHAUSTED] Add GROQ_API_KEY to .env, or use --no-llm.")
                    raise SystemExit(1)
            else:
                print(f"  [gemini error] {e}")
                time.sleep(2)
                return ""

    if GROQ_KEY:
        try:
            return _call_groq(prompt)
        except Exception as e:
            print(f"  [groq error] {e}")
            time.sleep(3)
            return ""

    return ""


# ── Scoring logic ─────────────────────────────────────────────────────────────

def parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def rule_score(rec):
    score = 1.0
    flags = []

    ftype   = str(rec.get("facility_type", "")).lower()
    beds    = rec.get("beds_count")
    name    = str(rec.get("facility_name", "")).lower()
    own     = str(rec.get("ownership", "")).lower()
    is_op   = rec.get("is_operational")
    has_em  = rec.get("has_emergency_trauma")
    has_icu = rec.get("has_icu")

    if ftype == "phc" and has_icu:
        score -= 0.4
        flags.append("PHC claiming ICU")

    if ftype == "phc" and beds and beds > 50:
        score -= 0.3
        flags.append(f"PHC with {beds} beds (unrealistic)")

    if is_op is False and has_em is True:
        score -= 0.5
        flags.append("Closed facility with active emergency services")

    if "government" in name and own == "private":
        score -= 0.4
        flags.append("'Government' in name but ownership=private")

    if beds and beds > 2000:
        score -= 0.3
        flags.append(f"Unrealistic bed count: {beds}")

    return max(0.0, round(score, 4)), flags


def llm_validate(rec):
    prompt = VALIDATE_PROMPT.format(record=json.dumps(rec, ensure_ascii=False, default=str))
    raw = call_llm(prompt)
    if not raw:
        return 0.5, []
    obj = parse_json(raw)
    return round(float(obj.get("consistency_score", 0.5)), 4), obj.get("contradictions", [])


def assign_tier(score):
    if score >= 0.75: return "high"
    if score >= 0.50: return "medium"
    if score >= 0.30: return "low"
    return "unverified"


# ── Entry point ───────────────────────────────────────────────────────────────

def load_records():
    records = []
    with open(IN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm",  action="store_true", help="Skip LLM validation (rule-based only)")
    parser.add_argument("--provider", choices=["gemini", "groq"], default=None)
    args = parser.parse_args()

    global _force_groq
    if args.provider == "groq":
        _force_groq = True

    if not IN_PATH.exists():
        print(f"ERROR: {IN_PATH} not found. Run extractor first.")
        return

    print(f"Loading {IN_PATH} ...")
    records = load_records()
    print(f"Loaded {len(records)} records.")

    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as out_f:
        for rec in tqdm(records, desc="Scoring"):
            rscore, rflags = rule_score(rec)

            if args.no_llm:
                lscore, lcontras = rscore, []
            else:
                lscore, lcontras = llm_validate(rec)
                time.sleep(2)

            final = round(W_RULE * rscore + W_LLM * lscore, 4)

            scored = {
                **rec,
                "rule_score":         rscore,
                "llm_score":          lscore,
                "final_trust_score":  final,
                "trust_tier":         assign_tier(final),
                "rule_flags":         rflags,
                "llm_contradictions": lcontras,
            }
            out_f.write(json.dumps(scored, ensure_ascii=False) + "\n")

    print(f"Done. Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
