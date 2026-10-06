# Portfolio PDFs & GitHub Pages (`coolwg-dev.github.io`)

## Generate PDFs

From the repo root (run the model first so figures and JSON are current):

```powershell
py -3 -m src.run_case_study
py -3 scripts/build_portfolio_pdfs.py
```

Outputs:

| File | Description |
|------|-------------|
| `portfolio/pdf/TTI_0669HK_Investment_Memo.pdf` | Full investment memo (charts + key tables embedded) |
| `portfolio/pdf/TTI_0669HK_Valuation_Summary.pdf` | One-page valuation slide |
| `portfolio/valuation_model.py` | Commented Python entry point for reviewers |
| `portfolio/MODEL_WORKBOOK_STRUCTURE.md` | Excel tab map (spreadsheet structure) |

Add `reportlab` is already in `requirements.txt` after you pull latest.

---

## Suggested URL structure

Your site is a **user/org GitHub Pages** site: `https://coolwg-dev.github.io/`.

Use a **stable project slug** under a folder (works with the `coolwg-dev.github.io` repo):

| URL | Use case |
|-----|----------|
| **`https://coolwg-dev.github.io/finance/hk-equity-tti/`** | Recommended — groups all finance work under `/finance/` |
| `https://coolwg-dev.github.io/projects/hk-equity-tti/` | If you prefer a generic `/projects/` bucket |
| `https://coolwg-dev.github.io/case-studies/tti-0669-hk/` | Emphasizes “case study” wording for recruiters |

Pick **one slug** and keep it; link it from your main portfolio homepage as “HK Listed Equity — TTI (0669.HK)”.

### Placeholder naming convention

```
/finance/<market>-<theme>-<ticker-slug>/
         hk-equity-tti
         hk-equity-aia-1299   (future)
```

---

## Deploy to GitHub Pages (user site)

**Option A — Everything in `coolwg-dev.github.io` (simplest for one portfolio site)**

1. In your **`coolwg-dev.github.io`** repository, create:

   ```
   finance/hk-equity-tti/
     index.html          ← copy from portfolio/website/hk-equity-tti/index.html
     styles.css
   finance/hk-equity-tti/pdf/
     TTI_0669HK_Investment_Memo.pdf
     TTI_0669HK_Valuation_Summary.pdf
   ```

2. Fix links in `index.html`: PDFs should be `./pdf/...` (not `../../pdf/...`).

3. Commit, push to `main`. In repo **Settings → Pages**, source = **Deploy from branch** → `main` → `/ (root)`.

4. Live URL: **`https://coolwg-dev.github.io/finance/hk-equity-tti/`**

**Option B — Model code in a separate repo**

- Keep code in `financial-modelling` (or similar).
- Pages site only hosts HTML + PDFs; link “View source” to the code repo.
- Good when the model repo is private but you still want public PDFs.

**Option C — Project site from the model repo**

- Enable Pages on the model repo: **Settings → Pages → Folder `/docs`**.
- URL becomes `https://coolwg-dev.github.io/<repo-name>/` (not under root `/finance/` unless you use a custom domain).

---

## Main portfolio homepage link

On `coolwg-dev.github.io/index.html`, add a card:

```html
<article>
  <h3><a href="/finance/hk-equity-tti/">HK Equity — Techtronic (0669.HK)</a></h3>
  <p>DCF, comps, three-statement forecast · Buy (base case)</p>
  <a href="/finance/hk-equity-tti/pdf/TTI_0669HK_Investment_Memo.pdf">Memo PDF</a>
</article>
```

---

## GitHub repo README badges (optional)

In the model repo README, link the live case study:

```markdown
**Live portfolio:** [coolwg-dev.github.io/finance/hk-equity-tti](https://coolwg-dev.github.io/finance/hk-equity-tti/)
```

---

## Upload checklist for recruiters

- [ ] `TTI_0669HK_Investment_Memo.pdf`
- [ ] `TTI_0669HK_Valuation_Summary.pdf`
- [ ] Link to `portfolio/valuation_model.py` or full repo
- [ ] `MODEL_WORKBOOK_STRUCTURE.md` (or exported `.xlsx` later)
- [ ] One-line disclaimer: educational / not advice
