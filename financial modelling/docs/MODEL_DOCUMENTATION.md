# Model documentation — HK listed equity case study

**Subject:** Techtronic Industries Co. Ltd (`0669.HK`)  
**Reporting currency:** USD (company reports in USD; shares listed in HKD)  
**Forecast:** Five annual periods from FY2025 (configurable in `config/case_study.yaml`)  
**Data source:** Yahoo Finance via `yfinance` (public, delayed; for case-study reproducibility—not investment advice)

**Data modes** (`config/case_study.yaml` → `research.data_mode`):

- **`latest` (default):** All fiscal periods returned by yfinance (including **FY2025** when available), current spot, and current peer metrics. Re-run the pipeline to refresh outputs and PDFs.
- **`point_in_time`:** Applies `research.knowledge_cutoff` — drops fiscal columns after the cutoff and uses historical spot (Oct-2025 case-study replay).

## 1. Objective

Reproduce a sell-side–style workflow:

1. Pull historical financials and market data  
2. Screen peers  
3. Build a linked three-statement forecast  
4. Value via unlevered DCF with sensitivities  
5. Triangulate with trading and transaction multiples  
6. Document assumptions for peer review  

## 2. Repository layout

| Path | Purpose |
|------|---------|
| `config/case_study.yaml` | Tickers, drivers, WACC, scenarios, rating |
| `src/data_pull.py` | Historical IS/BS/CF normalization |
| `src/three_statement.py` | Forecast linkage (P&L → cash → equity) |
| `src/dcf.py` | WACC, DCF, sensitivity grids |
| `src/comps.py` | Trading multiples and implied valuation |
| `src/peer_screening.py` | Peer metadata and sector flags |
| `src/charts.py` | Figures for memo appendix |
| `src/run_case_study.py` | End-to-end runner |
| `outputs/` | CSV, JSON, PNG artifacts |

## 3. Historical data normalization

`historical_to_wide()` maps yfinance statement labels to:

- Revenue, COGS, gross profit, operating income (EBIT proxy), net income  
- D&A and capex from cash flow statement  
- Debt, cash, equity, working capital building blocks  

Amounts are scaled to **USD millions** when median absolute values exceed 1e6 (raw SEC/HKEX filings via Yahoo).

**Limitations:** Yahoo maps vary by filer; associate income, FX, and one-offs are not fully adjusted. The case study uses **reported GAAP** lines unless manually overridden in config.

## 4. Forecast mechanics

**Revenue:** Prior-year revenue × (1 + growth rate vector). Growth rates are calibrated to the latest YoY print then follow the base vector in YAML.

**Margins:**

- Gross margin × revenue → gross profit  
- SG&A and R&D as % of revenue  
- D&A as % of revenue (simplified; not PP&E roll-forward)  
- EBIT = gross profit − SG&A − R&D − D&A  

**Tax:** Effective rate on positive EBIT (flat `tax_rate`).

**Balance sheet / cash flow (simplified):**

- Unlevered FCF = EBIT×(1−t) + D&A − Capex − ΔNWC  
- NWC = `nwc_pct_revenue` × revenue; ΔNWC vs prior year  
- Cash accumulates FCF; **debt held flat** in base (no mandatory refinancing/dividend sweep)  
- Equity += net income (100% retention in base)  

This is intentionally lean for transparency; a production model would add a debt schedule, dividends, buybacks, and PP&E.

## 5. DCF

**Unlevered FCF** from forecast years discounted at **WACC**:

```
WACC = w_e × (Rf + β × ERP) + w_d × Kd × (1 − t)
```

Defaults: Rf 4.2%, ERP 5.5%, β 1.05, Kd 4.5%, target debt/capital 12%, tax 17.5%.

**Terminal value:** Gordon growth on last explicit FCF:

```
TV = FCF_n × (1 + g) / (WACC − g)
```

**Equity bridge:** EV − net debt (debt − cash from latest actual) = equity value; per-share = equity × 1e6 / shares outstanding.

**Sensitivities:**

- WACC ±75/150 bps × terminal growth grid  
- Gross margin ±100/200 bps shift on full forecast  

**Scenarios (bull / base / bear):** Adjust growth, margin, terminal `g`, and WACC per `config/case_study.yaml`.

## 6. Comparable companies

**Trading comps:** EV/EBITDA, EV/Revenue, P/E from peer medians (ex-subject). Peers: global power tools / outdoor equipment names in YAML.

**Transaction comps:** Illustrative precedent EV/EBITDA multiples (sourced from public deal commentary; held in config—not live M&A database).

Implied prices from comps use subject LTM EBITDA/revenue/earnings and **peer median** multiples.

## 7. Reproducibility

```powershell
cd "d:\dev\financial modelling"
py -3 -m pip install -r requirements.txt
py -3 -m src.run_case_study
```

Refresh `config/case_study.yaml` to change assumptions; commit config + docs when publishing a memo revision.

## 8. Known gaps vs institutional models

- No segment disclosure (Milwaukee / Outdoor / EMEA) — consolidate at group level  
- No stock-based comp, pension, or lease capitalization roll-forward  
- HKD/USD listing currency not modeled (spot from Yahoo in listing currency)  
- Insurance-style embedded value not applicable; industrial DCF used throughout  

For interview or coursework submission, call out these gaps explicitly in the investment memo.
