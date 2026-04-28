import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="CarePath AI",
    page_icon=str(ROOT / "assets" / "favicon.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Routing ────────────────────────────────────────────────────────────────
PAGES = ["home", "discover", "search", "analytics"]
LABELS = {"home": "Home", "discover": "Discover", "search": "Search", "analytics": "Analytics"}

active = st.query_params.get("page", "home")
if active not in PAGES:
    active = "home"

# ── Global styles + navbar ─────────────────────────────────────────────────
from utils.styles import inject_css
inject_css(active)

# ── Render active page ─────────────────────────────────────────────────────
from pages.home      import render as render_home
from pages.discover  import render as render_discover
from pages.search    import render as render_search
from pages.analytics import render as render_analytics

{"home": render_home, "discover": render_discover,
 "search": render_search, "analytics": render_analytics}[active]()
