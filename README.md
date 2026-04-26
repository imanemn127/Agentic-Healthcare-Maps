# Agentic Healthcare Maps

**GitHub:** https://github.com/imanemn127/Agentic-Healthcare-Maps

An end-to-end agentic AI pipeline that processes messy Indian medical facility records at scale (tested up to 73 records on free API tier; built to handle 10,000+), extracts structured data using an LLM, scores each record for trustworthiness, and surfaces everything through an interactive map and a natural language query interface.

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
├── data/                       # created at runtime (gitignored)
├── maps/                       # created at runtime (gitignored)
├── src/
│   ├── schemas.py              # Pydantic data models
│   ├── extractor.py            # LLM extraction engine
│   ├── trust_scorer.py         # trust scoring + self-correction
│   ├── geocode.py              # Nominatim geocoding
│   ├── query_agent.py          # natural language query engine
│   ├── map_generator.py        # Folium map builder
│   └── app.py                  # Streamlit dashboard
└── submission/
    └── project_summary.txt
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
        └─> src/app.py            →  Streamlit dashboard
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

Run the full pipeline:

```bash
# one command:
python run_all.py

# or step by step:
python generate_dataset.py
python -m src.extractor
python -m src.trust_scorer
python -m src.geocode
python -m src.map_generator
streamlit run src/app.py
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
| Dashboard | `streamlit run src/app.py` | http://localhost:8501 |

---

## Tech stack

- **LLM / Query:** Groq API (Llama 3.3 70B) · Google Gemini (fallback)
- **Data:** Pandas · Pydantic v2 · OpenPyXL
- **Geocoding:** Geopy / Nominatim
- **Mapping:** Folium · MarkerCluster
- **Dashboard:** Streamlit
- **Language:** Python 3.9+
