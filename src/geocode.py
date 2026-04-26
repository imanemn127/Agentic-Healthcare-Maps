"""
Geocode facilities using Nominatim with progressive fallback.
Reads data/scored_facilities.jsonl → writes data/geocoded_facilities.csv.
"""

import argparse
import json
import random
from pathlib import Path

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm

IN_PATH    = Path("data/scored_facilities.jsonl")
OUT_CSV    = Path("data/geocoded_facilities.csv")
CACHE_PATH = Path("data/geocode_cache.json")

# Approximate centroids for all Indian states/UTs
STATE_CENTROIDS = {
    "Andhra Pradesh":    (15.9129, 79.7400),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Assam":             (26.2006, 92.9376),
    "Bihar":             (25.0961, 85.3131),
    "Chhattisgarh":      (21.2787, 81.8661),
    "Goa":               (15.2993, 74.1240),
    "Gujarat":           (22.2587, 71.1924),
    "Haryana":           (29.0588, 76.0856),
    "Himachal Pradesh":  (31.1048, 77.1734),
    "Jharkhand":         (23.6102, 85.2799),
    "Karnataka":         (15.3173, 75.7139),
    "Kerala":            (10.8505, 76.2711),
    "Madhya Pradesh":    (22.9734, 78.6569),
    "Maharashtra":       (19.7515, 75.7139),
    "Manipur":           (24.6637, 93.9063),
    "Meghalaya":         (25.4670, 91.3662),
    "Mizoram":           (23.1645, 92.9376),
    "Nagaland":          (26.1584, 94.5624),
    "Odisha":            (20.9517, 85.0985),
    "Punjab":            (31.1471, 75.3412),
    "Rajasthan":         (27.0238, 74.2179),
    "Sikkim":            (27.5330, 88.5122),
    "Tamil Nadu":        (11.1271, 78.6569),
    "Telangana":         (18.1124, 79.0193),
    "Tripura":           (23.9408, 91.9882),
    "Uttar Pradesh":     (26.8467, 80.9462),
    "Uttarakhand":       (30.0668, 79.0193),
    "West Bengal":       (22.9868, 87.8550),
    "Delhi":             (28.7041, 77.1025),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Ladakh":            (34.1526, 77.5771),
    "Puducherry":        (11.9416, 79.8083),
    "Chandigarh":        (30.7333, 76.7794),
    "Andaman and Nicobar Islands": (11.7401, 92.6586),
}

STATE_ALIASES = {
    "u.p.": "Uttar Pradesh",  "up": "Uttar Pradesh",
    "m.p.": "Madhya Pradesh", "mp": "Madhya Pradesh",
    "t.n.": "Tamil Nadu",     "tn": "Tamil Nadu",
    "w.b.": "West Bengal",    "wb": "West Bengal",
    "a.p.": "Andhra Pradesh", "ap": "Andhra Pradesh",
    "j&k":  "Jammu and Kashmir",
    "hp":   "Himachal Pradesh",
    "uk":   "Uttarakhand",
    "orissa": "Odisha",
}

GEO_SCORE_MAP = {
    "precise":           1.0,
    "city":              0.7,
    "district":          0.4,
    "state_centroid":    0.2,
    "random":            0.05,
}


def normalise_state(state):
    if not state:
        return None
    key = str(state).strip().lower()
    return STATE_ALIASES.get(key, str(state).strip().title())


def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def try_geocode(fn, query, cache):
    if query in cache:
        e = cache[query]
        return e.get("lat"), e.get("lon")
    try:
        loc = fn(query, country_codes="in", language="en")
        if loc:
            cache[query] = {"lat": loc.latitude, "lon": loc.longitude}
            return loc.latitude, loc.longitude
    except Exception:
        pass
    cache[query] = {"lat": None, "lon": None}
    return None, None


def geocode_record(rec, fn, cache):
    name  = rec.get("facility_name", "")
    city  = rec.get("city", "") or ""
    dist  = rec.get("district", "") or ""
    state = normalise_state(rec.get("state")) or ""

    # Level 1: full address
    if name and city and state:
        lat, lon = try_geocode(fn, f"{name}, {city}, {dist}, {state}, India", cache)
        if lat:
            return lat, lon, "precise"

    # Level 2: city + state
    if city and state:
        lat, lon = try_geocode(fn, f"{city}, {state}, India", cache)
        if lat:
            return lat, lon, "city"

    # Level 3: district + state
    if dist and state:
        lat, lon = try_geocode(fn, f"{dist}, {state}, India", cache)
        if lat:
            return lat, lon, "district"

    # Level 4: state centroid
    if state in STATE_CENTROIDS:
        return *STATE_CENTROIDS[state], "state_centroid"

    # Level 5: random point within India
    return round(random.uniform(8.0, 37.0), 4), round(random.uniform(68.0, 97.0), 4), "random"


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
    parser = argparse.ArgumentParser(description="Geocode scored facilities")
    parser.parse_args()

    if not IN_PATH.exists():
        print(f"ERROR: {IN_PATH} not found. Run trust_scorer first.")
        return

    print(f"Loading {IN_PATH} ...")
    records = load_records()
    print(f"Loaded {len(records)} records.")

    cache = load_cache()
    print(f"Cache: {len(cache)} entries.")

    geolocator = Nominatim(user_agent="agentic_healthcare_maps")
    fn = RateLimiter(geolocator.geocode, min_delay_seconds=1.1, error_wait_seconds=5.0)

    results = []
    stats = {}

    for rec in tqdm(records, desc="Geocoding"):
        lat, lon, method = geocode_record(rec, fn, cache)
        geo_score = GEO_SCORE_MAP.get(method, 0.0)
        stats[method] = stats.get(method, 0) + 1

        results.append({
            **rec,
            "latitude":         lat,
            "longitude":        lon,
            "geocode_method":   method,
            "geocode_score":    geo_score,
        })

    save_cache(cache)

    df = pd.DataFrame(results)
    # Flatten list columns to pipe-separated strings for CSV storage
    for col in ["evidence_sentences", "rule_flags", "llm_contradictions"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: " | ".join(str(x) for x in v) if isinstance(v, list) else (v or "")
            )

    OUT_CSV.parent.mkdir(exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")

    real = sum(v for k, v in stats.items() if k not in ("random",))
    print(f"\nDone. Saved to {OUT_CSV}")
    print(f"Total: {len(results)} | Real geocode: {real} ({real/len(results)*100:.1f}%)")
    print(f"Methods: {stats}")


if __name__ == "__main__":
    main()
