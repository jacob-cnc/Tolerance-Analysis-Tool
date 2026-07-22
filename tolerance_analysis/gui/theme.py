"""
Application theme module for the Tolerance Analysis Tool.

Defines colors, fonts, and Qt stylesheet for consistent application styling.
"""

# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------

COLORS = {
    # Canvas
    "canvas_bg": "#1a1a2e",          # Dark workspace (L ~11%)

    # UI Shell
    "ui_bg": "#f0f0f5",              # Light shell (L ~95%)
    "ui_surface": "#e8e8ed",         # Card surfaces (L ~91%)
    "ui_border": "#c8c8d0",          # Borders

    # Semantic colors
    "positive": "#4fc3f7",           # Blue/cyan - positive direction
    "negative": "#ffb74d",           # Orange/amber - negative direction
    "in_spec": "#66bb6a",            # Green - within tolerance
    "out_spec": "#ef5350",           # Red - outside tolerance
    "monte_carlo": "#ab47bc",        # Purple - MC overlay

    # Text
    "text_primary": "#212121",
    "text_secondary": "#616161",
    "text_on_dark": "#e0e0e0",
}

# ---------------------------------------------------------------------------
# Font Families
# ---------------------------------------------------------------------------

FONTS = {
    "ui": "Inter",
    "mono": "JetBrains Mono",
    "fallback_ui": "Segoe UI, Helvetica, Arial, sans-serif",
    "fallback_mono": "Consolas, Courier New, monospace",
}

# ---------------------------------------------------------------------------
# Derived helpers for stylesheet construction
# ---------------------------------------------------------------------------

_UI_FONT = f'"{FONTS["ui"]}", {FONTS["fallback_ui"]}'
_MONO_FONT = f'"{FONTS["mono"]}", {FONTS["fallback_mono"]}'

# ---------------------------------------------------------------------------
# Qt Stylesheet
# ---------------------------------------------------------------------------

STYLESHEET = f"""
/* ===== Global defaults ===== */
QMainWindow, QWidget {{
    background-color: {COLORS["ui_bg"]};
    color: {COLORS["text_primary"]};
    font-family: {_UI_FONT};
    font-size: 11pt;
}}

/* ===== Dark canvas for visualization ===== */
QWidget#VisualizationCanvas {{
    background-color: {COLORS["canvas_bg"]};
    color: {COLORS["text_on_dark"]};
}}

/* ===== QGroupBox ===== */
QGroupBox {{
    background-color: {COLORS["ui_surface"]};
    border: 1px solid {COLORS["ui_border"]};
    border-radius: 4px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: {COLORS["text_primary"]};
}}

/* ===== QPushButton ===== */
QPushButton {{
    background-color: {COLORS["ui_surface"]};
    border: 1px solid {COLORS["ui_border"]};
    border-radius: 4px;
    padding: 6px 16px;
    font-family: {_UI_FONT};
    font-size: 10pt;
    color: {COLORS["text_primary"]};
}}

QPushButton:hover {{
    background-color: {COLORS["ui_border"]};
    border-color: {COLORS["text_secondary"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["text_secondary"]};
    color: {COLORS["ui_bg"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["ui_bg"]};
    color: {COLORS["ui_border"]};
    border-color: {COLORS["ui_border"]};
}}

/* ===== QTableWidget ===== */
QTableWidget {{
    background-color: {COLORS["ui_bg"]};
    alternate-background-color: {COLORS["ui_surface"]};
    border: 1px solid {COLORS["ui_border"]};
    gridline-color: {COLORS["ui_border"]};
    font-family: {_MONO_FONT};
    font-size: 10pt;
    color: {COLORS["text_primary"]};
}}

QTableWidget::item {{
    padding: 4px 6px;
}}

QTableWidget::item:selected {{
    background-color: {COLORS["positive"]};
    color: {COLORS["canvas_bg"]};
}}

QHeaderView::section {{
    background-color: {COLORS["ui_surface"]};
    border: 1px solid {COLORS["ui_border"]};
    padding: 4px 8px;
    font-family: {_UI_FONT};
    font-weight: 600;
    font-size: 10pt;
    color: {COLORS["text_primary"]};
}}

/* ===== QComboBox ===== */
QComboBox {{
    background-color: {COLORS["ui_surface"]};
    border: 1px solid {COLORS["ui_border"]};
    border-radius: 4px;
    padding: 4px 8px;
    font-family: {_UI_FONT};
    font-size: 10pt;
    color: {COLORS["text_primary"]};
    min-width: 80px;
}}

QComboBox:hover {{
    border-color: {COLORS["text_secondary"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["ui_bg"]};
    border: 1px solid {COLORS["ui_border"]};
    selection-background-color: {COLORS["positive"]};
    selection-color: {COLORS["canvas_bg"]};
}}

/* ===== QLineEdit / QSpinBox ===== */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS["ui_bg"]};
    border: 1px solid {COLORS["ui_border"]};
    border-radius: 3px;
    padding: 4px 6px;
    font-family: {_MONO_FONT};
    font-size: 10pt;
    color: {COLORS["text_primary"]};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS["positive"]};
}}

/* ===== QLabel ===== */
QLabel {{
    color: {COLORS["text_primary"]};
}}

/* ===== QTabWidget ===== */
QTabWidget::pane {{
    border: 1px solid {COLORS["ui_border"]};
    background-color: {COLORS["ui_bg"]};
}}

QTabBar::tab {{
    background-color: {COLORS["ui_surface"]};
    border: 1px solid {COLORS["ui_border"]};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 14px;
    font-family: {_UI_FONT};
    font-size: 10pt;
    color: {COLORS["text_secondary"]};
}}

QTabBar::tab:selected {{
    background-color: {COLORS["ui_bg"]};
    color: {COLORS["text_primary"]};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS["ui_border"]};
}}

/* ===== QScrollBar ===== */
QScrollBar:vertical {{
    background-color: {COLORS["ui_bg"]};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["ui_border"]};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["text_secondary"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLORS["ui_bg"]};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS["ui_border"]};
    border-radius: 4px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS["text_secondary"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ===== QToolTip ===== */
QToolTip {{
    background-color: {COLORS["canvas_bg"]};
    color: {COLORS["text_on_dark"]};
    border: 1px solid {COLORS["text_secondary"]};
    padding: 4px;
    font-size: 9pt;
}}
"""
