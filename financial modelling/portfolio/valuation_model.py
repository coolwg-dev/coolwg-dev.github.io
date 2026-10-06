"""
Portfolio sample: HK equity valuation pipeline (Techtronic 0669.HK).

This script is a readable entry point for recruiters and reviewers.
It documents the model flow and delegates to the full implementation in `src/`.

Educational case study only — not investment advice.

Run from repository root:
    py -3 -m pip install -r requirements.txt
    py -3 portfolio/valuation_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports when executed as a script from repo root or portfolio/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    """
    End-to-end workflow:
      1. Load YAML assumptions (ticker, WACC, growth, scenarios).
      2. Pull historical statements via yfinance.
      3. Build 5-year three-statement forecast (linked FCF).
      4. Run unlevered DCF + WACC/growth/margin sensitivities.
      5. Trading + transaction comps triangulation.
      6. Export CSV/JSON/charts under outputs/.
    """
    from src.run_case_study import main as run_pipeline

    print("=" * 60)
    print("HK Listed Equity Case Study — Valuation Model")
    print("Subject: 0669.HK (config/case_study.yaml)")
    print("=" * 60)
    run_pipeline()
    print()
    print("Next: py -3 -m scripts.build_portfolio_pdfs")
    print("Docs:  docs/MODEL_DOCUMENTATION.md")
    print("Memo:  docs/INVESTMENT_MEMO.md")


if __name__ == "__main__":
    main()
