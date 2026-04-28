import streamlit as st
from utils.constants import (
    FONT_URL,
    PRIMARY, PRIMARY_L, PRIMARY_D,
    ACCENT, ACCENT_L, ACCENT_D,
    GREEN, GREEN_L, AMBER, AMBER_L, RED, RED_L, MUTED,
    L_BG, L_SURFACE, L_SURFACE2, L_BORDER,
    L_TEXT, L_TEXT2, L_TEXT3, L_TEXT4,
    D_BG, D_SURFACE, D_SURFACE2, D_BORDER,
    D_TEXT, D_TEXT2, D_TEXT3, D_TEXT4,
)

PAGES  = ["home", "discover", "search", "analytics"]
LABELS = {"home": "Home", "discover": "Discover", "search": "Search", "analytics": "Analytics"}

NAV_BG   = "#0b1e3a"
NAV_MID  = "#1a3355"


def inject_css(active_page: str = "home") -> None:
    # Build nav tab HTML
    tabs_html = ""
    for page in PAGES:
        label     = LABELS[page]
        is_active = page == active_page
        cls       = "nav-tab nav-tab--active" if is_active else "nav-tab"
        tabs_html += f'<a href="?page={page}" target="_self" class="{cls}">{label}</a>'

    st.markdown(f"""
<style>
@import url('{FONT_URL}');

/* ── Reset & base ─────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body, [class*="css"], .stApp {{
  font-family: 'Sora', system-ui, sans-serif !important;
  background: {L_BG} !important;
  color: {L_TEXT2} !important;
  -webkit-font-smoothing: antialiased;
}}
#MainMenu, footer, header, .stDeployButton {{ display: none !important; }}
[data-testid="stHeader"] {{ display: none !important; }}
.block-container {{
  padding: 1.5rem 2rem 5rem !important;
  max-width: 1440px !important;
}}

/* ── Navbar ───────────────────────────────────────────────────────────── */
.cp-nav {{
  position: sticky;
  top: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0;
  height: 58px;
  padding: 0 2.5rem;
  background: linear-gradient(90deg, {NAV_BG} 0%, {NAV_MID} 100%);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  box-shadow: 0 2px 24px rgba(0,0,0,0.35);
  margin-bottom: 0;
}}

/* Logo */
.nav-logo {{
  display: flex;
  align-items: center;
  gap: 0.6rem;
  text-decoration: none;
  margin-right: 2.5rem;
  flex-shrink: 0;
}}
.nav-logo-icon {{
  width: 32px;
  height: 32px;
  background: {ACCENT_L};
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}}
.nav-logo-name {{
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.3px;
  white-space: nowrap;
}}
.nav-logo-sub {{
  font-size: 0.62rem;
  font-weight: 400;
  color: rgba(255,255,255,0.45);
  letter-spacing: 0.5px;
  display: block;
  line-height: 1;
  margin-top: 1px;
}}

/* Tabs */
.nav-tabs {{
  display: flex;
  align-items: center;
  height: 100%;
  gap: 2px;
}}
.nav-tab {{
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 1.1rem;
  color: rgba(255,255,255,0.65);
  font-size: 0.82rem;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  border-bottom: 3px solid transparent;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
  border-radius: 0;
}}
.nav-tab:hover {{
  color: #fff;
  background: rgba(255,255,255,0.06);
}}
.nav-tab--active {{
  color: #fff !important;
  font-weight: 600;
  border-bottom-color: {ACCENT_L} !important;
  background: rgba(255,255,255,0.08);
}}

/* ── Design tokens — light mode (default) ─────────────────────────────── */
:root {{
  --bg:        {L_BG};
  --surface:   {L_SURFACE};
  --surface2:  {L_SURFACE2};
  --border:    {L_BORDER};
  --text:      {L_TEXT};
  --text2:     {L_TEXT2};
  --text3:     {L_TEXT3};
  --text4:     {L_TEXT4};
  --primary:   {PRIMARY};
  --primary-l: {PRIMARY_L};
  --primary-d: {PRIMARY_D};
  --accent:    {ACCENT};
  --accent-l:  {ACCENT_L};
  --accent-d:  {ACCENT_D};
  --green:     {GREEN};
  --green-l:   {GREEN_L};
  --amber:     {AMBER};
  --amber-l:   {AMBER_L};
  --red:       {RED};
  --red-l:     {RED_L};
  --muted:     {MUTED};
  --shadow:    0 1px 4px rgba(30,77,123,0.08), 0 4px 16px rgba(30,77,123,0.06);
  --shadow-lg: 0 4px 20px rgba(30,77,123,0.14), 0 12px 40px rgba(30,77,123,0.10);
  --r:         12px;
  --r-sm:      8px;
  --r-xs:      5px;
  --hiw-bg:         {L_SURFACE};
  --hiw-border:     {L_BORDER};
  --hiw-header-bg:  #EFF6FF;
  --hiw-header-border: #BFDBFE;
  --insight-bg:     linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
  --insight-border: #BFDBFE;
  --icon-ingest-bg: #EFF6FF;
  --icon-reason-bg: #F5F3FF;
  --icon-surface-bg:#ECFDF5;
}}

/* ── Dark mode token overrides ────────────────────────────────────────── */
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:        {D_BG};
    --surface:   {D_SURFACE};
    --surface2:  {D_SURFACE2};
    --border:    {D_BORDER};
    --text:      {D_TEXT};
    --text2:     {D_TEXT2};
    --text3:     {D_TEXT3};
    --text4:     {D_TEXT4};
    --shadow:    0 1px 4px rgba(0,0,0,0.3), 0 4px 16px rgba(0,0,0,0.2);
    --shadow-lg: 0 4px 20px rgba(0,0,0,0.4), 0 12px 40px rgba(0,0,0,0.3);
    --hiw-bg:          {D_SURFACE};
    --hiw-border:      {D_BORDER};
    --hiw-header-bg:   rgba(30,77,123,0.25);
    --hiw-header-border: rgba(56,189,248,0.2);
    --insight-bg:      linear-gradient(135deg, rgba(30,77,123,0.18) 0%, rgba(5,150,105,0.12) 100%);
    --insight-border:  rgba(56,189,248,0.2);
    --icon-ingest-bg:  rgba(30,77,123,0.25);
    --icon-reason-bg:  rgba(109,40,217,0.2);
    --icon-surface-bg: rgba(5,150,105,0.18);
  }}
}}

/* Streamlit dark theme class override (Streamlit sets this on <html>) */
[data-theme="dark"] {{
  --bg:        {D_BG};
  --surface:   {D_SURFACE};
  --surface2:  {D_SURFACE2};
  --border:    {D_BORDER};
  --text:      {D_TEXT};
  --text2:     {D_TEXT2};
  --text3:     {D_TEXT3};
  --text4:     {D_TEXT4};
  --shadow:    0 1px 4px rgba(0,0,0,0.3), 0 4px 16px rgba(0,0,0,0.2);
  --shadow-lg: 0 4px 20px rgba(0,0,0,0.4), 0 12px 40px rgba(0,0,0,0.3);
  --hiw-bg:          {D_SURFACE};
  --hiw-border:      {D_BORDER};
  --hiw-header-bg:   rgba(30,77,123,0.25);
  --hiw-header-border: rgba(56,189,248,0.2);
  --insight-bg:      linear-gradient(135deg, rgba(30,77,123,0.18) 0%, rgba(5,150,105,0.12) 100%);
  --insight-border:  rgba(56,189,248,0.2);
  --icon-ingest-bg:  rgba(30,77,123,0.25);
  --icon-reason-bg:  rgba(109,40,217,0.2);
  --icon-surface-bg: rgba(5,150,105,0.18);
}}

/* ── Cards ────────────────────────────────────────────────────────────── */
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.1rem 1.3rem;
  margin-bottom: 0.8rem;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s, border-color 0.2s;
}}
.card:hover {{
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-l);
}}
.card-top {{ display: flex; gap: 0.9rem; align-items: flex-start; margin-bottom: 0.6rem; }}
.card-rank {{
  min-width: 28px; height: 28px;
  background: var(--primary); color: #fff;
  border-radius: 6px; font-size: 0.7rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}}
.card-name {{ font-size: 0.95rem; font-weight: 700; color: var(--text); line-height: 1.3; }}
.card-location {{ font-size: 0.75rem; color: var(--text3); margin-top: 2px; display: flex; align-items: center; gap: 4px; }}

/* ── Tags ─────────────────────────────────────────────────────────────── */
.tags {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }}
.tag {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; font-weight: 500;
}}
.tag-type {{ background: var(--icon-ingest-bg);  color: var(--primary); }}
.tag-own  {{ background: var(--icon-reason-bg);  color: #9F7AEA; }}
.tag-dist {{ background: var(--icon-surface-bg); color: var(--green); }}
.tag-beds {{ background: rgba(217,119,6,0.12);   color: var(--amber); }}

/* ── Trust block ──────────────────────────────────────────────────────── */
.trust-block {{ margin: 0.5rem 0; }}
.trust-row {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 4px; }}
.trust-value {{ font-size: 1rem; font-weight: 700; }}
.tv-high   {{ color: {GREEN}; }}
.tv-medium {{ color: {AMBER}; }}
.tv-low    {{ color: {RED}; }}
.tv-unver  {{ color: {MUTED}; }}
.trust-tier {{
  font-size: 0.62rem; font-weight: 700; padding: 2px 7px;
  border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px;
}}
.tier-high   {{ background: rgba(5,150,105,0.15);  color: var(--green); }}
.tier-medium {{ background: rgba(217,119,6,0.15);  color: var(--amber); }}
.tier-low    {{ background: rgba(220,38,38,0.12);  color: var(--red); }}
.tier-unver  {{ background: var(--surface2); color: var(--text4); }}
.trust-bar {{ height: 4px; background: var(--surface2); border-radius: 4px; overflow: hidden; }}
.trust-fill {{ height: 100%; border-radius: 4px; transition: width 0.4s; }}
.fill-high   {{ background: {GREEN}; }}
.fill-medium {{ background: {AMBER}; }}
.fill-low    {{ background: {RED}; }}
.fill-unver  {{ background: {MUTED}; }}

/* ── Capability chips ─────────────────────────────────────────────────── */
.caps {{ display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0; }}
.cap-yes {{
  display: inline-flex; align-items: center; gap: 4px;
  background: rgba(5,150,105,0.15); color: var(--green);
  padding: 2px 8px; border-radius: 20px; font-size: 0.68rem; font-weight: 600;
}}

/* ── Evidence ─────────────────────────────────────────────────────────── */
.evidence-list {{ margin-top: 6px; display: flex; flex-direction: column; gap: 4px; }}
.ev-item {{
  display: flex; gap: 6px; align-items: flex-start;
  font-size: 0.73rem; color: var(--text3); line-height: 1.5;
}}

/* ── Section heading ──────────────────────────────────────────────────── */
.section-head {{
  display: flex; align-items: center; gap: 0.7rem;
  margin: 1.6rem 0 0.8rem;
}}
.section-head-bar {{
  width: 3px; height: 18px;
  background: var(--primary); border-radius: 2px; flex-shrink: 0;
}}
.section-head-label {{
  font-size: 0.88rem; font-weight: 700; color: var(--text);
  text-transform: uppercase; letter-spacing: 0.6px;
}}
.section-head-line {{ flex: 1; height: 1px; background: var(--border); }}

/* ── Insight block ────────────────────────────────────────────────────── */
.insight-block {{
  background: var(--insight-bg);
  border: 1px solid var(--insight-border);
  border-radius: var(--r-sm);
  padding: 0.9rem 1.1rem;
  margin-top: 0.5rem;
}}
.insight-label {{
  font-size: 0.65rem; font-weight: 700; color: var(--primary);
  text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;
}}
.insight-text {{ font-size: 0.8rem; color: var(--text2); line-height: 1.65; }}

/* ── Intent box ───────────────────────────────────────────────────────── */
.intent-box {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: var(--r-sm);
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}}
.intent-label {{
  font-size: 0.65rem; font-weight: 700; color: var(--accent-d);
  text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 3px;
}}
.intent-text {{ font-size: 0.82rem; color: var(--text2); font-style: italic; }}

/* ── Search header ────────────────────────────────────────────────────── */
.search-header {{ margin-bottom: 1.2rem; }}
.search-header-title {{ font-size: 1.25rem; font-weight: 700; color: var(--text); margin-bottom: 4px; }}
.search-header-sub {{ font-size: 0.82rem; color: var(--text3); max-width: 640px; line-height: 1.6; }}

/* ── Example row ──────────────────────────────────────────────────────── */
.example-row {{ display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin: 0.5rem 0 0.8rem; }}
.example-label {{ font-size: 0.72rem; color: var(--text4); font-weight: 600; }}

/* ── Empty state ──────────────────────────────────────────────────────── */
.empty-state {{
  display: flex; flex-direction: column; align-items: center;
  padding: 3rem 0; color: var(--text4);
}}
.empty-state svg {{ width: 40px; height: 40px; stroke: var(--border); fill: none; stroke-width: 1.5; margin-bottom: 1rem; }}
.empty-msg {{ text-align: center; font-size: 0.82rem; line-height: 1.7; }}

/* ── Pipeline (home page) ─────────────────────────────────────────────── */
.pipeline-section {{
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 0 3rem;
}}
.pipeline-eyebrow {{
  font-size: 0.72rem; font-weight: 700; color: var(--accent-d);
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.6rem;
}}
.pipeline-title {{
  font-size: 2rem; font-weight: 700; color: var(--text); line-height: 1.2;
  margin-bottom: 0.8rem;
}}
.pipeline-title em {{ font-style: italic; color: var(--primary-l); }}
.pipeline-subtitle {{
  font-size: 0.88rem; color: var(--text3); line-height: 1.7;
  max-width: 620px; margin-bottom: 2rem;
}}
.pipeline-flow {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem;
  margin-bottom: 2rem;
}}
.pipeline-step {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.2rem 1.1rem;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s, transform 0.2s;
}}
.pipeline-step:hover {{ box-shadow: var(--shadow-lg); transform: translateY(-2px); }}
.step-layer {{
  font-size: 0.62rem; font-weight: 700; color: var(--accent-d);
  text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.6rem;
}}
.step-icon {{
  width: 38px; height: 38px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 0.7rem;
}}
.icon-ingest  {{ background: var(--icon-ingest-bg);  color: var(--primary); }}
.icon-reason  {{ background: var(--icon-reason-bg);  color: #9F7AEA; }}
.icon-surface {{ background: var(--icon-surface-bg); color: var(--green); }}
.step-name {{ font-size: 0.92rem; font-weight: 700; color: var(--text); margin-bottom: 0.35rem; }}
.step-desc {{ font-size: 0.76rem; color: var(--text3); line-height: 1.6; margin-bottom: 0.7rem; }}
.step-tags {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.step-tag {{
  background: var(--surface2); color: var(--text3);
  font-size: 0.65rem; font-weight: 500;
  padding: 2px 8px; border-radius: 20px; border: 1px solid var(--border);
}}

/* Feature chips */
.feature-row {{
  display: flex; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 2rem;
}}
.feature-chip {{
  display: flex; align-items: center; gap: 0.45rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 0.5rem 0.9rem;
  box-shadow: var(--shadow);
}}
.fc-label {{ font-size: 0.78rem; font-weight: 600; color: var(--text); }}
.fc-val   {{ font-size: 0.72rem; color: var(--text3); }}

/* ── How the agent works — framed card ───────────────────────────────── */
.hiw-card {{
  background: var(--hiw-bg);
  border: 1px solid var(--hiw-border);
  border-radius: var(--r);
  box-shadow: var(--shadow);
  overflow: hidden;
}}
.hiw-header {{
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.9rem 1.4rem;
  background: var(--hiw-header-bg);
  border-bottom: 1px solid var(--hiw-header-border);
}}
.hiw-header-dot {{
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-l); flex-shrink: 0;
}}
.hiw-title {{
  font-size: 0.78rem; font-weight: 700; color: var(--text);
  text-transform: uppercase; letter-spacing: 0.7px;
}}
.hiw-steps {{
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: start;
  gap: 0;
  padding: 1.4rem 1.6rem;
}}
.hiw-step {{
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}}
.hiw-num {{
  flex-shrink: 0;
  width: 30px; height: 30px;
  border-radius: 7px;
  background: var(--primary);
  color: #fff;
  font-size: 0.72rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(30,77,123,0.35);
}}
.hiw-step-body {{ flex: 1; }}
.hiw-step-title {{
  font-size: 0.82rem; font-weight: 700; color: var(--text);
  margin-bottom: 0.25rem;
}}
.hiw-step-text {{ font-size: 0.75rem; color: var(--text3); line-height: 1.6; }}
.hiw-connector {{
  display: flex; align-items: flex-start; padding-top: 0.55rem;
  color: var(--border); font-size: 1.2rem; padding: 0.55rem 0.6rem 0;
  flex-shrink: 0;
}}
.hiw-connector::after {{
  content: "→";
  color: var(--accent-d);
  font-size: 1rem;
  font-weight: 300;
}}

/* ── Coverage bar (discover page) ─────────────────────────────────────── */
.cov-item {{ margin-bottom: 0.55rem; }}
.cov-row {{ display: flex; justify-content: space-between; margin-bottom: 3px; }}
.cov-name {{ font-size: 0.76rem; font-weight: 600; color: var(--text2); }}
.cov-count {{ font-size: 0.76rem; color: var(--text4); font-weight: 500; }}
.cov-track {{ height: 5px; background: var(--surface2); border-radius: 4px; overflow: hidden; }}
.cov-fill {{ height: 100%; background: var(--primary); border-radius: 4px; transition: width 0.4s; }}

/* ── Compare table ────────────────────────────────────────────────────── */
.cmp-table {{
  width: 100%; border-collapse: collapse;
  font-size: 0.78rem; border-radius: var(--r); overflow: hidden;
  box-shadow: var(--shadow);
}}
.cmp-table thead {{ background: var(--primary); color: #fff; }}
.cmp-table th, .cmp-table td {{ padding: 0.55rem 1rem; text-align: left; }}
.cmp-table tbody tr:nth-child(even) {{ background: var(--surface2); }}
.cmp-table tbody tr {{ border-bottom: 1px solid var(--border); }}
.cmp-winner {{ color: {GREEN}; font-weight: 700; }}

/* ── Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: var(--surface2); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 10px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text4); }}

/* ── Footer ───────────────────────────────────────────────────────────── */
.app-footer {{
  text-align: center; padding: 2rem 0 1rem;
  font-size: 0.72rem; color: var(--text4);
  border-top: 1px solid var(--border);
  margin-top: 3rem; line-height: 2;
}}
.footer-brand {{ color: var(--primary); font-weight: 700; }}

/* ── Streamlit overrides ──────────────────────────────────────────────── */
[data-testid="stMetricValue"] {{
  font-size: 1.4rem !important; font-weight: 700 !important; color: var(--text) !important;
}}
[data-testid="stMetricLabel"] {{
  font-size: 0.72rem !important; color: var(--text3) !important;
}}
div[data-testid="stHorizontalBlock"] {{
  gap: 1rem !important;
}}
.stButton > button {{
  border-radius: 8px !important;
  font-family: 'Sora', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
}}
.stTextInput > div > div > input {{
  border-radius: var(--r-sm) !important;
  border-color: var(--border) !important;
  font-family: 'Sora', sans-serif !important;
  font-size: 0.85rem !important;
}}
</style>

<nav class="cp-nav">
  <a href="?page=home" target="_self" class="nav-logo">
    <div class="nav-logo-icon">
      <svg viewBox="0 0 24 24" width="17" height="17" fill="none"
           stroke="#0b1e3a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    </div>
    <div>
      <span class="nav-logo-name">CarePath AI</span>
      <span class="nav-logo-sub">Healthcare Intelligence</span>
    </div>
  </a>
  <div class="nav-tabs">
    {tabs_html}
  </div>
</nav>
""", unsafe_allow_html=True)
