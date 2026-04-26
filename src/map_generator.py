"""
Generate an interactive Folium map of Indian healthcare facilities.
Reads data/geocoded_facilities.csv → writes maps/healthcare_map.html.
"""

import argparse
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster

DATA_PATH   = Path("data/geocoded_facilities.csv")
OUTPUT_PATH = Path("maps/healthcare_map.html")

INDIA_CENTER = [20.5937, 78.9629]
INDIA_ZOOM   = 5

TIER_COLORS = {
    "high":       "#2ecc71",
    "medium":     "#f39c12",
    "low":        "#e74c3c",
    "unverified": "#95a5a6",
}

LEGEND_HTML = """
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:white;
     padding:12px 16px;border-radius:8px;border:1px solid #ccc;
     font-family:Arial,sans-serif;font-size:12px;box-shadow:2px 2px 6px rgba(0,0,0,.25)">
  <b style="font-size:13px">Trust Tier</b><br>
  <span style="color:#2ecc71">&#9679;</span> High (&ge;0.75)<br>
  <span style="color:#f39c12">&#9679;</span> Medium (&ge;0.50)<br>
  <span style="color:#e74c3c">&#9679;</span> Low (&ge;0.30)<br>
  <span style="color:#95a5a6">&#9679;</span> Unverified<br>
  <hr style="margin:5px 0">
  <b>Medical Deserts</b><br>
  <span style="background:#7d3c98;display:inline-block;width:11px;height:11px;border-radius:2px"></span> No high-trust facility
</div>
"""


def build_popup(row):
    name  = row.get("facility_name", "Unknown")
    ftype = str(row.get("facility_type", "")).title()
    city  = row.get("city", "")
    state = row.get("state", "")
    score = row.get("final_trust_score", 0)
    beds  = row.get("beds_count", "N/A")
    em    = "Yes" if row.get("has_emergency_trauma") else "No"
    icu   = "Yes" if row.get("has_icu") else "No"

    try:
        score_str = f"{float(score):.2f}"
    except (TypeError, ValueError):
        score_str = "N/A"

    ev_raw  = str(row.get("evidence_sentences", ""))
    snippet = ev_raw.split(" | ")[0][:100] if ev_raw else ""

    return f"""
    <div style="font-family:Arial,sans-serif;font-size:12px;min-width:190px">
      <b>{name}</b><br>
      {ftype} &bull; {city}, {state}<br>
      Trust: <b>{score_str}</b> &bull; Beds: {beds}<br>
      Emergency: {em} &bull; ICU: {icu}<br>
      <hr style="margin:4px 0"><small><i>"{snippet}…"</i></small>
    </div>"""


def build_desert_grid(df, cell_deg=0.5):
    """Return rectangles for cells with no high-trust facility."""
    high = df[df["final_trust_score"] >= 0.75].dropna(subset=["latitude", "longitude"])
    cells = []
    lat = 6.0
    while lat < 37.5:
        lon = 68.0
        while lon < 97.5:
            count = len(high[
                (high["latitude"] >= lat) & (high["latitude"] < lat + cell_deg) &
                (high["longitude"] >= lon) & (high["longitude"] < lon + cell_deg)
            ])
            if count == 0:
                cells.append((lat, lon))
            lon += cell_deg
        lat += cell_deg
    return cells


def make_map(df):
    m = folium.Map(location=INDIA_CENTER, zoom_start=INDIA_ZOOM, tiles="CartoDB positron")

    # Medical desert grid layer
    desert_layer = folium.FeatureGroup(name="Medical Deserts", show=True)
    for lat, lon in build_desert_grid(df):
        folium.Rectangle(
            bounds=[[lat, lon], [lat + 0.5, lon + 0.5]],
            color=None, fill=True, fill_color="#7d3c98", fill_opacity=0.35,
            tooltip="No high-trust facility in this cell",
        ).add_to(desert_layer)
    desert_layer.add_to(m)

    # Facility markers, grouped by trust tier
    valid = df.dropna(subset=["latitude", "longitude"]).copy()
    valid["trust_tier"] = valid["trust_tier"].fillna("unverified").astype(str)

    for tier, color in TIER_COLORS.items():
        layer   = folium.FeatureGroup(name=f"{tier.title()} Trust", show=(tier != "unverified"))
        cluster = MarkerCluster()
        subset  = valid[valid["trust_tier"] == tier]

        for _, row in subset.iterrows():
            popup = folium.Popup(
                folium.IFrame(build_popup(row.to_dict()), width=260, height=160),
                max_width=280,
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=5, color=color, fill=True,
                fill_color=color, fill_opacity=0.85,
                popup=popup,
                tooltip=f"{row.get('facility_name','?')} [{tier}]",
            ).add_to(cluster)

        cluster.add_to(layer)
        layer.add_to(m)

    # Density heatmap (hidden by default)
    heat_data = valid[["latitude", "longitude"]].values.tolist()
    if heat_data:
        heat_layer = folium.FeatureGroup(name="Density Heatmap", show=False)
        HeatMap(heat_data, radius=12, blur=10, min_opacity=0.3).add_to(heat_layer)
        heat_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.get_root().html.add_child(folium.Element(LEGEND_HTML))
    return m


def main():
    parser = argparse.ArgumentParser(description="Generate interactive Folium map")
    parser.parse_args()

    if not DATA_PATH.exists():
        print(f"ERROR: {DATA_PATH} not found. Run geocode.py first.")
        return

    print(f"Loading {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH, low_memory=False)

    for col in ["latitude", "longitude", "final_trust_score", "beds_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["final_trust_score"] = df["final_trust_score"].fillna(0)

    bool_cols = ["has_icu", "has_emergency_trauma", "has_oncology",
                 "has_dialysis", "has_anesthesiologist", "supports_appendectomy"]
    bool_map = {"True": True, "False": False, True: True, False: False}
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map(bool_map)

    print(f"Records: {len(df)} | Geocoded: {df['latitude'].notna().sum()}")

    m = make_map(df)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    m.save(str(OUTPUT_PATH))
    print(f"Map saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
