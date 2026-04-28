# pages/discover.py
import streamlit as st
import streamlit.components.v1 as components

from utils.constants import GREEN, AMBER, RED, MUTED, MAP_PATH
from utils.ui import load_data, section


def render() -> None:
    df = load_data()
    if df.empty:
        st.error("Dataset not found. Run: `python run_all.py`")
        return

    left, right = st.columns([2, 1], gap="large")

    with left:
        section("Interactive Map")
        st.caption("Facilities colour-coded by trust tier. Toggle layers using the map controls.")
        if not MAP_PATH.exists():
            st.warning("Map file not found. Run: `python src/map_generator.py`")
        else:
            try:
                components.html(MAP_PATH.read_text(encoding="utf-8"), height=560, scrolling=False)
            except Exception as e:
                st.error(f"Map render error: {e}")

    with right:
        section("State Coverage — Top 10")
        top_states = df.groupby("state").size().sort_values(ascending=False).head(10)
        max_cnt = int(top_states.max()) or 1
        cov_html = "".join(
            f'<div class="cov-item">'
            f'<div class="cov-row">'
            f'<span class="cov-name">{s.title()}</span>'
            f'<span class="cov-count">{c}</span>'
            f'</div>'
            f'<div class="cov-track">'
            f'<div class="cov-fill" style="width:{c/max_cnt*100:.1f}%"></div>'
            f'</div></div>'
            for s, c in top_states.items()
        )
        st.markdown(cov_html, unsafe_allow_html=True)

        section("Data Quality")
        total = len(df)
        geo   = int(df["latitude"].notna().sum())
        tier_counts = df["trust_tier"].value_counts()
        for tier, color, label in [
            ("high",       GREEN, f"{tier_counts.get('high', 0)} high-confidence"),
            ("medium",     AMBER, f"{tier_counts.get('medium', 0)} medium-confidence"),
            ("low",        RED,   f"{tier_counts.get('low', 0)} low-confidence"),
            ("unverified", MUTED, f"{tier_counts.get('unverified', 0)} unverified"),
        ]:
            cnt = tier_counts.get(tier, 0)
            pct = cnt / total if total else 0
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;margin-bottom:0.2rem;font-size:0.77rem">'
                f'<span style="font-weight:600;color:var(--text2)">{label}</span>'
                f'<span style="color:{color};font-weight:700">{pct:.0%}</span></div>'
                f'<div style="background:var(--surface2);border-radius:4px;height:4px;'
                f'margin-bottom:0.55rem">'
                f'<div style="width:{pct*100:.1f}%;height:100%;background:{color};'
                f'border-radius:4px"></div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="insight-block" style="margin-top:0.8rem">'
            f'<div class="insight-label">Geocoding Coverage</div>'
            f'<div class="insight-text">'
            f'<strong>{geo:,}</strong> of <strong>{total:,}</strong> facilities have GPS coordinates '
            f'({geo/total:.0%}). The remaining {total-geo:,} appear as data gaps on the map.'
            f'</div></div>',
            unsafe_allow_html=True,
        )