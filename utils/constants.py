# utils/constants.py
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
DATA_PATH  = ROOT / "data" / "geocoded_facilities.csv"
MAP_PATH   = ROOT / "maps" / "healthcare_map.html"

# ── Palette ────────────────────────────────────────────────────────────────
PRIMARY    = "#1E4D7B"
PRIMARY_L  = "#2B6CB0"
PRIMARY_D  = "#153858"
ACCENT     = "#0EA5E9"
ACCENT_L   = "#38BDF8"
ACCENT_D   = "#0284C7"
GREEN      = "#059669"
GREEN_L    = "#10B981"
AMBER      = "#D97706"
AMBER_L    = "#F59E0B"
RED        = "#DC2626"
RED_L      = "#EF4444"
MUTED      = "#64748B"

# Light surface tokens
L_BG       = "#F0F4F8"
L_SURFACE  = "#FFFFFF"
L_SURFACE2 = "#F1F5F9"
L_BORDER   = "#CBD5E1"
L_TEXT     = "#0F172A"
L_TEXT2    = "#1E293B"
L_TEXT3    = "#475569"
L_TEXT4    = "#94A3B8"

# Dark surface tokens
D_BG       = "#0C1929"
D_SURFACE  = "#132033"
D_SURFACE2 = "#1A2D42"
D_BORDER   = "#243B53"
D_TEXT     = "#E8F1FA"
D_TEXT2    = "#B8CEE4"
D_TEXT3    = "#7A9CBD"
D_TEXT4    = "#4A6B8A"

FONT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Sora:wght@300;400;500;600;700&"
    "family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&"
    "family=JetBrains+Mono:wght@400;500&"
    "display=swap"
)

# ── SVG icon path strings ──────────────────────────────────────────────────
ICO_PIN      = "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
ICO_BUILDING = "M3 21h18M3 7l9-4 9 4M4 7v14M20 7v14M9 21V11h6v10"
ICO_SHIELD   = "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
ICO_BED      = "M2 4v16M2 8h20a2 2 0 0 1 2 2v10M2 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2M12 8v8"
ICO_CHECK    = "M20 6L9 17l-5-5"
ICO_QUOTE    = "M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1zm12 0c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"
ICO_DIST     = "M17.657 16.657L13.414 20.9a1.998 1.998 0 0 1-2.827 0l-4.244-4.243a8 8 0 1 1 11.314 0z"

_ICO_DB      = "M12 2C6.48 2 2 3.79 2 6v12c0 2.21 4.48 4 10 4s10-1.79 10-4V6c0-2.21-4.48-4-10-4zM2 12c0 2.21 4.48 4 10 4s10-1.79 10-4M2 6c0 2.21 4.48 4 10 4s10-1.79 10-4"
_ICO_BRAIN   = "M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.84A2.5 2.5 0 0 1 9.5 2M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.84A2.5 2.5 0 0 0 14.5 2"
_ICO_MAP2    = "M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4zM8 2v16M16 6v16"
_ICO_SHIELD2 = "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
_ICO_ARROW   = "M5 12h14M12 5l7 7-7 7"

# ── Capability metadata ────────────────────────────────────────────────────
CAP_META = {
    "has_icu":               "ICU",
    "has_emergency_trauma":  "Emergency",
    "has_oncology":          "Oncology",
    "has_dialysis":          "Dialysis",
    "has_anesthesiologist":  "Anaesthesia",
    "supports_appendectomy": "Surgery",
}

EXAMPLE_QUERIES = [
    "ICU hospital in Karnataka",
    "Government dialysis centre Bihar",
    "Emergency trauma Maharashtra",
    "Oncology hospital Rajasthan",
]

CHART_COLORS = {
    "high":       GREEN,
    "medium":     AMBER,
    "low":        RED,
    "unverified": MUTED,
}