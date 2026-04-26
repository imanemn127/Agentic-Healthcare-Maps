"""
Run the full Agentic Healthcare Maps pipeline in order.
Stops immediately if any step fails.
"""

import subprocess
import sys
from pathlib import Path


STEPS = [
    ("Dataset generation", [sys.executable, "generate_dataset.py"]),
    ("LLM extraction",     [sys.executable, "-m", "src.extractor"]),
    ("Trust scoring",      [sys.executable, "-m", "src.trust_scorer"]),
    ("Geocoding",          [sys.executable, "-m", "src.geocode"]),
    ("Map generation",     [sys.executable, "-m", "src.map_generator"]),
]


def run_step(name, cmd):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"\n[ERROR] '{name}' failed with exit code {result.returncode}.")
        sys.exit(result.returncode)
    print(f"[OK] {name} completed.")


def check_prerequisites():
    if not Path(".env").exists():
        print("ERROR: .env file not found. Copy .env.example and fill in your GROQ_API_KEY.")
        sys.exit(1)


if __name__ == "__main__":
    check_prerequisites()
    print("Starting Agentic Healthcare Maps pipeline...")

    for name, cmd in STEPS:
        run_step(name, cmd)

    print("\n" + "=" * 60)
    print("  Pipeline complete.")
    print("  Start the dashboard with:  streamlit run src/app.py")
    print("=" * 60)
