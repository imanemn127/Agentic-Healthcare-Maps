# utils/ui.py
import json
import os
import pandas as pd
import streamlit as st

from utils.constants import (
    CAP_META, ICO_PIN, ICO_CHECK, ICO_QUOTE,
    ICO_BUILDING, ICO_SHIELD, ICO_BED, ICO_DIST,
    GREEN, AMBER, RED, MUTED,
    DATA_PATH,
)


# ── Data loaders ───────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH, low_memory=False)
    for col in ["final_trust_score", "latitude", "longitude",
                "beds_count", "rule_score", "llm_score", "geocode_score", "row_id"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["final_trust_score"] = df["final_trust_score"].fillna(0)
    for col in ["state", "facility_type", "ownership",
                "trust_tier", "city", "district", "facility_name"]:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").astype(str).str.strip()
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def get_facility_insight(name: str, record_json: str) -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return ""
    try:
        from groq import Groq
        c = Groq(api_key=key)
        r = c.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": (
                "You are a healthcare analyst. Given this facility record, write exactly 2 sentences: "
                "(1) key strengths based on the data, (2) one concrete recommendation for a patient. "
                f"Be specific and professional. No bullet points.\n\nFacility: {record_json}"
            )}],
            temperature=0.3, max_tokens=200,
        )
        return r.choices[0].message.content or ""
    except Exception:
        return ""


@st.cache_data(ttl=1800, show_spinner=False)
def get_dataset_summary(stats_json: str) -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return ""
    try:
        from groq import Groq
        c = Groq(api_key=key)
        r = c.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": (
                "You are a public health analyst. Given aggregate stats about an Indian healthcare "
                "dataset, write exactly 3 sentences: (1) a coverage observation, (2) a data quality "
                f"concern, (3) a policy recommendation. Cite numbers. No bullets.\n\nStats: {stats_json}"
            )}],
            temperature=0.3, max_tokens=220,
        )
        return r.choices[0].message.content or ""
    except Exception:
        return ""


# ── Section divider ────────────────────────────────────────────────────────

def section(label: str) -> None:
    st.markdown(
        f'<div class="section-head">'
        f'<div class="section-head-bar"></div>'
        f'<div class="section-head-label">{label}</div>'
        f'<div class="section-head-line"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── HTML primitives ────────────────────────────────────────────────────────

def trust_tier_html(tier: str) -> str:
    cls = {"high": "tier-high", "medium": "tier-medium", "low": "tier-low"}.get(tier, "tier-unver")
    return f'<span class="trust-tier {cls}">{tier.upper()}</span>'


def trust_block(score: float, tier: str) -> str:
    tv = {"high": "tv-high", "medium": "tv-medium", "low": "tv-low"}.get(tier, "tv-unver")
    fc = {"high": "fill-high", "medium": "fill-medium", "low": "fill-low"}.get(tier, "fill-unver")
    return (
        f'<div class="trust-block">'
        f'<div class="trust-row">'
        f'<span class="trust-value {tv}">{score:.0%}</span>'
        f'{trust_tier_html(tier)}'
        f'</div>'
        f'<div class="trust-bar">'
        f'<div class="trust-fill {fc}" style="width:{score*100:.1f}%"></div>'
        f'</div></div>'
    )


def cap_chips(caps: dict) -> str:
    chips = [
        f'<span class="cap cap-yes">'
        f'<svg viewBox="0 0 24 24" style="width:9px;height:9px;stroke:currentColor;fill:none;'
        f'stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round">'
        f'<path d="{ICO_CHECK}"/></svg>{label}</span>'
        for key, label in CAP_META.items()
        if caps.get(key) is True
    ]
    return f'<div class="caps">{"".join(chips)}</div>' if chips else ""


def tag(css_class: str, icon_path: str, text: str) -> str:
    ico = (
        f'<svg viewBox="0 0 24 24" style="width:10px;height:10px;stroke:currentColor;'
        f'fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round">'
        f'<path d="{icon_path}"/></svg>'
    )
    return f'<span class="tag {css_class}">{ico}{text}</span>'


def pin_svg() -> str:
    return (
        f'<svg viewBox="0 0 24 24" style="width:12px;height:12px;stroke:currentColor;'
        f'fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round">'
        f'<path d="{ICO_PIN}"/></svg>'
    )


# ── Result card ────────────────────────────────────────────────────────────

def render_result_card(r: dict, index: int, show_insight: bool = False) -> None:
    tier  = r.get("trust_tier", "unverified")
    score = float(r.get("trust_score", 0))
    name  = r.get("facility_name", "Unknown")
    city  = r.get("city", "")
    state = r.get("state", "")
    loc   = ", ".join(x.title() for x in [city, state] if x and x.lower() != "unknown")

    tags: list[str] = []
    ftype = str(r.get("facility_type", "")).strip().title()
    if ftype and ftype.lower() not in ("unknown", "nan", ""):
        tags.append(tag("tag-type", ICO_BUILDING, ftype))
    own = str(r.get("ownership", "")).strip().title()
    if own and own.lower() not in ("unknown", "nan", ""):
        tags.append(tag("tag-own", ICO_SHIELD, own))
    dist = r.get("distance_km")
    if dist is not None:
        tags.append(tag("tag-dist", ICO_DIST, f"{dist} km"))
    beds_raw = r.get("beds_count") or r.get("beds")
    if beds_raw and str(beds_raw) not in ("nan", "None", ""):
        try:
            tags.append(tag("tag-beds", ICO_BED, f"{int(float(beds_raw))} beds"))
        except (ValueError, TypeError):
            pass

    caps_html  = cap_chips(r.get("capabilities", {}))
    trust_html = trust_block(score, tier)
    tags_html  = "".join(tags)

    ev_items = "".join(
        f'<div class="ev-item">'
        f'<svg viewBox="0 0 24 24" style="width:10px;height:10px;stroke:var(--accent-d);'
        f'fill:none;stroke-width:2;stroke-linecap:round;flex-shrink:0;margin-top:2px">'
        f'<path d="{ICO_QUOTE}"/></svg>{s}</div>'
        for s in r.get("evidence_sentences", [])[:2]
    )
    ev_block = f'<div class="evidence-list">{ev_items}</div>' if ev_items else ""

    st.markdown(
        f'<div class="card">'
        f'<div class="card-top">'
        f'<div class="card-rank">#{index}</div>'
        f'<div class="card-main">'
        f'<div class="card-name">{name}</div>'
        f'<div class="card-location">{pin_svg()}{loc}</div>'
        f'<div class="tags">{tags_html}</div>'
        f'</div></div>'
        f'{trust_html}{caps_html}{ev_block}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if show_insight:
        r_json = json.dumps(
            {k: v for k, v in r.items() if k != "evidence_sentences" and v is not None},
            default=str,
        )
        with st.spinner("Generating insight…"):
            insight = get_facility_insight(name, r_json)
        if insight:
            st.markdown(
                f'<div class="insight-block">'
                f'<div class="insight-label">AI Insight</div>'
                f'<div class="insight-text">{insight}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Export row ─────────────────────────────────────────────────────────────

def render_export(results: list) -> None:
    if not results:
        return
    c1, c2, _ = st.columns([1, 1, 2])
    json_bytes = json.dumps(results, indent=2, ensure_ascii=False).encode()
    c1.download_button(
        "Export JSON", data=json_bytes,
        file_name="carepath_results.json", mime="application/json",
        use_container_width=True,
    )
    flat = []
    for r in results:
        row = {k: v for k, v in r.items() if k not in ("capabilities", "evidence_sentences")}
        row.update(r.get("capabilities", {}))
        row["evidence"] = " | ".join(r.get("evidence_sentences", []))
        flat.append(row)
    csv_bytes = pd.DataFrame(flat).to_csv(index=False).encode()
    c2.download_button(
        "Export CSV", data=csv_bytes,
        file_name="carepath_results.csv", mime="text/csv",
        use_container_width=True,
    )


# ── Compare table ──────────────────────────────────────────────────────────

def render_compare_table(da: dict, db: dict) -> None:
    name_a  = da.get("facility_name", "Facility A")
    name_b  = db.get("facility_name", "Facility B")
    score_a = float(da.get("final_trust_score", da.get("trust_score", 0)))
    score_b = float(db.get("final_trust_score", db.get("trust_score", 0)))

    def yesno(d: dict, key: str) -> str:
        v = d.get(key)
        if v is True:  return "Yes"
        if v is False: return "No"
        return "—"

    rows = [
        ("Location",    f"{da.get('city','')}, {da.get('state','')}",
                        f"{db.get('city','')}, {db.get('state','')}"),
        ("Type",        str(da.get("facility_type","—")).title(),
                        str(db.get("facility_type","—")).title()),
        ("Ownership",   str(da.get("ownership","—")).title(),
                        str(db.get("ownership","—")).title()),
        ("Beds",        str(da.get("beds_count","—")),
                        str(db.get("beds_count","—"))),
        ("Trust Score", f"{score_a:.0%}", f"{score_b:.0%}"),
        ("Trust Tier",  str(da.get("trust_tier","—")),
                        str(db.get("trust_tier","—"))),
        ("ICU",         yesno(da,"has_icu"),         yesno(db,"has_icu")),
        ("Emergency",   yesno(da,"has_emergency_trauma"),
                        yesno(db,"has_emergency_trauma")),
        ("Oncology",    yesno(da,"has_oncology"),     yesno(db,"has_oncology")),
        ("Dialysis",    yesno(da,"has_dialysis"),     yesno(db,"has_dialysis")),
        ("Surgery",     yesno(da,"supports_appendectomy"),
                        yesno(db,"supports_appendectomy")),
    ]

    trs = ""
    for label, va, vb in rows:
        ca = cb = ""
        if label == "Trust Score":
            ca = "cmp-winner" if score_a > score_b else ""
            cb = "cmp-winner" if score_b > score_a else ""
        trs += f"<tr><td>{label}</td><td class='{ca}'>{va}</td><td class='{cb}'>{vb}</td></tr>"

    st.markdown(
        f'<table class="cmp-table"><thead><tr>'
        f'<th>Attribute</th><th>{name_a}</th><th>{name_b}</th>'
        f'</tr></thead><tbody>{trs}</tbody></table>',
        unsafe_allow_html=True,
    )