# CarePath AI — Agentic Healthcare Maps

**GitHub:** https://github.com/imanemn127/Agentic-Healthcare-Maps

An end-to-end agentic AI pipeline that processes messy Indian medical facility records at scale (tested up to 73 records on free API tier; built to handle 10,000+), extracts structured data using an LLM, scores each record for trustworthiness, and surfaces everything through an interactive map and a natural-language query interface — all wrapped in a polished multi-page Streamlit dashboard.

---

## What it does

Raw facility data is noisy — inconsistent formatting, missing fields, contradictions between columns. This pipeline cleans it automatically:

1. **LLM Extraction** — processes batches of raw records and pulls out structured fields (facility type, bed count, specialties, emergency status) along with verbatim evidence sentences so every extracted value is traceable.

2. **Trust Scoring with self-correction** — a weighted score combines field completeness, rule-based contradiction checks, geocoding quality, and an LLM validator. Records scoring below 0.4 are automatically re-extracted with a corrective prompt. The loop closes without human intervention.

3. **Geocoding** — facility addresses are resolved to coordinates using Nominatim with a 4-level fallback strategy and a persistent cache to avoid redundant requests.

4. **Interactive Map** — a Folium map colour-coded by trust tier, with a separate layer marking medical deserts (grid cells with no nearby facility).

5. **Natural Language Query** — ask "ICU hospital in Maharashtra" and the agent parses the intent, filters the dataset, and returns ranked results with capability details and evidence sentences. Uses Groq (Llama 3.3 70B) with Gemini as fallback.

---

## Project structure

```
Agentic-Healthcare-Maps/
├── .env.example
├── requirements.txt
├── run_all.py                  # one-click pipeline runner
├── generate_dataset.py
├── app.py                      # Streamlit entry point (multi-page router)
├── data/                       # created at runtime (gitignored)
├── maps/                       # created at runtime (gitignored)
├── assets/
│   └── favicon.png
├── src/
│   ├── schemas.py              # Pydantic data models
│   ├── extractor.py            # LLM extraction engine
│   ├── fast_extractor.py       # faster extraction variant
│   ├── trust_scorer.py         # trust scoring + self-correction
│   ├── geocode.py              # Nominatim geocoding
│   ├── query_agent.py          # natural language query engine
│   └── map_generator.py        # Folium map builder
├── pages/
│   ├── home.py                 # Hero, pipeline diagram, "How the Agent Works"
│   ├── discover.py             # Interactive map + state coverage bars
│   ├── search.py               # Natural-language search UI
│   └── analytics.py            # 6 Altair charts + capability table + data table
└── utils/
    ├── __init__.py
    ├── constants.py            # Design tokens, icon SVG paths, CAP_META, palette
    ├── styles.py               # CSS builder — navbar, dark/light mode, all components
    └── ui.py                   # Shared UI primitives, card renderers, data loaders
```

---

## Pipeline flow

```
generate_dataset.py
  └─> data/raw_facilities.xlsx
        │
        ▼
src/extractor.py          [LLM batch extraction with evidence sentences]
  └─> data/extracted_facilities.jsonl
        │
        ▼
src/trust_scorer.py       [rule scoring + LLM validator + self-correction]
  └─> data/scored_facilities.jsonl
        │
        ▼
src/geocode.py            [Nominatim, 4-level fallback, persistent cache]
  └─> data/geocoded_facilities.csv
        │
        ├─> src/map_generator.py  →  maps/healthcare_map.html
        └─> app.py                →  Streamlit dashboard
                                       └─> src/query_agent.py
```

---

## Quick start

```bash
git clone https://github.com/imanemn127/Agentic-Healthcare-Maps.git
cd Agentic-Healthcare-Maps

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your API keys:

```
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here   # optional fallback
```

Run the full pipeline then launch the dashboard:

```bash
# one command:
python run_all.py

# or step by step:
python generate_dataset.py
python -m src.extractor
python -m src.trust_scorer
python -m src.geocode
python -m src.map_generator

# launch dashboard:
streamlit run app.py
```

Dashboard opens at http://localhost:8501

---

## Individual scripts

| Script | Command | Output |
|--------|---------|--------|
| Dataset generator | `python generate_dataset.py` | `data/raw_facilities.xlsx` |
| LLM extractor | `python -m src.extractor` | `data/extracted_facilities.jsonl` |
| Trust scorer | `python -m src.trust_scorer` | `data/scored_facilities.jsonl` |
| Geocoder | `python -m src.geocode` | `data/geocoded_facilities.csv` |
| Map generator | `python -m src.map_generator` | `maps/healthcare_map.html` |
| Query agent (CLI) | `python src/query_agent.py "ICU hospital in Maharashtra"` | JSON to stdout |
| Dashboard | `streamlit run app.py` | http://localhost:8501 |

---

## Dashboard pages

### Home
Hero section describing the three-layer agentic pipeline (Ingest → Reason → Surface), live KPI chips (facilities indexed, states covered, geocoded records, high-trust records), and a **"How the Agent Works"** framed card that walks through the three query steps with numbered blue cubes.

### Discover
Full-width interactive Folium map with trust-tier colour coding and cluster markers. Side panel shows a state-coverage bar chart (top 10 states) and a data-quality breakdown by trust tier with geocoding coverage stats.

### Search
Natural-language facility search powered by Groq / Llama 3.3. Parses intent into structured filters (state, type, ownership, capabilities), ranks results by trust score + distance, and returns facility cards with evidence sentences. Optional AI insight per result. Supports example queries and CSV/JSON export.

### Analytics
Filter panel (state, type, trust tier, min score) → overview metrics → AI dataset analysis → six interactive Altair charts:

| Chart | Type |
|-------|------|
| Top 15 States by Facility Count | Vertical bar |
| Trust Tier Distribution | Donut |
| Top 10 Facility Types | Horizontal bar |
| Trust Score Distribution | Histogram |
| Ownership Breakdown | Donut |
| Capability Coverage by State | Heatmap (state × capability) |

Followed by a capability coverage table and a sortable top-500 dataset table.

---

## UI architecture

The dashboard is built as a **single-entry multi-page Streamlit app** (`app.py`) that routes via `?page=` query params — no `st.navigation()`, so URLs are bookmarkable and the nav state survives page reload.

- **Navbar** — sticky top bar with navy gradient, logo left, tabs right. Active tab is underlined with the accent colour. Built as injected HTML/CSS, not a Streamlit component.
- **Dark / light mode** — all colour tokens are CSS custom properties. Both `@media (prefers-color-scheme: dark)` and `[data-theme="dark"]` (Streamlit's own class) are handled so the palette flips automatically.
- **No Streamlit chrome** — sidebar, header bar, deploy button, and footer are all hidden.

---

## Tech stack

- **LLM / Query:** Groq API (Llama 3.3 70B) · Google Gemini (fallback)
- **Data:** Pandas · Pydantic v2 · OpenPyXL
- **Geocoding:** Geopy / Nominatim
- **Mapping:** Folium · MarkerCluster
- **Charts:** Altair
- **Dashboard:** Streamlit (multi-page, custom HTML/CSS navbar)
- **Language:** Python 3.9+
