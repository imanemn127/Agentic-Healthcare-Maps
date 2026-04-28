# pages/search.py
import streamlit as st

from utils.constants import EXAMPLE_QUERIES
from utils.ui import render_result_card, render_export, section


def render() -> None:
    # ── Initialise session keys needed by this page ────────────────────────
    if "search_result" not in st.session_state:
        st.session_state.search_result = None

    st.markdown(
        '<div class="search-header">'
        '<div class="search-header-title">Natural Language Facility Search</div>'
        '<div class="search-header-sub">'
        'Parses your query into structured filters — state, facility type, ownership, '
        'clinical capabilities — then ranks results by trust score.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_q, col_loc, col_btn = st.columns([4, 2, 1])
    with col_q:
        query = st.text_input(
            "query", label_visibility="collapsed",
            placeholder="e.g.  Government ICU hospital in Maharashtra with oncology",
            key="search_query",
        )
    with col_loc:
        loc_str = st.text_input(
            "location", label_visibility="collapsed",
            placeholder="lat, lon  (optional)",
            key="search_loc",
        )
    with col_btn:
        search_clicked = st.button("Search", type="primary", use_container_width=True)

    # Example query buttons
    st.markdown('<div class="example-row"><span class="example-label">Try:</span>', unsafe_allow_html=True)
    ecols = st.columns(len(EXAMPLE_QUERIES))
    for i, ex in enumerate(EXAMPLE_QUERIES):
        if ecols[i].button(ex, key=f"ex_{i}", use_container_width=True):
            query = ex
            search_clicked = True
    st.markdown('</div>', unsafe_allow_html=True)

    location = None
    if loc_str:
        try:
            parts = loc_str.split(",")
            location = (float(parts[0].strip()), float(parts[1].strip()))
        except (ValueError, IndexError):
            st.warning("Location format: `19.076, 72.877`")

    if search_clicked and query:
        with st.status("Parsing intent and filtering dataset…", expanded=False) as status:
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
                from src.query_agent import run_query
                st.session_state.search_result = run_query(query, location=location)
                status.update(label="Done", state="complete", expanded=False)
            except Exception as e:
                st.error(f"Search error: {e}")
                return

    res = st.session_state.search_result
    if not res:
        return

    st.divider()
    st.markdown(
        f'<div class="intent-box">'
        f'<div class="intent-label">Interpreted as</div>'
        f'<div class="intent-text">{res.get("intent_summary", "")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    filters  = {k: v for k, v in res.get("filters_applied", {}).items() if v}
    caps_req = [k for k, v in res.get("capabilities_required", {}).items() if v is True]
    m1.metric("Matched",         res.get("total_matched", 0))
    m2.metric("Showing",         len(res.get("results", [])))
    m3.metric("Filters applied", len(filters))
    m4.metric("Capabilities",    len(caps_req))

    results = res.get("results", [])
    if not results:
        st.markdown(
            '<div class="empty-state">'
            '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/>'
            '<path d="M21 21l-4.35-4.35"/></svg>'
            '<div class="empty-msg">No facilities match these filters.<br>'
            'Try broadening your query or removing capability requirements.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    _, c_right = st.columns([5, 1])
    show_ins = c_right.checkbox("AI insights", value=False, key="q_ins")

    section(f"Top {len(results)} Results")
    for i, r in enumerate(results, 1):
        render_result_card(r, i, show_insight=show_ins)

    render_export(results)