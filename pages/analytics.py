# pages/analytics.py
import json
import os
import pandas as pd
import streamlit as st
import altair as alt

from utils.constants import (
    CAP_META, GREEN, AMBER, RED, MUTED,
    PRIMARY, PRIMARY_L, ACCENT_D,
    L_SURFACE, L_BORDER, L_TEXT, L_TEXT2, L_TEXT3,
)
from utils.ui import load_data, get_dataset_summary, section

TRUST_COLORS = {"high": GREEN, "medium": AMBER, "low": RED, "unverified": MUTED}


def _theme() -> dict:
    return {
        "view":   {"stroke": None, "fill": "transparent"},
        "axis":   {
            "labelFont": "Sora", "titleFont": "Sora",
            "labelColor": L_TEXT3, "titleColor": L_TEXT3,
            "gridColor": L_BORDER, "domainColor": L_BORDER,
            "tickColor":  L_BORDER, "labelFontSize": 11, "titleFontSize": 11,
        },
        "title":  {"font": "Sora", "color": L_TEXT, "fontSize": 13,
                   "fontWeight": 600, "anchor": "start"},
        "legend": {"labelFont": "Sora", "titleFont": "Sora",
                   "labelColor": L_TEXT2, "titleColor": L_TEXT3,
                   "labelFontSize": 11, "orient": "bottom"},
        "background": "transparent",
        "padding": {"top": 12, "right": 8, "bottom": 8, "left": 8},
    }


def chart_top_states(df: pd.DataFrame) -> alt.Chart:
    data = (
        df.groupby("state").size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(15)
    )
    data["state"] = data["state"].str.title()
    return (
        alt.Chart(data, title="Top 15 States by Facility Count")
        .mark_bar(color=PRIMARY, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("state:N", sort="-y", axis=alt.Axis(labelAngle=-35, title=None)),
            y=alt.Y("count:Q", axis=alt.Axis(title="Facilities")),
            tooltip=[alt.Tooltip("state:N", title="State"),
                     alt.Tooltip("count:Q", title="Count")],
        )
        .properties(height=280)
        .configure(**_theme())
    )


def chart_trust_tier(df: pd.DataFrame) -> alt.Chart:
    data = (
        df["trust_tier"].value_counts()
        .reset_index()
        .rename(columns={"trust_tier": "tier", "count": "n"})
    )
    color_map = alt.Scale(
        domain=list(TRUST_COLORS.keys()),
        range=list(TRUST_COLORS.values()),
    )
    return (
        alt.Chart(data, title="Trust Tier Distribution")
        .mark_arc(innerRadius=55, outerRadius=100)
        .encode(
            theta=alt.Theta("n:Q"),
            color=alt.Color("tier:N", scale=color_map, legend=alt.Legend(title="Tier")),
            tooltip=[alt.Tooltip("tier:N", title="Tier"),
                     alt.Tooltip("n:Q", title="Count")],
        )
        .properties(height=260)
        .configure(**_theme())
    )


def chart_facility_types(df: pd.DataFrame) -> alt.Chart:
    data = (
        df["facility_type"].str.title().value_counts()
        .reset_index()
        .rename(columns={"facility_type": "type", "count": "n"})
        .head(10)
    )
    return (
        alt.Chart(data, title="Top 10 Facility Types")
        .mark_bar(color=ACCENT_D, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("n:Q", axis=alt.Axis(title="Count")),
            y=alt.Y("type:N", sort="-x", axis=alt.Axis(title=None)),
            tooltip=[alt.Tooltip("type:N", title="Type"),
                     alt.Tooltip("n:Q", title="Count")],
        )
        .properties(height=280)
        .configure(**_theme())
    )


def chart_trust_histogram(df: pd.DataFrame) -> alt.Chart:
    data = df[["final_trust_score"]].dropna()
    return (
        alt.Chart(data, title="Trust Score Distribution")
        .mark_bar(color=PRIMARY_L, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("final_trust_score:Q", bin=alt.Bin(maxbins=25),
                    axis=alt.Axis(title="Trust Score", format=".0%")),
            y=alt.Y("count():Q", axis=alt.Axis(title="Facilities")),
            tooltip=[alt.Tooltip("final_trust_score:Q", title="Score", format=".0%"),
                     alt.Tooltip("count():Q", title="Count")],
        )
        .properties(height=260)
        .configure(**_theme())
    )


def chart_ownership(df: pd.DataFrame) -> alt.Chart:
    data = (
        df["ownership"].str.title().value_counts()
        .reset_index()
        .rename(columns={"ownership": "owner", "count": "n"})
        .head(8)
    )
    colors = [PRIMARY, PRIMARY_L, ACCENT_D, "#7C3AED", "#059669",
              AMBER, RED, MUTED]
    color_scale = alt.Scale(range=colors)
    return (
        alt.Chart(data, title="Ownership Breakdown")
        .mark_arc(innerRadius=50, outerRadius=95)
        .encode(
            theta=alt.Theta("n:Q"),
            color=alt.Color("owner:N", scale=color_scale,
                            legend=alt.Legend(title="Ownership")),
            tooltip=[alt.Tooltip("owner:N", title="Ownership"),
                     alt.Tooltip("n:Q", title="Count")],
        )
        .properties(height=260)
        .configure(**_theme())
    )


def chart_capability_heatmap(df: pd.DataFrame) -> alt.Chart:
    existing = [c for c in CAP_META if c in df.columns]
    rows = []
    for state in df["state"].str.title().value_counts().head(12).index:
        sub = df[df["state"].str.title() == state]
        for col in existing:
            pct = (sub[col] == True).mean() * 100
            rows.append({"State": state, "Capability": CAP_META[col], "Coverage %": round(pct, 1)})
    data = pd.DataFrame(rows)
    return (
        alt.Chart(data, title="Capability Coverage by State (Top 12)")
        .mark_rect()
        .encode(
            x=alt.X("Capability:N", axis=alt.Axis(labelAngle=-30, title=None)),
            y=alt.Y("State:N", axis=alt.Axis(title=None)),
            color=alt.Color("Coverage %:Q",
                            scale=alt.Scale(scheme="blues", domain=[0, 100]),
                            legend=alt.Legend(title="Coverage %")),
            tooltip=[alt.Tooltip("State:N"), alt.Tooltip("Capability:N"),
                     alt.Tooltip("Coverage %:Q", format=".1f")],
        )
        .properties(height=340)
        .configure(**_theme())
    )


def render() -> None:
    df = load_data()
    if df.empty:
        st.warning("No data available. Run the pipeline first.")
        return

    section("Filters")
    fc1, fc2, fc3, fc4 = st.columns(4)
    sel_state = fc1.selectbox("State",      ["All"] + sorted(df["state"].str.title().unique()), key="an_s")
    sel_type  = fc2.selectbox("Type",       ["All"] + sorted(df["facility_type"].str.title().unique()), key="an_t")
    sel_tier  = fc3.selectbox("Trust tier", ["All", "high", "medium", "low", "unverified"], key="an_tr")
    min_trust = fc4.slider("Min trust score", 0.0, 1.0, 0.0, 0.05, key="an_min")

    fdf = df.copy()
    if sel_state != "All": fdf = fdf[fdf["state"].str.title() == sel_state]
    if sel_type  != "All": fdf = fdf[fdf["facility_type"].str.title() == sel_type]
    if sel_tier  != "All": fdf = fdf[fdf["trust_tier"] == sel_tier]
    if min_trust  > 0:     fdf = fdf[fdf["final_trust_score"] >= min_trust]

    section("Overview")
    k1, k2, k3, k4, k5 = st.columns(5)
    avg_b = fdf["beds_count"].mean()
    k1.metric("Facilities",  f"{len(fdf):,}")
    k2.metric("States",      fdf["state"].nunique())
    k3.metric("Geocoded",    f"{int(fdf['latitude'].notna().sum()):,}")
    k4.metric("High Trust",  f"{int((fdf['trust_tier'] == 'high').sum()):,}")
    k5.metric("Avg Beds",    f"{avg_b:.0f}" if not pd.isna(avg_b) else "—")

    section("AI Dataset Analysis")
    stats = {
        "total":          len(fdf),
        "states":         fdf["state"].nunique(),
        "high_trust_pct": round((fdf["trust_tier"] == "high").mean() * 100, 1),
        "geocoded_pct":   round(fdf["latitude"].notna().mean() * 100, 1),
        "avg_beds":       round(avg_b, 0) if not pd.isna(avg_b) else None,
        "types":          fdf["facility_type"].value_counts().head(5).to_dict(),
        "top_states":     fdf["state"].value_counts().head(5).to_dict(),
    }
    with st.spinner("Generating analysis…"):
        summary = get_dataset_summary(json.dumps(stats, default=str))
    if summary:
        st.markdown(
            f'<div class="insight-block">'
            f'<div class="insight-label">AI Analysis</div>'
            f'<div class="insight-text">{summary}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    elif not os.getenv("GROQ_API_KEY"):
        st.caption("Set GROQ_API_KEY in .env to enable AI dataset analysis.")

    section("Visualisations")

    # Row 1 — top states bar + trust tier donut
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        try:
            st.altair_chart(chart_top_states(fdf), use_container_width=True)
        except Exception as e:
            st.warning(f"Top states chart error: {e}")
    with c2:
        try:
            st.altair_chart(chart_trust_tier(fdf), use_container_width=True)
        except Exception as e:
            st.warning(f"Trust tier chart error: {e}")

    # Row 2 — facility types bar + trust histogram
    c3, c4 = st.columns(2, gap="large")
    with c3:
        try:
            st.altair_chart(chart_facility_types(fdf), use_container_width=True)
        except Exception as e:
            st.warning(f"Facility types chart error: {e}")
    with c4:
        try:
            st.altair_chart(chart_trust_histogram(fdf), use_container_width=True)
        except Exception as e:
            st.warning(f"Trust histogram error: {e}")

    # Row 3 — ownership donut + capability heatmap
    c5, c6 = st.columns([1, 2], gap="large")
    with c5:
        try:
            st.altair_chart(chart_ownership(fdf), use_container_width=True)
        except Exception as e:
            st.warning(f"Ownership chart error: {e}")
    with c6:
        existing_caps = [c for c in CAP_META if c in fdf.columns]
        if existing_caps:
            try:
                st.altair_chart(chart_capability_heatmap(fdf), use_container_width=True)
            except Exception as e:
                st.warning(f"Heatmap error: {e}")

    section("Capability Coverage")
    existing = [c for c in CAP_META if c in fdf.columns]
    if existing:
        total = len(fdf)
        rows  = []
        for col in existing:
            yes_cnt = int((fdf[col] == True).sum())
            no_cnt  = int((fdf[col] == False).sum())
            unk_cnt = total - yes_cnt - no_cnt
            rows.append({
                "Capability": CAP_META[col],
                "Yes":        yes_cnt,
                "No":         no_cnt,
                "Unknown":    unk_cnt,
                "Coverage":   f"{yes_cnt/total:.0%}" if total else "—",
            })
        st.dataframe(pd.DataFrame(rows).set_index("Capability"), use_container_width=True)

    section("Dataset Table (top 500)")
    show_cols = [c for c in [
        "facility_name", "facility_type", "city", "state",
        "final_trust_score", "trust_tier", "has_icu", "has_emergency_trauma",
        "beds_count", "ownership", "latitude", "longitude",
    ] if c in fdf.columns]
    st.dataframe(
        fdf[show_cols].sort_values("final_trust_score", ascending=False).head(500),
        use_container_width=True,
    )
