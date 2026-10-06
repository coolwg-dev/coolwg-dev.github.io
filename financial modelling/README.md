# Hong Kong Listed Equity — Stock Pitch & Valuation Case Study (2025–2026)

Independent research template covering a **three-statement forecast**, **DCF with sensitivities** (WACC, terminal growth, margins), **trading and transaction comps**, and a **rated investment memo** with bull/base/bear scenarios.

**Subject company:** [Techtronic Industries](https://www.hkex.com.hk) (`0669.HK`) — HK-headquartered global power tools leader (Milwaukee, Ryobi).

## Quick start

```powershell
cd "d:\dev\financial modelling"
py -3 -m pip install -r requirements.txt
py -3 -m src.run_case_study
```

Outputs land in `outputs/` (forecasts, sensitivities, comps, charts, `valuation_summary.json`).

## Documentation

- [Investment memo](docs/INVESTMENT_MEMO.md) — thesis, catalysts, scenarios, **Buy** rating (base case)  
- [Model documentation](docs/MODEL_DOCUMENTATION.md) — assumptions, linkage logic, limitations  

## Customize another HK name

Edit `config/case_study.yaml`: change `company.ticker`, peer lists, drivers, and WACC. Re-run the pipeline.

## Stack

Python 3.11+, `yfinance`, `pandas`, `matplotlib`, `seaborn`, `PyYAML`.

**Note:** Default config replays **October 2025** (`research.data_mode: point_in_time`). Public delayed data only; not investment advice.

## Portfolio (PDFs & website)

```powershell
py -3 -m src.run_case_study
py -3 scripts/build_portfolio_pdfs.py
```

- PDFs: `portfolio/pdf/`
- Commented script: `portfolio/valuation_model.py`
- Excel tab map: `portfolio/MODEL_WORKBOOK_STRUCTURE.md`
- GitHub Pages template: `portfolio/website/hk-equity-tti/` — see [docs/PORTFOLIO_AND_WEBSITE.md](docs/PORTFOLIO_AND_WEBSITE.md) for deployment notes

**Live portfolio:** [coolwg-dev.github.io/finance/hk-equity-tti](https://coolwg-dev.github.io/finance/hk-equity-tti/)
