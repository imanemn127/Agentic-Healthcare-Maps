# pages/home.py
import streamlit as st
from utils.constants import (
    _ICO_DB, _ICO_BRAIN, _ICO_MAP2, _ICO_SHIELD2, ICO_PIN,
    PRIMARY, PRIMARY_L, PRIMARY_D, ACCENT_D, ACCENT_L,
)


def _svg(path_d: str, style: str = "") -> str:
    return (
        f'<svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;'
        f'fill:none;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round;{style}">'
        f'<path d="{path_d}"/></svg>'
    )


def _chip(label: str) -> str:
    return f'<span class="step-tag">{label}</span>'


def _feature_chip(label: str, value: str, icon_path: str) -> str:
    return (
        f'<div class="feature-chip">'
        f'<svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:var(--accent-d);'
        f'fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round">'
        f'<path d="{icon_path}"/></svg>'
        f'<span class="fc-label">{label}</span>'
        f'<span class="fc-val">{value}</span>'
        f'</div>'
    )


def render() -> None:
    n_fac, n_states, n_geo, n_high = 10_000, 28, 9_847, 3_214

    st.markdown(
        f'<div class="pipeline-section">'
        f'<div class="pipeline-eyebrow">Indian Healthcare Intelligence Platform</div>'
        f'<div class="pipeline-title">From raw records to<br><em>trusted recommendations</em></div>'
        f'<div class="pipeline-subtitle">'
        f'A multi-layer agentic pipeline that ingests 10,000+ facility records, '
        f'scores data reliability with LLM reasoning, geocodes every location, '
        f'and surfaces the right care through natural-language search.'
        f'</div>'

        f'<div class="pipeline-flow">'

        f'<div class="pipeline-step">'
        f'<div class="step-layer">Layer 1 · Ingest</div>'
        f'<div class="step-icon icon-ingest">{_svg(_ICO_DB)}</div>'
        f'<div class="step-name">Ingest &amp; Extract</div>'
        f'<div class="step-desc">'
        f'Raw XLSX facility records batch-processed by an LLM that normalises names, '
        f'parses messy bed counts, and infers clinical capabilities from free-text.'
        f'</div>'
        f'<div class="step-tags">{_chip("Gemini 2.0 Flash")}{_chip("Groq Llama 3.3")}'
        f'{_chip("10,000 records")}{_chip("Batch extraction")}</div>'
        f'</div>'

        f'<div class="pipeline-step">'
        f'<div class="step-layer">Layer 2 · Reason</div>'
        f'<div class="step-icon icon-reason">{_svg(_ICO_BRAIN)}</div>'
        f'<div class="step-name">Trust Scoring</div>'
        f'<div class="step-desc">'
        f'Each record receives a trust score combining rule-based sanity checks '
        f'with LLM consistency validation and accreditation signals.'
        f'</div>'
        f'<div class="step-tags">{_chip("Rule engine")}{_chip("LLM audit")}'
        f'{_chip("NABH / ISO / NABL")}{_chip("0.0 – 1.0 score")}</div>'
        f'</div>'

        f'<div class="pipeline-step">'
        f'<div class="step-layer">Layer 3 · Surface</div>'
        f'<div class="step-icon icon-surface">{_svg(_ICO_MAP2)}</div>'
        f'<div class="step-name">Geocode &amp; Search</div>'
        f'<div class="step-desc">'
        f'Facilities geocoded with progressive fallback, then exposed through an '
        f'NL query agent that parses intent and ranks by trust + distance.'
        f'</div>'
        f'<div class="step-tags">{_chip("Nominatim")}{_chip("Folium map")}'
        f'{_chip("NL intent parsing")}{_chip("Distance ranking")}</div>'
        f'</div>'

        f'</div>'  # .pipeline-flow

        f'<div class="feature-row">'
        f'{_feature_chip(f"{n_fac:,} Facilities", "indexed", _ICO_DB)}'
        f'{_feature_chip(f"{n_states} States", "covered", _ICO_MAP2)}'
        f'{_feature_chip(f"{n_geo:,} Records", "geocoded", ICO_PIN)}'
        f'{_feature_chip(f"{n_high:,} Records", "high trust", _ICO_SHIELD2)}'
        f'{_feature_chip("LLM-powered", "search", _ICO_BRAIN)}'
        f'</div>'

        # ── How the agent works — framed card with blue number cubes ─────
        f'<div class="hiw-card">'
        f'<div class="hiw-header">'
        f'<div class="hiw-header-dot"></div>'
        f'<div class="hiw-title">How The Agent Works</div>'
        f'</div>'
        f'<div class="hiw-steps">'

        f'<div class="hiw-step">'
        f'<div class="hiw-num">01</div>'
        f'<div class="hiw-step-body">'
        f'<div class="hiw-step-title">Parse Intent</div>'
        f'<div class="hiw-step-text">Your natural language query is decomposed into '
        f'structured filters — state, facility type, ownership, and clinical capabilities.</div>'
        f'</div></div>'

        f'<div class="hiw-connector"></div>'

        f'<div class="hiw-step">'
        f'<div class="hiw-num">02</div>'
        f'<div class="hiw-step-body">'
        f'<div class="hiw-step-title">Search &amp; Score</div>'
        f'<div class="hiw-step-text">10,000+ verified facilities are filtered and ranked '
        f'by trust score, accreditation signals, and geospatial distance.</div>'
        f'</div></div>'

        f'<div class="hiw-connector"></div>'

        f'<div class="hiw-step">'
        f'<div class="hiw-num">03</div>'
        f'<div class="hiw-step-body">'
        f'<div class="hiw-step-title">Return Results</div>'
        f'<div class="hiw-step-text">Transparent, auditable results are returned with '
        f'evidence snippets, trust breakdowns, and AI-generated insights.</div>'
        f'</div></div>'

        f'</div>'  # .hiw-steps
        f'</div>'  # .hiw-card

        f'</div>',  # .pipeline-section
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-footer">'
        '<span class="footer-brand">CarePath AI</span> — 5th Hack Nation Hackathon<br>'
        'Pipeline: Gemini 2.0 Flash · Groq Llama 3.3 · Folium · Altair · Streamlit'
        '</div>',
        unsafe_allow_html=True,
    )
