"""PDF report generator for tolerance analysis results.

Uses ReportLab Platypus for professional layout with tables and paragraphs.
Generates engineering-quality PDF reports suitable for design documentation.

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8
"""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from tolerance_analysis.boundary.standards import StandardMode, StandardsManager
from tolerance_analysis.boundary.unit_converter import UnitConverter, UnitSystem
from tolerance_analysis.engine.models import (
    AnalysisResults,
    Project,
    ToleranceChain,
)


class PDFReportGenerator:
    """Generates professional PDF reports using ReportLab.

    Design decisions:
    - Uses ReportLab Platypus for high-level layout (tables, paragraphs)
    - Supports up to 50 contributors in the data table
    - Header includes project name, date, standard mode, unit system
    - Standard-specific symbols and terminology applied based on active mode
    """

    def __init__(self) -> None:
        self._standards = StandardsManager()
        self._unit_converter = UnitConverter()

    def generate(
        self,
        project: Project,
        chain: ToleranceChain,
        results: AnalysisResults,
        filepath: str,
        standard_mode: StandardMode,
        unit_system: UnitSystem,
    ) -> None:
        """Generate complete PDF report.

        Args:
            project: The project containing metadata.
            chain: The tolerance chain to report on.
            results: Computed analysis results (must have at least worst_case or rss).
            filepath: Output PDF file path.
            standard_mode: Active GD&T standard mode for symbols/terminology.
            unit_system: Active unit system for value formatting.

        Raises:
            ValueError: If no analysis results are available.
        """
        if results.worst_case is None and results.rss is None and results.monte_carlo is None:
            raise ValueError(
                "Cannot generate report: no analysis results available. "
                "Run at least one analysis before exporting."
            )

        doc = SimpleDocTemplate(
            filepath,
            pagesize=LETTER,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        elements: list = []

        # Build report sections
        elements.extend(self._build_header(project, standard_mode, unit_system, styles))
        elements.append(Spacer(1, 0.2 * inch))
        elements.extend(self._build_chain_info(chain, styles))
        elements.append(Spacer(1, 0.2 * inch))
        elements.extend(self._build_contributor_table(chain, unit_system, standard_mode, styles))
        elements.append(Spacer(1, 0.2 * inch))

        if results.worst_case is not None:
            elements.extend(self._build_worst_case_section(results, unit_system, standard_mode, styles))
            elements.append(Spacer(1, 0.2 * inch))

        if results.rss is not None:
            elements.extend(self._build_rss_section(results, unit_system, standard_mode, styles))
            elements.append(Spacer(1, 0.2 * inch))

        if results.monte_carlo is not None:
            elements.extend(self._build_monte_carlo_section(results, unit_system, standard_mode, styles))
            elements.append(Spacer(1, 0.2 * inch))

        elements.extend(self._build_notes_section(standard_mode, styles))

        doc.build(elements)

    def _format_value(self, value: float, unit_system: UnitSystem) -> str:
        """Format a numeric value with appropriate precision for the unit system."""
        return self._unit_converter.format_value(value, unit_system)

    def _get_tolerance_label(self, standard_mode: StandardMode) -> str:
        """Get the tolerance label based on standard mode."""
        symbols = self._standards.get_symbols(standard_mode)
        return symbols.get("tolerance_label", "Tolerance")

    def _get_unit_label(self, unit_system: UnitSystem) -> str:
        """Get display label for the unit system."""
        if unit_system == UnitSystem.INCH:
            return "Inches"
        return "Millimeters"

    def _build_header(
        self,
        project: Project,
        standard_mode: StandardMode,
        unit_system: UnitSystem,
        styles,
    ) -> list:
        """Build the report header section."""
        elements = []

        # Title style
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=6,
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=4,
        )

        elements.append(Paragraph("Tolerance Analysis Report", title_style))
        elements.append(Paragraph(f"Project: {project.name}", styles["Heading2"]))

        # Header info table
        report_label = self._standards.get_report_label(standard_mode)
        standard_display = report_label if report_label else "Generic (No Standard)"
        generation_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        header_data = [
            ["Generation Date:", generation_date],
            ["Standard Mode:", standard_display],
            ["Unit System:", self._get_unit_label(unit_system)],
        ]

        header_table = Table(header_data, colWidths=[1.5 * inch, 4 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(header_table)

        return elements

    def _build_chain_info(self, chain: ToleranceChain, styles) -> list:
        """Build the tolerance chain information section."""
        elements = []

        elements.append(Paragraph("Tolerance Chain", styles["Heading2"]))

        info_data = [
            ["Chain Name:", chain.name],
            ["Description:", chain.description if chain.description else "—"],
            ["Contributors:", str(len(chain.contributors))],
        ]

        info_table = Table(info_data, colWidths=[1.5 * inch, 5 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(info_table)

        return elements

    def _build_contributor_table(
        self,
        chain: ToleranceChain,
        unit_system: UnitSystem,
        standard_mode: StandardMode,
        styles,
    ) -> list:
        """Build the contributor data table (up to 50 contributors)."""
        elements = []

        symbols = self._standards.get_symbols(standard_mode)
        bilateral_symbol = symbols.get("bilateral", "±")

        elements.append(Paragraph("Contributor Data", styles["Heading2"]))

        # Table header
        header_row = ["#", "Name", "Nominal", "Upper Tol", "Lower Tol", "Direction", "Type"]

        table_data = [header_row]

        # Limit to 50 contributors per requirement
        contributors = chain.contributors[:50]

        for i, contributor in enumerate(contributors, 1):
            direction_label = "+" if contributor.direction.value == 1 else "−"
            type_label = contributor.tolerance_type.value.capitalize()

            table_data.append(
                [
                    str(i),
                    contributor.name,
                    self._format_value(contributor.nominal, unit_system),
                    f"{bilateral_symbol}{self._format_value(contributor.upper_tolerance, unit_system)}",
                    f"{bilateral_symbol}{self._format_value(contributor.lower_tolerance, unit_system)}",
                    direction_label,
                    type_label,
                ]
            )

        col_widths = [0.3 * inch, 1.8 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 0.7 * inch, 0.9 * inch]
        contrib_table = Table(table_data, colWidths=col_widths)
        contrib_table.setStyle(
            TableStyle(
                [
                    # Header row styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    # Data row styling
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("ALIGN", (0, 1), (0, -1), "CENTER"),  # # column
                    ("ALIGN", (2, 1), (4, -1), "RIGHT"),  # Numeric columns
                    ("ALIGN", (5, 1), (5, -1), "CENTER"),  # Direction
                    ("ALIGN", (6, 1), (6, -1), "CENTER"),  # Type
                    # Grid
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    # Alternating row colors
                    *[
                        ("BACKGROUND", (0, row), (-1, row), colors.HexColor("#f8f9fa"))
                        for row in range(2, len(table_data), 2)
                    ],
                ]
            )
        )
        elements.append(contrib_table)

        if len(chain.contributors) > 50:
            elements.append(Spacer(1, 0.1 * inch))
            note_style = ParagraphStyle(
                "TruncationNote",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.gray,
                italic=True,
            )
            elements.append(
                Paragraph(
                    f"Note: Showing first 50 of {len(chain.contributors)} contributors.",
                    note_style,
                )
            )

        return elements

    def _build_worst_case_section(
        self,
        results: AnalysisResults,
        unit_system: UnitSystem,
        standard_mode: StandardMode,
        styles,
    ) -> list:
        """Build the worst-case results section."""
        elements = []

        wc = results.worst_case
        if wc is None:
            return elements

        # Section heading with method label
        if standard_mode == StandardMode.ASME:
            method_label = "Worst-Case Analysis (ASME Y14.5)"
        elif standard_mode == StandardMode.ISO:
            method_label = "Worst-Case Analysis (ISO GPS)"
        else:
            method_label = "Worst-Case Analysis"

        elements.append(Paragraph(method_label, styles["Heading2"]))

        results_data = [
            ["Parameter", "Value"],
            ["Nominal", self._format_value(wc.nominal, unit_system)],
            ["Total Tolerance", self._format_value(wc.total_tolerance, unit_system)],
            ["Maximum", self._format_value(wc.maximum, unit_system)],
            ["Minimum", self._format_value(wc.minimum, unit_system)],
            ["Tolerance Band", self._format_value(wc.tolerance_band, unit_system)],
        ]

        results_table = Table(results_data, colWidths=[2.5 * inch, 2.0 * inch])
        results_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(results_table)

        return elements

    def _build_rss_section(
        self,
        results: AnalysisResults,
        unit_system: UnitSystem,
        standard_mode: StandardMode,
        styles,
    ) -> list:
        """Build the RSS results section with worst-case comparison."""
        elements = []

        rss = results.rss
        if rss is None:
            return elements

        # Section heading with method label
        if standard_mode == StandardMode.ASME:
            method_label = "RSS Statistical Analysis (ASME Y14.5)"
        elif standard_mode == StandardMode.ISO:
            method_label = "RSS Statistical Analysis (ISO GPS)"
        else:
            method_label = "RSS Statistical Analysis"

        elements.append(Paragraph(method_label, styles["Heading2"]))

        # Combined table showing RSS and Worst-Case side by side
        results_data = [
            ["Parameter", "RSS (Statistical)", "Worst-Case"],
            [
                "Nominal",
                self._format_value(rss.nominal, unit_system),
                self._format_value(rss.worst_case.nominal, unit_system),
            ],
            [
                "Tolerance",
                self._format_value(rss.statistical_tolerance, unit_system),
                self._format_value(rss.worst_case.total_tolerance, unit_system),
            ],
            [
                "Maximum",
                self._format_value(rss.statistical_maximum, unit_system),
                self._format_value(rss.worst_case.maximum, unit_system),
            ],
            [
                "Minimum",
                self._format_value(rss.statistical_minimum, unit_system),
                self._format_value(rss.worst_case.minimum, unit_system),
            ],
            [
                "Band",
                self._format_value(rss.statistical_band, unit_system),
                self._format_value(rss.worst_case.tolerance_band, unit_system),
            ],
        ]

        results_table = Table(results_data, colWidths=[2.0 * inch, 2.0 * inch, 2.0 * inch])
        results_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(results_table)

        return elements

    def _build_monte_carlo_section(
        self,
        results: AnalysisResults,
        unit_system: UnitSystem,
        standard_mode: StandardMode,
        styles,
    ) -> list:
        """Build the Monte Carlo results section."""
        elements = []

        mc = results.monte_carlo
        if mc is None:
            return elements

        # Section heading with method label
        if standard_mode == StandardMode.ASME:
            method_label = "Monte Carlo Simulation (ASME Y14.5)"
        elif standard_mode == StandardMode.ISO:
            method_label = "Monte Carlo Simulation (ISO GPS)"
        else:
            method_label = "Monte Carlo Simulation"

        elements.append(Paragraph(method_label, styles["Heading2"]))

        # Simulation info
        info_style = ParagraphStyle(
            "MCInfo",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=8,
        )
        elements.append(
            Paragraph(
                f"Iterations: {mc.num_iterations:,}",
                info_style,
            )
        )

        # Statistics table
        stats_data = [
            ["Statistic", "Value"],
            ["Mean", self._format_value(mc.mean, unit_system)],
            ["Standard Deviation", self._format_value(mc.std_dev, unit_system)],
            ["Minimum", self._format_value(mc.minimum, unit_system)],
            ["Maximum", self._format_value(mc.maximum, unit_system)],
        ]

        # Add percentiles
        percentile_labels = {
            "0.135": "0.135% (−3σ)",
            "2.275": "2.275% (−2σ)",
            "50": "50% (Median)",
            "97.725": "97.725% (+2σ)",
            "99.865": "99.865% (+3σ)",
        }

        for key, label in percentile_labels.items():
            if key in mc.percentiles:
                stats_data.append(
                    [f"Percentile {label}", self._format_value(mc.percentiles[key], unit_system)]
                )

        stats_table = Table(stats_data, colWidths=[2.5 * inch, 2.0 * inch])
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(stats_table)

        return elements

    def _build_notes_section(self, standard_mode: StandardMode, styles) -> list:
        """Build the notes/assumptions section."""
        elements = []

        elements.append(Paragraph("Notes &amp; Assumptions", styles["Heading2"]))

        assumption_text = self._standards.get_default_assumption(standard_mode)

        note_style = ParagraphStyle(
            "NoteText",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=4,
        )

        if assumption_text:
            elements.append(Paragraph(f"• {assumption_text}", note_style))
        else:
            elements.append(
                Paragraph(
                    "• No standard-specific assumptions applied (Generic mode).",
                    note_style,
                )
            )

        elements.append(
            Paragraph(
                "• All tolerances converted to bilateral form for analysis.",
                note_style,
            )
        )
        elements.append(
            Paragraph(
                "• RSS analysis assumes independent, normally distributed manufacturing variation.",
                note_style,
            )
        )

        return elements
