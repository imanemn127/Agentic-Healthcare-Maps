"""
Natural-language query agent over the geocoded facility dataset.
Parses intent with Groq (primary) or Gemini (fallback), filters the CSV,
ranks by trust + distance.
"""

import json
import os
import re
import time
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
GROQ_KEY     = os.getenv("GROQ_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
GROQ_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")

# Always resolve relative to this file so CWD doesn't matter
_HERE     = Path(__file__).resolve().parent
DATA_PATH = _HERE.parent / "data" / "geocoded_facilities.csv"

_groq_client   = None
_gemini_client = None


def _call_groq(prompt):
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_KEY)
    resp = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512,
    )
    return resp.choices[0].message.content


def _call_gemini(prompt):
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_KEY)
    resp = _gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text


def call_llm(prompt):
    # Prefer Groq if key is available (faster, no quota issues for hackathon)
    if GROQ_KEY:
        try:
            return _call_groq(prompt)
        except Exception as e:
            if GEMINI_KEY:
                pass  # fall through to Gemini
            else:
                raise RuntimeError(f"Groq failed: {e}")
    if GEMINI_KEY:
        try:
            return _call_gemini(prompt)
        except Exception as e:
            time.sleep(1)
            raise RuntimeError(f"Gemini failed: {e}")
    raise RuntimeError("No LLM provider available. Set GROQ_API_KEY or GEMINI_API_KEY in .env.")


INTENT_PROMPT = """\
Parse this healthcare facility query and return ONLY a JSON object with no extra text.

Query: "{query}"

Return exactly this structure:
{{
  "required_capabilities": {{
    "has_icu": true or false or null,
    "has_emergency_trauma": true or false or null,
    "has_oncology": true or false or null,
    "has_dialysis": true or false or null,
    "has_anesthesiologist": true or false or null,
    "supports_appendectomy": true or false or null
  }},
  "filters": {{
    "state": "exact Indian state name in lowercase or null",
    "facility_type": "hospital or clinic or null",
    "ownership": "government or private or trust or null",
    "min_trust_score": 0.0
  }},
  "intent_summary": "one sentence describing what the user needs"
}}

Rules:
- Set a capability to true ONLY if the query explicitly requires it. Otherwise null.
- State must be the full lowercase name (e.g. "maharashtra", "karnataka", "bihar").
- Return ONLY the JSON object. No markdown, no explanation.
"""


def parse_json(text):
    if not text:
        return {}
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def load_data():
    df = pd.read_csv(DATA_PATH, low_memory=False)

    bool_cols = ["has_icu", "has_emergency_trauma", "has_oncology",
                 "has_dialysis", "has_anesthesiologist", "supports_appendectomy",
                 "part_time_doctors"]
    for col in bool_cols:
        if col in df.columns:
            # Map every truthy/falsy variant; leave NaN as NaN (don't coerce to False)
            df[col] = df[col].map(
                {True: True, False: False,
                 "True": True, "False": False,
                 "true": True, "false": False,
                 1: True, 0: False,
                 "1": True, "0": False}
            )

    for col in ["final_trust_score", "latitude", "longitude", "beds_count",
                "rule_score", "llm_score", "geocode_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["final_trust_score"] = df["final_trust_score"].fillna(0)

    for col in ["state", "facility_type", "ownership", "trust_tier"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip().str.lower()

    return df


def parse_intent(query):
    prompt = INTENT_PROMPT.format(query=query)
    try:
        raw = call_llm(prompt)
    except Exception:
        return {"required_capabilities": {}, "filters": {}, "intent_summary": query}
    if not raw:
        return {"required_capabilities": {}, "filters": {}, "intent_summary": query}
    parsed = parse_json(raw)
    if not parsed:
        return {"required_capabilities": {}, "filters": {}, "intent_summary": query}
    return parsed


def _fuzzy_state_match(df_states_series, target):
    """Return a boolean mask for rows whose state contains the target string."""
    t = target.strip().lower()
    return df_states_series.str.contains(t, regex=False)


def apply_filters(df, intent):
    data = df.copy()
    filters = intent.get("filters") or {}
    caps    = intent.get("required_capabilities") or {}

    state_val = filters.get("state")
    if state_val:
        # Try exact match first, then substring (handles LLM casing quirks)
        exact = data[data["state"] == state_val.strip().lower()]
        if not exact.empty:
            data = exact
        else:
            fuzzy = data[_fuzzy_state_match(data["state"], state_val)]
            if not fuzzy.empty:
                data = fuzzy

    ftype = filters.get("facility_type")
    if ftype:
        exact = data[data["facility_type"] == ftype.strip().lower()]
        if not exact.empty:
            data = exact
        else:
            data = data[data["facility_type"].str.contains(ftype.strip().lower(), regex=False)]

    ownership = filters.get("ownership")
    if ownership:
        data = data[data["ownership"] == ownership.strip().lower()]

    min_trust = filters.get("min_trust_score")
    if min_trust:
        try:
            data = data[data["final_trust_score"] >= float(min_trust)]
        except (TypeError, ValueError):
            pass

    # Capability filters: only filter on True; skip NaN rows (don't discard unknown)
    for cap, required in caps.items():
        if required is True and cap in data.columns:
            data = data[data[cap] == True]

    return data


def run_query(query, location=None):
    """
    Main entry point. Returns a dict with intent, filters, and top results.
    location: (lat, lon) tuple or None
    """
    df = load_data()

    intent   = parse_intent(query)
    filtered = apply_filters(df, intent)

    # Fallback: if LLM hallucinated filters that killed all results, relax to state-only
    if filtered.empty:
        state_val = (intent.get("filters") or {}).get("state")
        if state_val:
            state_only_intent = {
                "required_capabilities": {},
                "filters": {"state": state_val},
                "intent_summary": intent.get("intent_summary", query),
            }
            filtered = apply_filters(df, state_only_intent)

    # Last resort: no filters at all, return top-trust facilities
    if filtered.empty:
        filtered = df.copy()

    ranked = filtered.copy()

    if location:
        ref_lat, ref_lon = location
        valid = ranked.dropna(subset=["latitude", "longitude"]).copy()
        valid["distance_km"] = valid.apply(
            lambda r: haversine(ref_lat, ref_lon, r["latitude"], r["longitude"]), axis=1
        )
        max_dist = valid["distance_km"].max() or 1.0
        valid["rank_score"] = valid["final_trust_score"] - 0.3 * (valid["distance_km"] / max_dist)
        ranked = valid.sort_values("rank_score", ascending=False)
    else:
        ranked = ranked.sort_values("final_trust_score", ascending=False)

    top = ranked.head(5)

    results = []
    for _, row in top.iterrows():
        ev_raw   = str(row.get("evidence_sentences", ""))
        evidence = [s.strip() for s in ev_raw.split(" | ") if s.strip() and s.strip() != "nan"]

        dist_val = row.get("distance_km")
        dist_out = round(float(dist_val), 1) if dist_val is not None and pd.notna(dist_val) else None

        caps_out = {}
        for cap in ["has_icu", "has_emergency_trauma", "has_oncology",
                    "has_dialysis", "has_anesthesiologist", "supports_appendectomy"]:
            v = row.get(cap)
            caps_out[cap] = None if (v is None or (isinstance(v, float) and pd.isna(v))) else bool(v)

        results.append({
            "facility_name":      str(row.get("facility_name", "Unknown")),
            "facility_type":      str(row.get("facility_type", "")),
            "city":               str(row.get("city", "")),
            "state":              str(row.get("state", "")),
            "trust_score":        round(float(row.get("final_trust_score", 0)), 3),
            "trust_tier":         str(row.get("trust_tier", "unverified")),
            "distance_km":        dist_out,
            "evidence_sentences": evidence[:3],
            "capabilities":       caps_out,
        })

    return {
        "intent_summary":        intent.get("intent_summary", query),
        "filters_applied":       intent.get("filters") or {},
        "capabilities_required": intent.get("required_capabilities") or {},
        "total_matched":         len(filtered),
        "results":               results,
    }


if __name__ == "__main__":
    import sys, pprint
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "ICU hospital in Maharashtra"
    pprint.pprint(run_query(q))
