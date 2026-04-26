"""
Streamlit dashboard: Map | Query | Data Explorer
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `from src.X import Y` always works
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

DATA_PATH = _ROOT / "data" / "geocoded_facilities.csv"
MAP_PATH  = _ROOT / "maps" / "healthcare_map.html"

st.set_page_config(
    page_title="Agentic Healthcare Maps",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(ttl=600)
def load_data():
    if not DATA_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH, low_memory=False)

    for col in ["final_trust_score", "latitude", "longitude", "beds_count",
                "rule_score", "llm_score", "geocode_score", "row_id"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["final_trust_score"] = df["final_trust_score"].fillna(0)

    for col in ["state", "facility_type", "ownership", "trust_tier",
                "city", "district", "facility_name"]:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").astype(str).str.strip()

    return df


# ── Tab: Map ─────────────────────────────────────────────────────────────────

def render_map():
    st.subheader("Interactive Map of Indian Healthcare Facilities")
    st.caption("Colour-coded by trust tier · Purple grid = medical deserts · Toggle layers with the control (top-right)")

    if not MAP_PATH.exists():
        st.warning(
            f"`{MAP_PATH}` not found. Generate it with:\n"
            "```\npython src/map_generator.py\n```"
        )
        return

    html = MAP_PATH.read_text(encoding="utf-8")
    components.html(html, height=640, scrolling=False)


# ── Tab: Query ────────────────────────────────────────────────────────────────

def render_query():
    st.subheader("Natural Language Query")
    st.caption("Describe what you need — the agent will parse capabilities, filter the dataset, and rank results.")

    if "qresult" not in st.session_state:
        st.session_state.qresult = None

    col_q, col_loc, col_btn = st.columns([4, 2, 1])
    with col_q:
        query = st.text_input("Your query", placeholder="Hospital with ICU and emergency in Maharashtra")
    with col_loc:
        loc_str = st.text_input("Your location (lat,lon)", placeholder="19.076, 72.877", help="Optional – used to rank by distance")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        search = st.button("Search", type="primary", use_container_width=True)

    examples = [
        "ICU hospital in Karnataka",
        "Dialysis center near Delhi",
        "Government hospital with oncology in Bihar",
        "Emergency trauma center Rajasthan",
    ]
    st.markdown("**Examples:**")
    ecols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if ecols[i].button(ex, key=f"ex_{i}"):
            query = ex
            search = True

    location = None
    if loc_str:
        try:
            parts = loc_str.split(",")
            location = (float(parts[0].strip()), float(parts[1].strip()))
        except (ValueError, IndexError):
            st.warning("Invalid location format – expected `lat, lon` (e.g. 19.076, 72.877)")

    if search and query:
        with st.spinner("Querying…"):
            try:
                from src.query_agent import run_query
                st.session_state.qresult = run_query(query, location=location)
            except Exception as e:
                st.error(f"Query failed: {e}")
                return

    res = st.session_state.qresult
    if not res:
        return

    st.markdown("---")
    st.info(f"**Intent:** {res.get('intent_summary', '')}")
    st.caption(
        f"Filters: `{res.get('filters_applied', {})}` · "
        f"Capabilities required: `{res.get('capabilities_required', {})}` · "
        f"Matched: **{res.get('total_matched', 0)}** records"
    )

    results = res.get("results", [])
    if not results:
        st.warning("No facilities match the query.")
        return

    tier_color = {"high": "green", "medium": "orange", "low": "red", "unverified": "grey"}

    for i, r in enumerate(results):
        tier  = r.get("trust_tier", "unverified")
        color = tier_color.get(tier, "grey")
        dist  = f" · {r['distance_km']} km away" if r.get("distance_km") is not None else ""
        label = (
            f"{i+1}. **{r.get('facility_name','Unknown')}** — "
            f"{r.get('city','')}, {r.get('state','').title()} "
            f"[:{color}[{tier.upper()}] {r.get('trust_score',0):.2f}]{dist}"
        )
        with st.expander(label, expanded=(i == 0)):
            ca, cb = st.columns(2)
            with ca:
                st.markdown(f"**Type:** {str(r.get('facility_type','')).title()}")
                st.markdown(f"**Trust score:** {r.get('trust_score',0):.3f}")
                if r.get("distance_km") is not None:
                    st.markdown(f"**Distance:** {r['distance_km']} km")
            with cb:
                caps = r.get("capabilities", {})
                for cap, val in caps.items():
                    icon = "Yes" if val else ("No" if val is False else "—")
                    st.markdown(f"{icon} `{cap}`")

            ev = r.get("evidence_sentences", [])
            if ev:
                st.markdown("**Evidence:**")
                for sentence in ev:
                    st.info(f'"{sentence}"')


# ── Tab: Data Explorer ────────────────────────────────────────────────────────

def render_explorer(df):
    st.subheader("Data Explorer")

    if df.empty:
        st.warning("No data loaded.")
        return

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        states = ["All"] + sorted(df["state"].unique().tolist())
        sel_state = st.selectbox("State", states)
    with col_f2:
        types_ = ["All"] + sorted(df["facility_type"].unique().tolist())
        sel_type = st.selectbox("Type", types_)
    with col_f3:
        tiers = ["All"] + sorted(df["trust_tier"].unique().tolist())
        sel_tier = st.selectbox("Trust Tier", tiers)
    with col_f4:
        min_trust = st.slider("Min Trust Score", 0.0, 1.0, 0.0, 0.05)

    filtered = df.copy()
    if sel_state != "All":
        filtered = filtered[filtered["state"] == sel_state]
    if sel_type != "All":
        filtered = filtered[filtered["facility_type"] == sel_type]
    if sel_tier != "All":
        filtered = filtered[filtered["trust_tier"] == sel_tier]
    if min_trust > 0:
        filtered = filtered[filtered["final_trust_score"] >= min_trust]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Facilities", f"{len(filtered):,}")
    m2.metric("States", filtered["state"].nunique())
    m3.metric("Geocoded", f"{filtered['latitude'].notna().sum():,}")
    m4.metric("High Trust", f"{(filtered['trust_tier'] == 'high').sum():,}")

    st.markdown("---")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("**Facilities by State (top 15)**")
        st.bar_chart(filtered["state"].value_counts().head(15))
    with col_c2:
        st.markdown("**Trust Tier Distribution**")
        st.bar_chart(filtered["trust_tier"].value_counts())

    st.markdown("---")
    display_cols = [
        "facility_name", "facility_type", "city", "state",
        "final_trust_score", "trust_tier", "has_icu", "has_emergency_trauma",
        "beds_count", "latitude", "longitude",
    ]
    show_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[show_cols].sort_values("final_trust_score", ascending=False).head(500),
        use_container_width=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.title("Agentic Healthcare Maps")
    st.caption(
        "73 Indian healthcare facilities · AI-extracted · Trust-scored · "
        "Geocoded · Queryable in natural language"
    )

    df = load_data()
    if df.empty:
        st.error(
            "Dataset not found. Run the pipeline:\n"
            "```\npython run_all.py\n```"
        )
        return

    tab_map, tab_query, tab_explorer = st.tabs(["Map", "Query", "Data Explorer"])
    with tab_map:
        render_map()
    with tab_query:
        render_query()
    with tab_explorer:
        render_explorer(df)


if __name__ == "__main__":
    main()
