"""Stack-up visualization canvas for the Tolerance Analysis Tool.

Renders an opposed-bar layout: positive contributors stacked on one row,
negative contributors stacked on a second row aligned to the same left edge.
The gap (or interference) between their endpoints is visually apparent.

Uses QPainter for all rendering (no matplotlib dependency).
"""

from typing import Optional

from PyQt5.QtCore import QRectF, QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QFont, QPaintEvent
from PyQt5.QtWidgets import QWidget

from tolerance_analysis.engine.models import (
    AnalysisResults,
    Direction,
    MonteCarloResult,
    ToleranceChain,
    WorstCaseResult,
)
from tolerance_analysis.gui.theme import COLORS


class VisualizationCanvas(QWidget):
    """Opposed-bar stack-up visualization.

    Layout (top to bottom):
      - Row header "Positive" + stacked blue bars (left-aligned)
      - Labels for positive contributors (collision-avoided)
      - Row header "Negative" + stacked orange bars (left-aligned)
      - Labels for negative contributors (collision-avoided)
      - Gap/interference indicator between the two row endpoints
      - Result summary text
      - Monte Carlo histogram (if available)
    """

    # Layout constants
    _MARGIN_TOP = 24
    _MARGIN_BOTTOM = 20
    _MARGIN_LEFT = 20
    _MARGIN_RIGHT = 20
    _BAR_HEIGHT = 36
    _ROW_GAP = 16          # vertical gap between positive and negative sections
    _LABEL_ROW_HEIGHT = 16
    _MAX_LABEL_ROWS = 3
    _GAP_INDICATOR_HEIGHT = 28
    _MC_HEIGHT = 50
    _RESULT_TEXT_HEIGHT = 20

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("VisualizationCanvas")
        self.setMinimumSize(400, 250)

        self._chain: Optional[ToleranceChain] = None
        self._results: Optional[AnalysisResults] = None
        self._warnings: list = []

        # Debug overrides (set by VizDebugDock when active)
        self._debug_label_font_size: Optional[int] = None
        self._debug_value_font_size: Optional[int] = None
        self._debug_label_y_offset: Optional[int] = None
        self._debug_value_y_offset: Optional[int] = None
        self._debug_label_max_width: Optional[int] = None
        self._debug_label_mode: Optional[str] = None
        self._debug_stagger_threshold: Optional[int] = None
        self._debug_show_values: Optional[bool] = None
        self._debug_tol_opacity: Optional[int] = None
        self._debug_min_bar_width: Optional[int] = None
        self._debug_result_font_size: Optional[int] = None
        self._debug_gap: Optional[int] = None

    def sizeHint(self) -> QSize:
        return QSize(800, 400)

    def set_chain(
        self, chain: ToleranceChain, results: Optional[AnalysisResults] = None
    ) -> None:
        self._chain = chain
        self._results = results
        # Evaluate warnings
        from tolerance_analysis.engine.warnings import evaluate_warnings
        self._warnings = evaluate_warnings(chain, results) if chain else []
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_color = QColor(COLORS["canvas_bg"])
        painter.fillRect(self.rect(), bg_color)

        if self._chain is None or not self._chain.contributors:
            self._draw_placeholder(painter)
            painter.end()
            return

        self._draw_opposed_bars(painter)
        painter.end()

    def _draw_placeholder(self, painter: QPainter) -> None:
        text_color = QColor(COLORS["text_on_dark"])
        painter.setPen(QPen(text_color))
        font = QFont("Inter", 14)
        font.setStyleHint(QFont.SansSerif)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "No contributors added")

    def _draw_opposed_bars(self, painter: QPainter) -> None:
        """Main drawing routine: opposed positive/negative bar layout."""
        contributors = self._chain.contributors
        tol_opacity = self._debug_tol_opacity if self._debug_tol_opacity is not None else 77
        label_font_size = self._debug_label_font_size if self._debug_label_font_size is not None else 8
        value_font_size = self._debug_value_font_size if self._debug_value_font_size is not None else 8

        # Split contributors by direction
        pos_contribs = [c for c in contributors if c.direction == Direction.POSITIVE]
        neg_contribs = [c for c in contributors if c.direction == Direction.NEGATIVE]

        # Compute totals
        pos_total = sum(abs(c.nominal) for c in pos_contribs)
        neg_total = sum(abs(c.nominal) for c in neg_contribs)
        max_total = max(pos_total, neg_total, 0.001)

        # Scale: map max_total to full canvas width
        canvas_width = self.width() - self._MARGIN_LEFT - self._MARGIN_RIGHT
        scale = canvas_width / max_total

        # Fonts
        value_font = QFont("JetBrains Mono", value_font_size)
        value_font.setStyleHint(QFont.Monospace)
        label_font = QFont("Inter", label_font_size)
        label_font.setStyleHint(QFont.SansSerif)
        header_font = QFont("Inter", 9)
        header_font.setStyleHint(QFont.SansSerif)
        header_font.setBold(True)

        text_color = QColor(COLORS["text_on_dark"])
        dim_text = QColor(COLORS["text_on_dark"])
        dim_text.setAlpha(160)

        y_cursor = self._MARGIN_TOP

        # --- Positive row ---
        pos_color = QColor(COLORS["positive"])
        y_cursor = self._draw_bar_row(
            painter, pos_contribs, pos_color, "Positive Stack",
            y_cursor, scale, tol_opacity, value_font, label_font,
            header_font, text_color, dim_text
        )

        y_cursor += self._ROW_GAP

        # --- Negative row ---
        neg_color = QColor(COLORS["negative"])
        y_cursor = self._draw_bar_row(
            painter, neg_contribs, neg_color, "Negative Stack",
            y_cursor, scale, tol_opacity, value_font, label_font,
            header_font, text_color, dim_text
        )

        y_cursor += self._ROW_GAP

        # --- Gap/Interference indicator ---
        gap_nominal = pos_total - neg_total
        pos_end_x = self._MARGIN_LEFT + pos_total * scale
        neg_end_x = self._MARGIN_LEFT + neg_total * scale

        y_cursor = self._draw_gap_indicator(
            painter, gap_nominal, pos_end_x, neg_end_x,
            y_cursor, scale, value_font, text_color
        )

        y_cursor += self._ROW_GAP

        # --- Result summary text (if analysis run) ---
        if self._results is not None and self._results.worst_case is not None:
            y_cursor = self._draw_result_summary(
                painter, y_cursor, canvas_width, text_color, value_font
            )
            y_cursor += self._ROW_GAP

        # --- Monte Carlo histogram ---
        if self._results is not None and self._results.monte_carlo is not None:
            self._draw_monte_carlo_overlay(painter, y_cursor, canvas_width)
            y_cursor += self._MC_HEIGHT + 24

        # --- Warning banners ---
        if self._warnings:
            self._draw_warning_banners(painter, y_cursor, canvas_width)

    def _draw_bar_row(
        self, painter: QPainter, contribs: list, bar_color: QColor,
        header_text: str, y_start: float, scale: float, tol_opacity: int,
        value_font: QFont, label_font: QFont, header_font: QFont,
        text_color: QColor, dim_text: QColor
    ) -> float:
        """Draw one row of stacked bars (positive or negative) with labels.

        Returns the y position after this row's labels.
        """
        if not contribs:
            # Draw header and empty message
            painter.setFont(header_font)
            painter.setPen(QPen(dim_text))
            painter.drawText(
                QRectF(self._MARGIN_LEFT, y_start, 200, 16),
                Qt.AlignLeft | Qt.AlignVCenter, f"{header_text}: (none)"
            )
            return y_start + 20

        # Draw header label
        painter.setFont(header_font)
        painter.setPen(QPen(dim_text))
        row_total = sum(abs(c.nominal) for c in contribs)
        header_label = f"{header_text}: {row_total:.4f}\""
        painter.drawText(
            QRectF(self._MARGIN_LEFT, y_start, 400, 14),
            Qt.AlignLeft | Qt.AlignVCenter, header_label
        )
        y_start += 16

        # Draw bars
        y_bar = y_start
        x_offset = self._MARGIN_LEFT
        bar_segments = []  # (x_start, bar_width, x_center, contributor)

        for contrib in contribs:
            bar_width = abs(contrib.nominal) * scale
            bar_width = max(bar_width, 3)  # minimum visible

            # Solid bar
            bar_rect = QRectF(x_offset, y_bar, bar_width, self._BAR_HEIGHT)
            painter.fillRect(bar_rect, bar_color)

            # Tolerance band overlay
            tol_color = QColor(bar_color)
            tol_color.setAlpha(tol_opacity)
            tol_range = contrib.upper_tolerance + contrib.lower_tolerance
            tol_px = tol_range * scale
            if tol_px > 0:
                tol_rect = QRectF(
                    x_offset + bar_width - tol_px / 2,
                    y_bar, tol_px, self._BAR_HEIGHT
                )
                painter.fillRect(tol_rect, tol_color)

            # Draw segment border for clarity
            border_pen = QPen(QColor(bar_color).darker(140), 1)
            painter.setPen(border_pen)
            painter.drawRect(bar_rect)

            bar_segments.append((x_offset, bar_width, x_offset + bar_width / 2, contrib))
            x_offset += bar_width

        # Draw values inside or above bars
        painter.setFont(value_font)
        metrics = painter.fontMetrics()
        above_values = []

        for (seg_x, seg_w, seg_cx, contrib) in bar_segments:
            value_text = f"{abs(contrib.nominal):.4f}"
            tw = metrics.horizontalAdvance(value_text)
            th = metrics.height()

            if seg_w >= tw + 8:
                # Draw inside bar, dark text
                painter.setPen(QPen(QColor("#1a1a2e")))
                vr = QRectF(seg_x, y_bar, seg_w, self._BAR_HEIGHT)
                painter.drawText(vr, Qt.AlignCenter, value_text)
            else:
                above_values.append((seg_cx, value_text, tw, th))

        # Draw above-bar values with collision avoidance
        if above_values:
            painter.setPen(QPen(text_color))
            max_vrows = 2
            v_occupancy: list[list[tuple[float, float]]] = [[] for _ in range(max_vrows)]
            row_h = above_values[0][3] + 2

            for cx, vtext, tw, th in above_values:
                vx = max(self._MARGIN_LEFT, min(cx - tw / 2, self.width() - self._MARGIN_RIGHT - tw))
                vx_end = vx + tw + 4

                placed = 0
                for ri in range(max_vrows):
                    if all(not (vx < oe and vx_end > os) for os, oe in v_occupancy[ri]):
                        placed = ri
                        break
                else:
                    placed = max_vrows - 1

                v_occupancy[placed].append((vx, vx_end))
                vy = y_bar - 3 - placed * row_h
                painter.drawText(QRectF(vx, vy - th, tw + 2, th), Qt.AlignCenter, vtext)

        # Draw labels below bars with collision avoidance
        painter.setFont(label_font)
        metrics = painter.fontMetrics()
        label_zone_top = y_bar + self._BAR_HEIGHT + 4
        row_h = metrics.height() + 2
        l_occupancy: list[list[tuple[float, float]]] = [[] for _ in range(self._MAX_LABEL_ROWS)]
        leader_color = QColor(COLORS["text_on_dark"])
        leader_color.setAlpha(80)

        for (seg_x, seg_w, seg_cx, contrib) in bar_segments:
            label_text = contrib.name
            tw = metrics.horizontalAdvance(label_text)
            ideal_x = seg_cx - tw / 2
            lx = max(self._MARGIN_LEFT, min(ideal_x, self.width() - self._MARGIN_RIGHT - tw))
            lx_end = lx + tw + 6

            placed = 0
            for ri in range(self._MAX_LABEL_ROWS):
                if all(not (lx < oe and lx_end > os) for os, oe in l_occupancy[ri]):
                    placed = ri
                    break
            else:
                placed = self._MAX_LABEL_ROWS - 1

            l_occupancy[placed].append((lx, lx_end))
            ly = label_zone_top + placed * row_h

            # Leader line
            if placed > 0:
                painter.setPen(QPen(leader_color, 1, Qt.DotLine))
                painter.drawLine(int(seg_cx), int(y_bar + self._BAR_HEIGHT), int(seg_cx), int(ly))

            # Label text
            painter.setPen(QPen(text_color))
            painter.setFont(label_font)
            painter.drawText(QRectF(lx, ly, tw + 2, row_h), Qt.AlignLeft | Qt.AlignVCenter, label_text)

        return label_zone_top + self._MAX_LABEL_ROWS * row_h

    def _draw_gap_indicator(
        self, painter: QPainter, gap_nominal: float,
        pos_end_x: float, neg_end_x: float,
        y_start: float, scale: float,
        value_font: QFont, text_color: QColor
    ) -> float:
        """Draw the gap/interference indicator between the two bar endpoints."""
        # Determine gap bounds
        left_x = min(pos_end_x, neg_end_x)
        right_x = max(pos_end_x, neg_end_x)
        gap_width = right_x - left_x

        y_gap = y_start

        if abs(gap_nominal) < 1e-8:
            # Zero gap — just a line
            painter.setPen(QPen(QColor(COLORS["text_on_dark"]), 2))
            painter.drawLine(int(pos_end_x), int(y_gap), int(pos_end_x), int(y_gap + self._GAP_INDICATOR_HEIGHT))
            label = "Gap: 0.0000\" (perfect fit)"
            label_color = QColor(COLORS["in_spec"])
        elif gap_nominal > 0:
            # Positive gap = clearance (green)
            gap_color = QColor(COLORS["in_spec"])
            gap_color.setAlpha(120)
            gap_rect = QRectF(left_x, y_gap, gap_width, self._GAP_INDICATOR_HEIGHT)
            painter.fillRect(gap_rect, gap_color)
            # Border
            painter.setPen(QPen(QColor(COLORS["in_spec"]), 2))
            painter.drawRect(gap_rect)
            label = f"Gap: +{gap_nominal:.4f}\" (clearance)"
            label_color = QColor(COLORS["in_spec"])
        else:
            # Negative gap = interference (red)
            gap_color = QColor(COLORS["out_spec"])
            gap_color.setAlpha(120)
            gap_rect = QRectF(left_x, y_gap, gap_width, self._GAP_INDICATOR_HEIGHT)
            painter.fillRect(gap_rect, gap_color)
            painter.setPen(QPen(QColor(COLORS["out_spec"]), 2))
            painter.drawRect(gap_rect)
            label = f"Gap: {gap_nominal:.4f}\" (interference)"
            label_color = QColor(COLORS["out_spec"])

        # Draw vertical alignment lines from bars to gap
        align_pen = QPen(QColor(COLORS["text_on_dark"]), 1, Qt.DashLine)
        align_pen.setColor(QColor(COLORS["text_on_dark"]))
        painter.setPen(align_pen)
        # Positive endpoint line
        painter.drawLine(int(pos_end_x), int(y_gap - 4), int(pos_end_x), int(y_gap + self._GAP_INDICATOR_HEIGHT + 4))
        # Negative endpoint line
        painter.drawLine(int(neg_end_x), int(y_gap - 4), int(neg_end_x), int(y_gap + self._GAP_INDICATOR_HEIGHT + 4))

        # Gap label text
        painter.setFont(value_font)
        painter.setPen(QPen(label_color))
        label_rect = QRectF(
            self._MARGIN_LEFT, y_gap + self._GAP_INDICATOR_HEIGHT + 4,
            self.width() - self._MARGIN_LEFT - self._MARGIN_RIGHT,
            self._RESULT_TEXT_HEIGHT
        )
        painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, label)

        return y_gap + self._GAP_INDICATOR_HEIGHT + self._RESULT_TEXT_HEIGHT + 8

    def _draw_result_summary(
        self, painter: QPainter, y_start: float,
        canvas_width: float, text_color: QColor, value_font: QFont
    ) -> float:
        """Draw worst-case/RSS result summary text."""
        wc = self._results.worst_case
        rss = self._results.rss

        painter.setFont(value_font)
        painter.setPen(QPen(text_color))

        lines = []
        if wc is not None:
            lines.append(
                f"Worst-Case:  Nom {wc.nominal:.4f}\"  "
                f"Tol ±{wc.total_tolerance:.4f}\"  "
                f"Range [{wc.minimum:.4f}\", {wc.maximum:.4f}\"]"
            )
        if rss is not None:
            lines.append(
                f"RSS (3σ):    Nom {rss.nominal:.4f}\"  "
                f"Tol ±{rss.statistical_tolerance:.4f}\"  "
                f"Range [{rss.statistical_minimum:.4f}\", {rss.statistical_maximum:.4f}\"]"
            )

        y = y_start
        for line in lines:
            rect = QRectF(self._MARGIN_LEFT, y, canvas_width, self._RESULT_TEXT_HEIGHT)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, line)
            y += self._RESULT_TEXT_HEIGHT + 2

        return y

    def _draw_monte_carlo_overlay(
        self, painter: QPainter, y_start: float, canvas_width: float
    ) -> None:
        """Render Monte Carlo histogram at the given y position."""
        mc: MonteCarloResult = self._results.monte_carlo
        if not mc.bin_counts or not mc.bin_edges:
            return

        y_mc = y_start

        max_count = max(mc.bin_counts) if mc.bin_counts else 1
        if max_count == 0:
            max_count = 1

        mc_color = QColor(COLORS["monte_carlo"])
        mc_color.setAlpha(153)

        num_bins = len(mc.bin_counts)
        bin_pixel_width = canvas_width / num_bins

        for i, count in enumerate(mc.bin_counts):
            bar_height = (count / max_count) * self._MC_HEIGHT
            x = self._MARGIN_LEFT + i * bin_pixel_width
            y = y_mc + self._MC_HEIGHT - bar_height
            painter.fillRect(QRectF(x, y, bin_pixel_width, bar_height), mc_color)

        # Label
        text_color = QColor(COLORS["text_on_dark"])
        painter.setPen(QPen(text_color))
        label_font = QFont("Inter", 9)
        label_font.setStyleHint(QFont.SansSerif)
        painter.setFont(label_font)

        mc_label = (
            f"Monte Carlo ({mc.num_iterations:,} iter)  "
            f"μ={mc.mean:.4f}\"  σ={mc.std_dev:.4f}\"  "
            f"[{mc.minimum:.4f}\", {mc.maximum:.4f}\"]"
        )
        label_rect = QRectF(
            self._MARGIN_LEFT, y_mc + self._MC_HEIGHT + 4,
            canvas_width, 16
        )
        painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, mc_label)

    def _draw_warning_banners(
        self, painter: QPainter, y_start: float, canvas_width: float
    ) -> None:
        """Draw warning banners below the analysis results."""
        from tolerance_analysis.engine.warnings import WarningSeverity

        banner_font = QFont("Inter", 8)
        banner_font.setStyleHint(QFont.SansSerif)
        painter.setFont(banner_font)
        metrics = painter.fontMetrics()
        banner_height = metrics.height() + 8

        y = y_start

        for warning in self._warnings[:4]:  # Show max 4 warnings on canvas
            # Color by severity
            if warning.severity == WarningSeverity.CRITICAL:
                bg = QColor(COLORS["out_spec"])
                bg.setAlpha(50)
                border = QColor(COLORS["out_spec"])
                icon = "\u274c"
            elif warning.severity == WarningSeverity.CAUTION:
                bg = QColor(COLORS["negative"])
                bg.setAlpha(40)
                border = QColor(COLORS["negative"])
                icon = "\u26a0"
            else:
                bg = QColor(COLORS["positive"])
                bg.setAlpha(30)
                border = QColor(COLORS["positive"])
                icon = "\u2139"

            banner_rect = QRectF(self._MARGIN_LEFT, y, canvas_width, banner_height)
            painter.fillRect(banner_rect, bg)
            painter.setPen(QPen(border, 1))
            painter.drawRect(banner_rect)

            # Text
            text_color = QColor(COLORS["text_on_dark"])
            painter.setPen(QPen(text_color))
            text_rect = QRectF(self._MARGIN_LEFT + 4, y, canvas_width - 8, banner_height)
            painter.drawText(
                text_rect, Qt.AlignLeft | Qt.AlignVCenter,
                f"{icon} {warning.title}: {warning.message}"
            )

            y += banner_height + 3
