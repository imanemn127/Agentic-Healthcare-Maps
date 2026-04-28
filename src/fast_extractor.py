"""
fast_extractor.py — LLM batch extractor for 10,000 facility records.

Strategy:
  - Batches N records per LLM call (default 20) → 500 calls total for 10k rows
  - Token-bucket rate limiter holds to ≤28 req/min (Groq free tier: 30/min)
  - Single-threaded sequential dispatch avoids burst violations
  - Checkpoint resume: skip already-extracted row_ids
  - Falls back Gemini → Groq automatically on quota hit

Usage:
  python src/fast_extractor.py                  # process all, resume from checkpoint
  python src/fast_extractor.py --force          # clear checkpoint and reprocess all
  python src/fast_extractor.py --limit 200      # first 200 rows only
  python src/fast_extractor.py --batch 20       # records per call (default 20)
  python src/fast_extractor.py --rpm 28         # requests per minute cap (default 28)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import threading
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

_ROOT    = Path(__file__).resolve().parent.parent
RAW_PATH = _ROOT / "data" / "raw_facilities.xlsx"
OUT_PATH = _ROOT / "data" / "extracted_facilities.jsonl"

GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
GROQ_KEY     = os.getenv("GROQ_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
GROQ_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")

# ──────────────────────────────────────────────────────────────────────────────
# BATCH PROMPT
# ──────────────────────────────────────────────────────────────────────────────

BATCH_PROMPT = """\
Extract structured fields from each Indian healthcare facility record below.
Return a JSON array — one object per record, preserving input order.

Each object must have EXACTLY these keys:
  row_id                  — copy from input (integer)
  facility_name           — cleaned/expanded name string
  facility_type           — normalised: Hospital | PHC | CHC | Clinic | Nursing Home |
                            Dispensary | Diagnostic Centre | unknown
  city                    — string or null
  district                — string or null
  state                   — full official Indian state name
  beds_count              — integer (parse "~37", "approx 50", "6 beds") or null
  ownership               — government | private | trust | unknown
  is_operational          — true if Open/Operational/Functioning, false if Closed, null otherwise
  has_icu                 — true/false/null (PHC/Clinic/Dispensary = false by default)
  has_emergency_trauma    — true if 24x7 or emergency ward mentioned, false/null otherwise
  has_oncology            — true only if Oncology in specialties, null otherwise
  has_dialysis            — true only if Dialysis in specialties, null otherwise
  has_anesthesiologist    — true if Anaesthesia in specialties or hospital ≥100 beds, null otherwise
  supports_appendectomy   — true if General Surgery in specialties, null otherwise
  trust_score             — float 0.0–1.0: confidence in record quality
  evidence_sentences      — array of up to 3 verbatim/near-verbatim phrases from input

Normalisation rules:
  - ownership: "gvoernment"/"governmnet" etc → "government"; "prviate" etc → "private"
  - facility_type: "phc"/"PHC (est.)"/"PHC * verify" → "PHC"; "Hosp"/"HOSPITAL" → "Hospital"
  - state: expand abbreviations (U.P.→Uttar Pradesh, M.P.→Madhya Pradesh, T.N.→Tamil Nadu etc.)
  - trust_score: accredited (NABH/ISO/NABL) facilities get +0.15 bonus; records with many
    typos/uncertain markers (* verify, approx) get slight penalty

Return ONLY the JSON array. No markdown fences, no explanations, nothing else.

Records:
{records_json}
"""

# ──────────────────────────────────────────────────────────────────────────────
# TOKEN-BUCKET RATE LIMITER
# ──────────────────────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding-window rate limiter.
    Tracks the last `limit` call timestamps and blocks until a slot opens.
    Adds a small jitter to prevent thundering-herd on burst recovery.
    """

    def __init__(self, limit: int = 25) -> None:
        self._limit = limit
        self._calls: list[float] = []
        self._lock  = threading.Lock()

    def acquire(self) -> None:
        import random
        while True:
            with self._lock:
                now = time.monotonic()
                self._calls = [t for t in self._calls if now - t < 60.0]
                if len(self._calls) < self._limit:
                    self._calls.append(now)
                    return
                wait = 60.0 - (now - self._calls[0]) + 0.1 + random.uniform(0, 0.5)
            time.sleep(max(wait, 0.1))


_limiter: RateLimiter = RateLimiter(28)   # replaced in main() based on --rpm flag

# ──────────────────────────────────────────────────────────────────────────────
# LLM CLIENTS  (thread-safe via threading.local)
# ──────────────────────────────────────────────────────────────────────────────

_groq_local   = threading.local()
_gemini_local = threading.local()
_use_gemini   = threading.Event()   # set when Groq quota is exhausted


def _get_groq():
    if not hasattr(_groq_local, "client"):
        from groq import Groq
        _groq_local.client = Groq(api_key=GROQ_KEY)
    return _groq_local.client


def _get_gemini():
    if not hasattr(_gemini_local, "client"):
        from google import genai
        _gemini_local.client = genai.Client(api_key=GEMINI_KEY)
    return _gemini_local.client


def call_llm(prompt: str, retry: int = 0) -> str:
    """Acquire rate-limit token, dispatch to Groq (primary) or Gemini (fallback)."""
    _limiter.acquire()

    if _use_gemini.is_set() and GEMINI_KEY:
        return _call_gemini(prompt)

    if GROQ_KEY:
        try:
            return _call_groq(prompt)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate_limit" in msg.lower():
                # Back off and retry — rate limiter was too optimistic
                wait = min(120, 10 * (2 ** retry))
                tqdm.write(f"  [rate limit] backing off {wait:.0f}s (retry {retry+1})")
                time.sleep(wait)
                return call_llm(prompt, retry + 1)
            if "413" in msg:
                # Batch too large — caller should reduce batch size
                raise
            if GEMINI_KEY:
                tqdm.write("  [groq quota] switching to Gemini")
                _use_gemini.set()
                return _call_gemini(prompt)
            raise

    if GEMINI_KEY:
        return _call_gemini(prompt)

    raise RuntimeError("No LLM provider available. Set GROQ_API_KEY or GEMINI_API_KEY in .env")


def _call_groq(prompt: str) -> str:
    r = _get_groq().chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4096,
    )
    return r.choices[0].message.content or ""


def _call_gemini(prompt: str) -> str:
    r = _get_gemini().models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return r.text or ""


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def parse_json_array(text: str) -> list:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # Try full array
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    # Fallback: single object wrapped in list
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return [json.loads(text[start:end + 1])]
        except json.JSONDecodeError:
            pass
    return []


def make_stub(row: dict) -> dict:
    return {
        "row_id":                int(row.get("row_id", 0)),
        "facility_name":         str(row.get("facility_name") or "Unknown"),
        "facility_type":         "unknown",
        "city":                  str(row.get("city") or ""),
        "district":              str(row.get("district") or ""),
        "state":                 str(row.get("state") or ""),
        "beds_count":            None,
        "ownership":             "unknown",
        "is_operational":        None,
        "has_icu":               None,
        "has_emergency_trauma":  None,
        "has_oncology":          None,
        "has_dialysis":          None,
        "has_anesthesiologist":  None,
        "supports_appendectomy": None,
        "trust_score":           0.0,
        "evidence_sentences":    ["[extraction failed]"],
        "extraction_mode":       "failed",
    }


def load_done_ids() -> set[int]:
    done: set[int] = set()
    if OUT_PATH.exists():
        with open(OUT_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done.add(int(json.loads(line)["row_id"]))
                    except (KeyError, ValueError, json.JSONDecodeError):
                        pass
    return done


def append_records(records: list[dict]) -> None:
    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# BATCH PROCESSING
# ──────────────────────────────────────────────────────────────────────────────

def process_batch(rows: list[dict]) -> list[dict]:
    slim = [
        {
            "row_id":             r.get("row_id"),
            "facility_name":      r.get("facility_name"),
            "facility_type":      r.get("facility_type"),
            "city":               r.get("city"),
            "district":           r.get("district"),
            "state":              r.get("state"),
            "beds":               r.get("beds"),
            "specialties":        r.get("specialties"),
            "ownership":          r.get("ownership"),
            "operational_status": r.get("operational_status"),
            "emergency_services": r.get("emergency_services"),
            "accreditation":      r.get("accreditation"),
        }
        for r in rows
    ]

    prompt = BATCH_PROMPT.format(
        records_json=json.dumps(slim, ensure_ascii=False, default=str)
    )

    try:
        text = call_llm(prompt)
    except Exception as e:
        tqdm.write(f"  [batch error] {e}")
        return [make_stub(r) for r in rows]

    parsed = parse_json_array(text)

    # Map parsed items back by row_id; fall back to stub for any missing
    result_map: dict[int, dict] = {}
    mode = "gemini" if _use_gemini.is_set() else "groq"
    for item in parsed:
        if isinstance(item, dict):
            try:
                rid = int(item.get("row_id", -1))
                if rid >= 0:
                    item["extraction_mode"] = mode
                    result_map[rid] = item
            except (ValueError, TypeError):
                pass

    results = []
    for r in rows:
        rid = int(r.get("row_id", 0))
        results.append(result_map.get(rid, make_stub(r)))

    return results


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    global _limiter

    parser = argparse.ArgumentParser(description="Fast LLM batch extractor — 10,000 facilities")
    parser.add_argument("--limit",  type=int, default=None, help="Process only first N rows")
    parser.add_argument("--force",  action="store_true",    help="Clear checkpoint and reprocess all")
    parser.add_argument("--batch",  type=int, default=20,   help="Records per LLM call (default 20)")
    parser.add_argument("--rpm",    type=int, default=28,   help="Max requests per minute (default 28)")
    args = parser.parse_args()

    if not GROQ_KEY and not GEMINI_KEY:
        print("ERROR: Set GROQ_API_KEY or GEMINI_API_KEY in .env")
        sys.exit(1)

    _limiter = RateLimiter(args.rpm)

    if args.force and OUT_PATH.exists():
        OUT_PATH.unlink()
        print("Checkpoint cleared.")

    print(f"Loading {RAW_PATH} ...")
    df = pd.read_excel(RAW_PATH, engine="openpyxl")
    if args.limit:
        df = df.head(args.limit)

    df = df.where(pd.notnull(df), None)
    all_rows = df.to_dict("records")

    done_ids = load_done_ids()
    pending  = [r for r in all_rows if int(r.get("row_id", 0)) not in done_ids]

    n_batches = -(-len(pending) // args.batch)   # ceiling division
    est_mins  = n_batches / args.rpm
    provider  = "Groq" if GROQ_KEY and not _use_gemini.is_set() else "Gemini"

    print(f"Total: {len(all_rows):,}  |  Done: {len(done_ids):,}  |  Pending: {len(pending):,}")
    print(f"Batch size: {args.batch}  |  Rate limit: {args.rpm} req/min  |  Provider: {provider}")
    print(f"Batches: {n_batches}  |  Est. time: ~{est_mins:.0f} min\n")

    if not pending:
        print("Nothing to do. Use --force to reprocess.")
        return

    batches = [pending[i:i + args.batch] for i in range(0, len(pending), args.batch)]

    bar = tqdm(total=len(pending), desc="Extracting", unit="rec")

    for batch in batches:
        results = process_batch(batch)
        append_records(results)
        bar.update(len(results))
        # Show running total every 500 records
        done_now = len(done_ids) + bar.n
        if done_now % 500 < args.batch:
            tqdm.write(f"  checkpoint: {done_now:,} records written")

    bar.close()

    total_done = len(load_done_ids())
    mode_label = "Gemini" if _use_gemini.is_set() else "Groq"
    print(f"\nExtraction complete via {mode_label}.")
    print(f"Total records in checkpoint: {total_done:,}")
    print(f"\nNext step:  python src/trust_scorer.py --no-llm")
    print(f"Then:       python src/geocode.py")
    print(f"Then:       python src/map_generator.py")


if __name__ == "__main__":
    main()
