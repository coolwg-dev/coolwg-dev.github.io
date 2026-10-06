"""
Build portfolio-ready PDFs: investment memo + valuation summary slide.

Usage (from repo root):
    py -3 -m scripts.build_portfolio_pdfs

Requires: reportlab, Pillow. Run case study first for latest figures.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "portfolio"
PDF_DIR = PORTFOLIO / "pdf"
FIG_DIR = ROOT / "outputs" / "figures"
OUT_DIR = ROOT / "outputs"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.presentation import load_research_dates, published_label, to_reportlab_datetime

REQUIRED_FIGURES = (
    "revenue_ebit_forecast.png",
    "dcf_sensitivity.png",
    "trading_comps_ev_ebitda.png",
    "dcf_scenarios.png",
)


def _load_published_context():
    with open(ROOT / "config" / "case_study.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    research, cutoff, published = load_research_dates(cfg)
    return research, cutoff, published


def _apply_source_date_epoch(published) -> str | None:
    """ReportLab reads SOURCE_DATE_EPOCH for PDF CreationDate/ModDate metadata."""
    when = to_reportlab_datetime(published)
    epoch = str(int(time.mktime(when.timetuple())))
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = epoch
    return previous


def _memo_cover_banner(published, usable_width: float) -> list:
    banner_style = ParagraphStyle(
        "Banner",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=14,
    )
    text = (
        f"INDEPENDENT EQUITY RESEARCH · PUBLISHED {published_label(published).upper()} · "
        "POINT-IN-TIME (31 OCT 2025 CUTOFF)"
    )
    tbl = Table([[Paragraph(text, banner_style)]], colWidths=[usable_width])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e3a5f")),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return [tbl, Spacer(1, 0.15 * inch)]


def _ensure_model_outputs() -> None:
    missing_figs = [f for f in REQUIRED_FIGURES if not (FIG_DIR / f).exists()]
    if not missing_figs and (OUT_DIR / "valuation_summary.json").exists():
        return
    print("Generating charts and valuation outputs (first run or stale figures)...")
    subprocess.run([sys.executable, "-m", "src.run_case_study"], cwd=ROOT, check=True)


def _resolve_figure_path(path: str) -> Path:
    normalized = path.replace("\\", "/").lstrip("./")
    while normalized.startswith("../"):
        normalized = normalized[3:]
    candidate = ROOT / normalized
    if candidate.exists():
        return candidate
    return ROOT / "outputs" / "figures" / Path(normalized).name


def _figure_flowable(path: str, caption: str, usable_width: float, cap_style) -> list:
    resolved = _resolve_figure_path(path)
    if not resolved.exists():
        return [
            Paragraph(
                f"<i>{_md_inline_to_xml(caption)} — figure not found; run case study pipeline.</i>",
                cap_style,
            ),
            Spacer(1, 0.1 * inch),
        ]
    with PILImage.open(resolved) as im:
        w, h = im.size
    aspect = h / w
    display_w = usable_width
    display_h = display_w * aspect
    max_h = 4.75 * inch
    if display_h > max_h:
        display_h = max_h
        display_w = display_h / aspect
    img = Image(str(resolved), width=display_w, height=display_h)
    cap = Paragraph(f"<i>{_md_inline_to_xml(caption)}</i>", cap_style)
    return [Spacer(1, 0.06 * inch), img, Spacer(1, 0.04 * inch), cap, Spacer(1, 0.12 * inch)]


def _csv_table_flowable(csv_path: Path, usable_width: float, title: str) -> list:
    if not csv_path.exists():
        return [Paragraph(f"<i>{title} — data not available.</i>", cap_style_placeholder())]
    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []
    # Format numeric cells for readability
    formatted = [rows[0]]
    for row in rows[1:]:
        formatted.append(
            [
                f"{float(cell):,.2f}" if re.fullmatch(r"-?\d+(\.\d+)?", str(cell).strip()) else cell
                for cell in row
            ]
        )
    title_style = ParagraphStyle(
        "TableTitle",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=4,
    )
    return [
        Paragraph(_md_inline_to_xml(title), title_style),
        _table_flowable(formatted, usable_width),
        Spacer(1, 0.12 * inch),
    ]


def cap_style_placeholder():
    return ParagraphStyle("Cap", fontSize=9, textColor=colors.grey, fontName="Helvetica-Oblique")


def _pit_snapshot_block(usable_width: float) -> list:
    """Key valuation metrics aligned to knowledge cutoff (from valuation_summary.json)."""
    summary_path = OUT_DIR / "valuation_summary.json"
    if not summary_path.exists():
        return [Paragraph("<i>Run case study pipeline to populate point-in-time snapshot.</i>", cap_style_placeholder())]
    meta = json.loads(summary_path.read_text(encoding="utf-8"))
    r = meta.get("research") or {}
    dcf = meta.get("base_dcf") or {}
    spot = meta.get("spot_price_hkd")
    dcf_hkd = dcf.get("value_per_share_hkd")
    upside = meta.get("dcf_upside_vs_spot")
    fy = r.get("last_actual_fiscal_year")
    cutoff = r.get("knowledge_cutoff") or "—"
    mode = r.get("data_mode", "—")
    rows = [
        ["Item", "Value"],
        ["Data mode", mode],
        ["Published", meta.get("research", {}).get("published_at") or meta.get("published_at", "—")[:10]],
        ["Knowledge cutoff", cutoff],
        ["Last actual fiscal year", f"FY{fy}" if fy else "—"],
        ["Spot price (HKD)", f"{spot:.2f}" if spot else "—"],
        ["Base-case DCF (HKD / sh)", f"{dcf_hkd:.1f}" if dcf_hkd else "—"],
        ["DCF vs spot", f"{upside:+.1%}" if upside is not None else "—"],
        ["Recommendation", meta.get("recommendation", "—")],
    ]
    title_style = ParagraphStyle(
        "SnapTitle",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=4,
    )
    return [
        Paragraph("Point-in-time valuation snapshot (model output)", title_style),
        _table_flowable(rows, usable_width),
        Spacer(1, 0.1 * inch),
    ]


def _auto_blocks(usable_width: float) -> dict[str, list]:
    blocks: dict[str, list] = {}
    blocks["<!-- AUTO:pit_snapshot -->"] = _pit_snapshot_block(usable_width)
    blocks["<!-- AUTO:scenario_prices -->"] = _csv_table_flowable(
        OUT_DIR / "dcf_scenarios.csv",
        usable_width,
        "Table — Quantified DCF scenarios (implied share price)",
    )
    blocks["<!-- AUTO:comps_implied -->"] = _csv_table_flowable(
        OUT_DIR / "comps_implied_valuation.csv",
        usable_width,
        "Table — Implied valuation from peer median multiples",
    )
    blocks["<!-- AUTO:txn_comps -->"] = _csv_table_flowable(
        OUT_DIR / "transaction_comps.csv",
        usable_width,
        "Table — Illustrative transaction comps (EV/EBITDA)",
    )
    return blocks


def _md_inline_to_xml(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def _parse_table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        if not line.strip().startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= {"-", ":"} for c in cells):
            continue
        rows.append(cells)
    return rows


def _table_flowable(rows: list[list[str]], usable_width: float) -> Table:
    """Build a word-wrapped table that fits within printable page width."""
    ncols = max(len(r) for r in rows)
    normalized = [r + [""] * (ncols - len(r)) for r in rows]

    font_size = 7.5 if ncols >= 4 else 8.5 if ncols == 3 else 9
    header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=font_size,
        leading=font_size + 2,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=font_size,
        leading=font_size + 2,
        textColor=colors.HexColor("#222222"),
    )

    data: list[list[Paragraph]] = []
    for ri, row in enumerate(normalized):
        style = header_style if ri == 0 else cell_style
        data.append(
            [
                Paragraph(_md_inline_to_xml(c) if c else "—", style)
                for c in row
            ]
        )

    if ncols == 2:
        col_widths = [usable_width * 0.34, usable_width * 0.66]
    elif ncols == 3:
        col_widths = [usable_width * 0.28, usable_width * 0.36, usable_width * 0.36]
    else:
        label_w = min(usable_width * 0.2, 1.15 * inch)
        rest = (usable_width - label_w) / max(ncols - 1, 1)
        col_widths = [label_w] + [rest] * (ncols - 1)

    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def markdown_to_flowables(md_path: Path, styles, usable_width: float) -> list:
    raw = md_path.read_text(encoding="utf-8").splitlines()
    flow: list = []
    auto_blocks = _auto_blocks(usable_width)
    i = 0
    body = styles["BodyText"]
    fig_caption = ParagraphStyle(
        "FigCaption",
        parent=body,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        fontName="Helvetica-Oblique",
    )
    body_small = ParagraphStyle(
        "BodySmall",
        parent=body,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333"),
    )
    quote = ParagraphStyle(
        "Quote",
        parent=body_small,
        leftIndent=12,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Oblique",
    )

    while i < len(raw):
        line = raw[i]
        if line.strip() == "---":
            flow.append(Spacer(1, 0.15 * inch))
            i += 1
            continue
        if line.startswith("# "):
            flow.append(Paragraph(_md_inline_to_xml(line[2:].strip()), styles["Title"]))
            flow.append(Spacer(1, 0.12 * inch))
            i += 1
            continue
        if line.startswith("## "):
            flow.append(Spacer(1, 0.08 * inch))
            flow.append(Paragraph(_md_inline_to_xml(line[3:].strip()), styles["Heading2"]))
            flow.append(Spacer(1, 0.06 * inch))
            i += 1
            continue
        if line.startswith("### "):
            flow.append(Paragraph(_md_inline_to_xml(line[4:].strip()), styles["Heading3"]))
            flow.append(Spacer(1, 0.04 * inch))
            i += 1
            continue
        if line.strip().startswith("> "):
            flow.append(Paragraph(_md_inline_to_xml(line.strip()[2:]), quote))
            i += 1
            continue
        if line.strip() in auto_blocks:
            flow.extend(auto_blocks[line.strip()])
            i += 1
            continue
        img_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if img_match:
            caption, path = img_match.groups()
            flow.extend(_figure_flowable(path, caption, usable_width, fig_caption))
            i += 1
            continue
        if line.strip().startswith("|"):
            table_lines = []
            while i < len(raw) and raw[i].strip().startswith("|"):
                table_lines.append(raw[i])
                i += 1
            rows = _parse_table_rows(table_lines)
            if rows:
                flow.append(_table_flowable(rows, usable_width))
                flow.append(Spacer(1, 0.1 * inch))
            continue
        if line.strip().startswith("```"):
            i += 1
            code_lines = []
            while i < len(raw) and not raw[i].strip().startswith("```"):
                code_lines.append(raw[i])
                i += 1
            if i < len(raw):
                i += 1
            code = "<br/>".join(_md_inline_to_xml(x) for x in code_lines)
            flow.append(Paragraph(code, body_small))
            flow.append(Spacer(1, 0.08 * inch))
            continue
        if line.strip().startswith("- "):
            flow.append(Paragraph("• " + _md_inline_to_xml(line.strip()[2:]), body))
            i += 1
            continue
        if re.match(r"^\d+\.\s", line.strip()):
            flow.append(Paragraph(_md_inline_to_xml(line.strip()), body))
            i += 1
            continue
        if line.strip():
            flow.append(Paragraph(_md_inline_to_xml(line.strip()), body))
        i += 1
    return flow


def build_memo_pdf() -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / "TTI_0669HK_Investment_Memo.pdf"
    if out.exists():
        out.unlink()
    _, cutoff, published = _load_published_context()
    styles = getSampleStyleSheet()
    styles["Title"].fontSize = 20
    styles["Title"].textColor = colors.HexColor("#1e3a5f")
    styles["Heading2"].fontSize = 13
    styles["Heading2"].textColor = colors.HexColor("#1e3a5f")
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14

    left_margin = 0.65 * inch
    right_margin = 0.65 * inch
    usable_width = A4[0] - left_margin - right_margin

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        rightMargin=right_margin,
        leftMargin=left_margin,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Techtronic Industries (0669.HK) — Investment Memo",
        author="Independent Research Case Study",
    )

    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    footer_line = (
        f"Published October 2025 · Knowledge cutoff 31 Oct 2025 · Educational use only · Page "
    )

    def on_page(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(left_margin, 0.5 * inch, f"{footer_line}{doc_.page}")
        canvas.restoreState()

    story = markdown_to_flowables(ROOT / "docs" / "INVESTMENT_MEMO.md", styles, usable_width)
    story[:0] = _memo_cover_banner(published, usable_width)
    stamp = (
        f"<i>Document published {published_label(published)}. "
        "Financials through FY2024 actual; spot and comps as of 31 October 2025.</i>"
    )
    summary_path = OUT_DIR / "valuation_summary.json"
    if summary_path.exists():
        meta = json.loads(summary_path.read_text(encoding="utf-8"))
        r = meta.get("research") or {}
        fy = r.get("last_actual_fiscal_year")
        spot = meta.get("spot_price_hkd")
        dcf_hkd = (meta.get("base_dcf") or {}).get("value_per_share_hkd")
        if spot and dcf_hkd:
            stamp = (
                f"<i>Published {published_label(published)} · "
                f"Spot {spot:.2f} HKD · Base DCF {dcf_hkd:.1f} HKD · Last actual FY{fy}.</i>"
            )
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(stamp, footer_style))
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return out


def _load_summary() -> dict:
    path = ROOT / "outputs" / "valuation_summary.json"
    if not path.exists():
        raise FileNotFoundError("Run `py -3 -m src.run_case_study` before building PDFs.")
    return json.loads(path.read_text(encoding="utf-8"))


def build_valuation_slide_pdf() -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / "TTI_0669HK_Valuation_Summary.pdf"
    if out.exists():
        out.unlink()
    _, cutoff, published = _load_published_context()
    summary = _load_summary()
    dcf = summary["base_dcf"]
    spot = summary["spot_price_hkd"]
    upside = summary.get("dcf_upside_vs_spot")

    scenarios_path = ROOT / "outputs" / "dcf_scenarios.csv"
    scenarios = []
    if scenarios_path.exists():
        import csv

        with open(scenarios_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                scenarios.append(row)

    page_w, page_h = landscape(A4)
    doc = SimpleDocTemplate(
        str(out),
        pagesize=landscape(A4),
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title="TTI Valuation Summary",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SlideTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#1e3a5f"),
        alignment=TA_LEFT,
    )
    sub_style = ParagraphStyle(
        "SlideSub",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#444444"),
    )
    kpi_label = ParagraphStyle("KpiLabel", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    kpi_value = ParagraphStyle(
        "KpiValue",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=colors.HexColor("#1e3a5f"),
    )

    story = [
        Paragraph("Valuation Summary — Techtronic Industries (0669.HK)", title_style),
        Paragraph(
            "Hong Kong Listed Equity · Independent Research Case Study · "
            f"Published {published_label(published)} · Knowledge cutoff 31 Oct 2025",
            sub_style,
        ),
        Spacer(1, 0.2 * inch),
    ]

    rating = summary.get("recommendation", "—")
    kpi_data = [
        [
            Paragraph("Recommendation", kpi_label),
            Paragraph("Spot (HKD)", kpi_label),
            Paragraph("DCF (HKD)", kpi_label),
            Paragraph("DCF upside", kpi_label),
        ],
        [
            Paragraph(f"<b>{rating}</b>", kpi_value),
            Paragraph(f"{spot:.1f}", kpi_value),
            Paragraph(f"{dcf.get('value_per_share_hkd', 0):.1f}", kpi_value),
            Paragraph(f"{upside:.0%}" if upside is not None else "—", kpi_value),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[2.2 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1e3a5f")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dde3ea")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f4f8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 0.2 * inch))

    dcf_rows = [
        ["Metric", "Value"],
        ["WACC", f"{dcf['wacc']:.1%}"],
        ["Terminal growth", f"{dcf['terminal_growth']:.1%}"],
        ["Enterprise value (USD m)", f"{dcf['enterprise_value']:,.0f}"],
        ["Equity value (USD m)", f"{dcf['equity_value']:,.0f}"],
        ["Implied price (USD)", f"{dcf['value_per_share']:.2f}"],
    ]
    dcf_table = Table(dcf_rows, colWidths=[2.8 * inch, 2.2 * inch])
    dcf_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ]
        )
    )

    if scenarios:
        scen_rows = [["Scenario", "Implied HKD", "WACC", "Terminal g"]]
        for s in scenarios:
            scen_rows.append(
                [
                    s["scenario"].title(),
                    f"{float(s['implied_price_hkd']):.0f}",
                    f"{float(s['wacc']):.1%}",
                    f"{float(s['terminal_growth']):.1%}",
                ]
            )
        scen_table = Table(scen_rows, colWidths=[1.4 * inch, 1.4 * inch, 1.2 * inch, 1.2 * inch])
        scen_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d5a87")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
                ]
            )
        )
        inner = Table([[dcf_table, Spacer(0.3 * inch, 1), scen_table]], colWidths=[5.2 * inch, 0.3 * inch, 5.4 * inch])
        story.append(inner)
    else:
        story.append(dcf_table)

    chart_path = FIG_DIR / "dcf_scenarios.png"
    if chart_path.exists():
        story.append(Spacer(1, 0.15 * inch))
        img = Image(str(chart_path), width=7.5 * inch, height=3.2 * inch)
        story.append(img)

    story.append(Spacer(1, 0.1 * inch))
    foot = ParagraphStyle("Foot", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(
        Paragraph(
            "Triangulation: DCF (primary) · trading comps · illustrative transaction multiples. "
            "Not investment advice. Model: github.com/coolwg-dev → financial modelling repo.",
            foot,
        )
    )
    doc.build(story)
    return out


def main() -> int:
    _ensure_model_outputs()
    _, _, published = _load_published_context()
    prior_epoch = _apply_source_date_epoch(published)
    try:
        memo = build_memo_pdf()
        slide = build_valuation_slide_pdf()
    finally:
        if prior_epoch is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = prior_epoch
    print(f"Wrote {memo}")
    print(f"Wrote {slide}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
