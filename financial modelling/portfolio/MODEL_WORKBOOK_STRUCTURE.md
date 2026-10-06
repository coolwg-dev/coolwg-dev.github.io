# Financial model workbook structure (Excel parity)

Use this layout if you mirror the Python model in Excel/Google Sheets. Tab names map to `outputs/*.csv` from the pipeline.

| Tab | Purpose | Key links |
|-----|---------|-----------|
| **Cover** | Ticker, date, rating, spot vs DCF | Manual + `valuation_summary.json` |
| **Inputs** | WACC building blocks, terminal g, tax, beta | `config/case_study.yaml` → `dcf` |
| **Drivers** | Revenue growth vector, margin %, capex/NWC % | `config/case_study.yaml` → `drivers` |
| **Hist_IS** | Historical income statement (USD m) | `outputs/data/*_historical.csv` |
| **Forecast_IS** | P&L forecast | `outputs/three_statement_forecast.csv` |
| **Forecast_CF** | UFCF bridge (EBIT, D&A, capex, ΔNWC) | Same CSV, FCF columns |
| **DCF** | Discount factors, PV explicit, terminal value | `src/dcf.py` logic |
| **Sensitivity** | WACC × terminal g grid; margin toggles | `dcf_sensitivity_*.csv` |
| **Scenarios** | Bull / base / bear | `dcf_scenarios.csv` |
| **Comps_Trading** | Peer multiples | `trading_comps.csv` |
| **Comps_Txn** | Precedent deals (illustrative) | `transaction_comps.csv` |
| **Comps_Implied** | Median-multiple implied price | `comps_implied_valuation.csv` |

**Check row:** `Forecast_CF!UFCF` sum-discounted should reconcile to `DCF!EV` (within rounding).

**Listing currency:** Model equity value in USD; convert to HKD with `fx_hkd_usd` on Cover tab (see `valuation_summary.json`).
