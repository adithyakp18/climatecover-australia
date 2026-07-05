from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import duckdb
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "db" / "climatecover.duckdb"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "data_refresh_manifest.json"
OUTPUT_DIR = PROJECT_ROOT / "output" / "pdf"
OUTPUT_PATH = OUTPUT_DIR / "ClimateCover_Australia_Project_Summary.pdf"

BRAND_NAVY = colors.HexColor("#10243F")
BRAND_BLUE = colors.HexColor("#1F5F99")
BRAND_GREEN = colors.HexColor("#2B8A7E")
SOFT_BLUE = colors.HexColor("#EAF2F8")
SOFT_GREY = colors.HexColor("#F4F6F8")
TEXT = colors.HexColor("#172033")
MUTED = colors.HexColor("#526071")
LINE = colors.HexColor("#D8E0EA")


class HorizontalRule(Flowable):
    def __init__(self, width: float = 16.5 * cm, color=LINE, thickness: float = 1):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = 0.2 * cm

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_metrics() -> dict:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        kpis = conn.execute(
            """
            SELECT
                COUNT(*) AS total_regions,
                ROUND(AVG(property_risk_score), 2) AS avg_property_risk_score,
                ROUND(AVG(premium_to_income_percent), 2) AS avg_premium_to_income_percent,
                SUM(CASE WHEN affordability_band = 'Severe' THEN 1 ELSE 0 END)
                    AS severe_affordability_regions,
                SUM(CASE WHEN risk_band IN ('High', 'Severe') THEN 1 ELSE 0 END)
                    AS high_or_severe_risk_regions
            FROM foundation_region_risk
            """
        ).fetchone()
        top_regions = conn.execute(
            """
            SELECT
                sa2_name,
                state_name,
                ROUND(property_risk_score, 2) AS property_risk_score,
                risk_band,
                ROUND(premium_to_income_percent, 2) AS premium_to_income_percent,
                affordability_band,
                ROUND(intervention_priority_score, 2) AS intervention_priority_score
            FROM foundation_region_risk
            ORDER BY intervention_priority_score DESC NULLS LAST
            LIMIT 10
            """
        ).fetchall()
        lineage = conn.execute(
            """
            SELECT layer, field_group, source, data_status, business_use
            FROM data_lineage
            ORDER BY
                CASE data_status
                    WHEN 'Real Public Data' THEN 1
                    WHEN 'Calculated Metric' THEN 2
                    ELSE 3
                END,
                layer
            """
        ).fetchall()
    finally:
        conn.close()

    return {
        "total_regions": int(kpis[0] or 0),
        "avg_property_risk_score": float(kpis[1] or 0),
        "avg_premium_to_income_percent": float(kpis[2] or 0),
        "severe_affordability_regions": int(kpis[3] or 0),
        "high_or_severe_risk_regions": int(kpis[4] or 0),
        "top_regions": top_regions,
        "lineage": lineage,
    }


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=31,
            textColor=BRAND_NAVY,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=BRAND_NAVY,
            spaceBefore=10,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=BRAND_BLUE,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=TEXT,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=MUTED,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.5,
            leftIndent=12,
            firstLineIndent=0,
            textColor=TEXT,
        ),
        "table": ParagraphStyle(
            "TableText",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=8.8,
            textColor=TEXT,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=8.8,
            textColor=colors.white,
        ),
        "metric": ParagraphStyle(
            "Metric",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=BRAND_NAVY,
            alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullets(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style), bulletColor=BRAND_BLUE) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=14,
        bulletFontSize=6,
    )


def make_table(
    rows: list[list[str | int | float]],
    col_widths: list[float],
    style_map: dict[str, ParagraphStyle],
    repeat_rows: int = 1,
) -> Table:
    wrapped = []
    for row_index, row in enumerate(rows):
        row_style = style_map["table_header"] if row_index < repeat_rows else style_map["table"]
        wrapped.append([Paragraph(str(cell), row_style) for cell in row])

    table = Table(wrapped, colWidths=col_widths, repeatRows=repeat_rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, repeat_rows - 1), BRAND_NAVY),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, repeat_rows), (-1, -1), [colors.white, SOFT_GREY]),
            ]
        )
    )
    return table


def metric_cards(metrics: dict, style_map: dict[str, ParagraphStyle]) -> Table:
    data = [
        [
            Paragraph(f"{metrics['total_regions']:,}", style_map["metric"]),
            Paragraph(f"{metrics['avg_property_risk_score']:.2f}", style_map["metric"]),
            Paragraph(f"{metrics['avg_premium_to_income_percent']:.2f}%", style_map["metric"]),
            Paragraph(f"{metrics['severe_affordability_regions']:,}", style_map["metric"]),
            Paragraph(f"{metrics['high_or_severe_risk_regions']:,}", style_map["metric"]),
        ],
        [
            Paragraph("SA2 regions", style_map["metric_label"]),
            Paragraph("Avg property risk", style_map["metric_label"]),
            Paragraph("Avg premium to income", style_map["metric_label"]),
            Paragraph("Severe affordability", style_map["metric_label"]),
            Paragraph("High or severe risk", style_map["metric_label"]),
        ],
    ]
    table = Table(data, colWidths=[3.25 * cm] * 5, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def architecture_table(style_map: dict[str, ParagraphStyle]) -> Table:
    rows = [
        ["Layer", "What It Does", "Key Files / Tables"],
        [
            "Public data acquisition",
            "Downloads and prepares ABS SEIFA and ABS Census SA2 household data.",
            "scripts/prepare_real_abs_data.py; data/raw/",
        ],
        [
            "Foundation model",
            "Creates the regional spine, SEIFA facts and demographic facts.",
            "dim_region; fact_seifa; fact_demographics; foundation_region_profile",
        ],
        [
            "Climate and hazard layer",
            "Adds complete climate and hazard indicators for every region.",
            "fact_climate; fact_hazard; foundation_region_climate",
        ],
        [
            "Risk and affordability layer",
            "Calculates premium burden, affordability bands, risk scores and intervention priority.",
            "fact_affordability; fact_property_risk; foundation_region_risk",
        ],
        [
            "Dashboard application",
            "Presents executive KPIs, exploration tables, regional profiles, methodology and data quality.",
            "app/Home.py; app/pages/*; src/dashboard/",
        ],
        [
            "Automation",
            "Refreshes public data and updates source metadata on a schedule.",
            ".github/workflows/refresh-public-data.yml; scripts/refresh_public_data.py",
        ],
    ]
    return make_table(rows, [3.2 * cm, 6.2 * cm, 6.9 * cm], style_map)


def build_story() -> list:
    manifest = load_manifest()
    metrics = load_metrics()
    s = styles()
    story: list = []

    story.append(Spacer(1, 1.0 * cm))
    story.append(p("ClimateCover Australia", s["title"]))
    story.append(
        p(
            "Insurance Affordability and Property Risk Intelligence Platform",
            s["subtitle"],
        )
    )
    story.append(HorizontalRule())
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        p(
            "A professional project handover covering the business problem, solution design, data sources, methodology, code structure, current results and deployment path.",
            s["body"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        p(
            f"Generated: {datetime.now().strftime('%d %B %Y')} | Latest data refresh: {manifest.get('last_refresh_utc', 'not available')}",
            s["small"],
        )
    )
    story.append(PageBreak())

    story.append(p("1. Executive Summary", s["h1"]))
    story.append(
        p(
            "ClimateCover Australia is a regional risk intelligence platform that identifies where climate-related property exposure overlaps with household insurance affordability pressure. It is designed for insurers, banks, government resilience teams, regulators and consulting stakeholders who need a clear, explainable view of regional vulnerability.",
            s["body"],
        )
    )
    story.append(metric_cards(metrics, s))
    story.append(Spacer(1, 0.35 * cm))
    story.append(
        bullets(
            [
                "Uses official ABS SEIFA 2021 SA2 records for regional names, population and socio-economic indicators.",
                "Uses real ABS Census 2021 SA2 household indicators for income, mortgage repayments, rent and household count.",
                "Creates calculated affordability and property risk metrics for decision support.",
                "Includes a Streamlit dashboard with executive overview, risk explorer, region profile, methodology and data quality pages.",
                "Includes an automated refresh workflow that can rebuild public data and source metadata from GitHub Actions.",
            ],
            s["bullet"],
        )
    )

    story.append(p("2. Business Problem and Value", s["h1"]))
    story.append(
        p(
            "Australian households face increasing home insurance affordability pressure as natural hazards, rebuilding costs and income vulnerability interact. Organisations need to understand where risk is concentrated, where affordability stress is emerging and where resilience investment may have the greatest impact.",
            s["body"],
        )
    )
    story.append(
        make_table(
            [
                ["Stakeholder", "Problem They Need To Solve", "How ClimateCover Helps"],
                [
                    "Insurers",
                    "Identify regional exposure and affordability pressure without relying only on portfolio-level summaries.",
                    "Ranks regions by property risk, premium burden and intervention priority.",
                ],
                [
                    "Banks",
                    "Understand climate and insurance stress that may affect household resilience and mortgage risk.",
                    "Combines household income, mortgage pressure, risk scores and affordability bands.",
                ],
                [
                    "Government",
                    "Prioritise mitigation, resilience funding and community support.",
                    "Highlights where physical risk overlaps with household vulnerability.",
                ],
                [
                    "Consultants",
                    "Demonstrate data platform, analytics, AI-style briefing and solution design capability.",
                    "Shows a complete data-to-dashboard architecture with explainable scoring.",
                ],
            ],
            [3.0 * cm, 6.0 * cm, 7.2 * cm],
            s,
        )
    )

    story.append(PageBreak())
    story.append(p("3. What Was Built", s["h1"]))
    story.append(architecture_table(s))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        p(
            "The result is a working local analytics product. Python and Pandas prepare the data, DuckDB stores the analytical model, and Streamlit presents decision-ready pages. The same repository can be deployed to Streamlit Community Cloud.",
            s["body"],
        )
    )

    story.append(p("4. Data Sources and Lineage", s["h1"]))
    story.append(
        p(
            "The platform separates data into real public data, modelled indicators and calculated metrics. This is important because it makes the dashboard honest and explainable while still keeping the product usable end to end.",
            s["body"],
        )
    )
    lineage_rows = [["Layer", "Fields", "Source", "Status", "Business Use"]]
    lineage_rows.extend([list(row) for row in metrics["lineage"]])
    story.append(
        make_table(
            lineage_rows,
            [2.5 * cm, 3.6 * cm, 3.9 * cm, 2.6 * cm, 3.9 * cm],
            s,
        )
    )
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        p(
            "Current real public data includes ABS SEIFA 2021 and ABS Census 2021 General Community Profile SA2 household fields. Climate and hazard fields are currently modelled indicators pending prepared BOM, Geoscience Australia and state hazard extracts. Insurance premiums are modelled affordability estimates because public national SA2-level insurer quote data is not openly available.",
            s["body"],
        )
    )

    story.append(PageBreak())
    story.append(p("5. Current Results", s["h1"]))
    story.append(
        p(
            "The current database contains 2,353 Australian SA2 regions. The table below lists the highest intervention priority regions in the latest build.",
            s["body"],
        )
    )
    top_rows = [
        [
            "Region",
            "State",
            "Risk",
            "Risk Band",
            "Premium / Income",
            "Affordability",
            "Priority",
        ]
    ]
    for row in metrics["top_regions"]:
        top_rows.append(
            [
                row[0],
                row[1],
                f"{row[2]:.2f}",
                row[3],
                f"{row[4]:.2f}%",
                row[5],
                f"{row[6]:.2f}",
            ]
        )
    story.append(
        make_table(
            top_rows,
            [3.4 * cm, 2.7 * cm, 1.5 * cm, 2.0 * cm, 2.2 * cm, 2.2 * cm, 1.6 * cm],
            s,
        )
    )

    story.append(p("6. Methodology", s["h1"]))
    story.append(p("Property Risk Score", s["h2"]))
    story.append(
        make_table(
            [
                ["Component", "Weight", "Purpose"],
                ["Flood risk", "30%", "Captures flood exposure contribution."],
                ["Bushfire risk", "25%", "Captures bushfire exposure contribution."],
                ["Cyclone and storm risk", "15%", "Captures severe weather exposure."],
                ["Climate indicators", "10%", "Adds rainfall, heat and temperature pressure."],
                ["Historical hazard indicator", "10%", "Represents combined hazard signal until event history is added."],
                ["Socio-economic vulnerability", "10%", "Adds household and SEIFA vulnerability context."],
            ],
            [5.0 * cm, 2.0 * cm, 9.0 * cm],
            s,
        )
    )
    story.append(p("Affordability Methodology", s["h2"]))
    story.append(
        bullets(
            [
                "Annual household income is calculated from median weekly household income multiplied by 52.",
                "Premium-to-income percentage compares the estimated annual insurance cost with annual household income.",
                "Bands are Low under 2%, Moderate from 2% to under 4%, High from 4% to under 8.33%, and Severe at 8.33% or above.",
                "The Severe threshold approximates one month of annual household income.",
            ],
            s["bullet"],
        )
    )

    story.append(PageBreak())
    story.append(p("7. Dashboard Pages", s["h1"]))
    story.append(
        make_table(
            [
                ["Page", "Purpose", "Key Features"],
                ["Home", "Introduces the product and data status.", "Business problem, solution overview, source list, navigation."],
                ["Executive Overview", "Gives a national decision view.", "KPI cards, risk distribution, affordability distribution, top ranked regions, generated executive briefing."],
                ["Risk Explorer", "Lets users filter and compare regions.", "State, risk band and affordability filters; searchable table; CSV export."],
                ["Region Profile", "Explains a selected region.", "Demographics, SEIFA, climate, hazard scores, affordability, generated regional briefing."],
                ["Methodology", "Explains the scoring and governance model.", "Public data foundation, affordability model, risk scoring, assumptions and limitations."],
                ["Data Quality", "Shows source credibility and validation status.", "Lineage table, refresh status, null checks, duplicate checks, range checks."],
            ],
            [3.0 * cm, 5.0 * cm, 8.2 * cm],
            s,
        )
    )

    story.append(p("8. Code Structure", s["h1"]))
    story.append(
        make_table(
            [
                ["Path", "Role"],
                ["app/", "Streamlit multi-page application."],
                ["app/pages/", "Executive overview, risk explorer, region profile, methodology and data quality pages."],
                ["src/dashboard/", "Reusable dashboard queries, chart builders, formatting and generated insight text."],
                ["src/data_ingestion/", "Reusable ingestion utilities for regions, SEIFA, demographics, climate, hazard and insurance estimates."],
                ["src/transformation/", "Builds foundation, climate and risk analytical models."],
                ["src/utils/", "DuckDB helpers and validation functions."],
                ["scripts/", "Pipeline runners, ABS preparation, database build and public data refresh."],
                ["docs/", "Data sources, data dictionary, methodology, manifest and source catalog."],
                ["db/", "Local DuckDB database."],
                ["data/raw/", "Downloaded and prepared source extracts."],
                ["output/pdf/", "Generated PDF documentation."],
            ],
            [4.2 * cm, 11.8 * cm],
            s,
        )
    )

    story.append(PageBreak())
    story.append(p("9. Automation and Deployment", s["h1"]))
    story.append(
        bullets(
            [
                "Local app launch command: streamlit run app/Home.py",
                "Local refresh command: python scripts/refresh_public_data.py",
                "GitHub Actions workflow: .github/workflows/refresh-public-data.yml",
                "The refresh workflow prepares public data, rebuilds the DuckDB model for validation, updates the refresh manifest and commits changed source metadata.",
                "The app can bootstrap the database when the required decision layer is missing.",
            ],
            s["bullet"],
        )
    )
    story.append(p("10. Limitations and Next Steps", s["h1"]))
    story.append(
        bullets(
            [
                "Climate indicators should be replaced with prepared BOM SA2 climate features.",
                "Hazard indicators should be replaced with Geoscience Australia and state spatial hazard layers.",
                "Insurance premiums remain modelled affordability estimates because public national SA2-level insurer premium data is not openly available.",
                "A production implementation should add automated tests for scoring and data quality thresholds.",
                "A client-grade implementation could connect insurer portfolio, claims, property and mitigation data under appropriate governance.",
            ],
            s["bullet"],
        )
    )
    story.append(p("11. Portfolio Value", s["h1"]))
    story.append(
        p(
            "This project demonstrates business analysis, enterprise data modelling, public data ingestion, data quality governance, explainable analytics, AI-style generated summaries, dashboard product design and deployment readiness. It is positioned for Australian data, AI, analytics and consulting roles where employers want to see practical solution design rather than a classroom notebook.",
            s["body"],
        )
    )

    return story


def on_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5 * cm, 1.0 * cm, "ClimateCover Australia - Project Summary")
    canvas.drawRightString(19.5 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.45 * cm,
        title="ClimateCover Australia Project Summary",
        author="ClimateCover Australia",
    )
    story = build_story()
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
