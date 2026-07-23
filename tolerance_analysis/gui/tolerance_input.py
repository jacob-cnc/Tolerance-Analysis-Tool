"""NX-style tolerance input widget.

Provides a visual format picker (similar to Siemens NX) where the user
selects how they want to express the tolerance, then fills in the
appropriate fields. The widget auto-detects the tolerance type for the
engine based on the input format.

Formats supported:
  ±X          - Bilateral symmetric
  +X / -Y    - Bilateral asymmetric (or unilateral if one is 0)
  Limits      - Upper limit / Lower limit (nominal derived)
  Fit Class   - ISO 286 code (e.g., H7, g6) with auto-lookup
"""

from typing import Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QButtonGroup,
)
from PyQt5.QtGui import QFont

from tolerance_analysis.engine.models import ToleranceType


class ToleranceFormat:
    """Enumeration of tolerance input formats."""
    BILATERAL_SYM = "bilateral_sym"     # ±X
    BILATERAL_ASYM = "bilateral_asym"   # +X / -Y
    LIMITS = "limits"                    # Upper / Lower limits
    FIT_CLASS = "fit_class"              # H7, g6, etc.


class ToleranceInputWidget(QWidget):
    """NX-style tolerance input with visual format picker.

    Emits tolerance_changed when the user modifies any value.
    The signal carries (upper_tolerance, lower_tolerance, tolerance_type)
    as determined by the current format and input values.
    """

    # Signal: (upper_tol: float, lower_tol: float, tol_type: str, nominal_override: float or None)
    # nominal_override is non-None only for Limits mode (where nominal is derived)
    tolerance_changed = pyqtSignal(float, float, str, object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._nominal: float = 1.0  # Current nominal for fit class lookup
        self._format = ToleranceFormat.BILATERAL_SYM
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # --- Format picker row (icon-style buttons) ---
        format_row = QHBoxLayout()
        format_row.setSpacing(2)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        btn_style = (
            "QToolButton { font-family: 'JetBrains Mono', monospace; font-size: 9pt; "
            "padding: 3px 6px; border: 1px solid #555; border-radius: 3px; "
            "background: #2a2a3e; color: #e0e0e0; }"
            "QToolButton:checked { background: #4fc3f7; color: #1a1a2e; border-color: #4fc3f7; }"
            "QToolButton:hover { background: #3a3a5e; }"
        )

        self._btn_sym = QToolButton()
        self._btn_sym.setText("±X")
        self._btn_sym.setToolTip("Bilateral symmetric (±)")
        self._btn_sym.setCheckable(True)
        self._btn_sym.setChecked(True)
        self._btn_sym.setStyleSheet(btn_style)
        self._btn_group.addButton(self._btn_sym, 0)
        format_row.addWidget(self._btn_sym)

        self._btn_asym = QToolButton()
        self._btn_asym.setText("+X\n−Y")
        self._btn_asym.setToolTip("Bilateral asymmetric (+X / -Y)")
        self._btn_asym.setCheckable(True)
        self._btn_asym.setStyleSheet(btn_style)
        self._btn_group.addButton(self._btn_asym, 1)
        format_row.addWidget(self._btn_asym)

        self._btn_limits = QToolButton()
        self._btn_limits.setText("Lim")
        self._btn_limits.setToolTip("Limit dimensions (Upper / Lower)")
        self._btn_limits.setCheckable(True)
        self._btn_limits.setStyleSheet(btn_style)
        self._btn_group.addButton(self._btn_limits, 2)
        format_row.addWidget(self._btn_limits)

        self._btn_fit = QToolButton()
        self._btn_fit.setText("H7")
        self._btn_fit.setToolTip("ISO 286 fit class (e.g., H7, g6)")
        self._btn_fit.setCheckable(True)
        self._btn_fit.setStyleSheet(btn_style)
        self._btn_group.addButton(self._btn_fit, 3)
        format_row.addWidget(self._btn_fit)

        format_row.addStretch()
        layout.addLayout(format_row)

        # --- Input fields (stacked, visibility toggled by format) ---
        self._fields_widget = QWidget()
        self._fields_layout = QGridLayout(self._fields_widget)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        self._fields_layout.setSpacing(3)

        field_style = (
            "QLineEdit { font-family: 'JetBrains Mono', monospace; font-size: 9pt; "
            "padding: 2px 4px; background: #2a2a3e; color: #e0e0e0; "
            "border: 1px solid #555; border-radius: 2px; }"
            "QLineEdit:focus { border-color: #4fc3f7; }"
        )
        label_style = "QLabel { color: #b0b0b0; font-size: 8pt; }"

        # Symmetric: single field
        self._lbl_sym = QLabel("±")
        self._lbl_sym.setStyleSheet(label_style)
        self._edit_sym = QLineEdit()
        self._edit_sym.setStyleSheet(field_style)
        self._edit_sym.setPlaceholderText("0.001")
        self._fields_layout.addWidget(self._lbl_sym, 0, 0)
        self._fields_layout.addWidget(self._edit_sym, 0, 1)

        # Asymmetric: two fields
        self._lbl_upper = QLabel("+")
        self._lbl_upper.setStyleSheet(label_style)
        self._edit_upper = QLineEdit()
        self._edit_upper.setStyleSheet(field_style)
        self._edit_upper.setPlaceholderText("0.002")
        self._lbl_lower = QLabel("−")
        self._lbl_lower.setStyleSheet(label_style)
        self._edit_lower = QLineEdit()
        self._edit_lower.setStyleSheet(field_style)
        self._edit_lower.setPlaceholderText("0.001")
        self._fields_layout.addWidget(self._lbl_upper, 1, 0)
        self._fields_layout.addWidget(self._edit_upper, 1, 1)
        self._fields_layout.addWidget(self._lbl_lower, 2, 0)
        self._fields_layout.addWidget(self._edit_lower, 2, 1)

        # Limits: two fields
        self._lbl_limit_upper = QLabel("Max")
        self._lbl_limit_upper.setStyleSheet(label_style)
        self._edit_limit_upper = QLineEdit()
        self._edit_limit_upper.setStyleSheet(field_style)
        self._edit_limit_upper.setPlaceholderText("1.002")
        self._lbl_limit_lower = QLabel("Min")
        self._lbl_limit_lower.setStyleSheet(label_style)
        self._edit_limit_lower = QLineEdit()
        self._edit_limit_lower.setStyleSheet(field_style)
        self._edit_limit_lower.setPlaceholderText("1.000")
        self._fields_layout.addWidget(self._lbl_limit_upper, 3, 0)
        self._fields_layout.addWidget(self._edit_limit_upper, 3, 1)
        self._fields_layout.addWidget(self._lbl_limit_lower, 4, 0)
        self._fields_layout.addWidget(self._edit_limit_lower, 4, 1)

        # Fit class: combo + result display
        self._lbl_fit = QLabel("Code")
        self._lbl_fit.setStyleSheet(label_style)
        self._edit_fit = QLineEdit()
        self._edit_fit.setStyleSheet(field_style)
        self._edit_fit.setPlaceholderText("H7")
        self._lbl_fit_result = QLabel("")
        self._lbl_fit_result.setStyleSheet("QLabel { color: #66bb6a; font-size: 8pt; }")
        self._lbl_fit_result.setWordWrap(True)
        self._fields_layout.addWidget(self._lbl_fit, 5, 0)
        self._fields_layout.addWidget(self._edit_fit, 5, 1)
        self._fields_layout.addWidget(self._lbl_fit_result, 6, 0, 1, 2)

        layout.addWidget(self._fields_widget)

        # --- Connect signals ---
        self._btn_group.buttonClicked.connect(self._on_format_changed)
        self._edit_sym.editingFinished.connect(self._emit_tolerance)
        self._edit_upper.editingFinished.connect(self._emit_tolerance)
        self._edit_lower.editingFinished.connect(self._emit_tolerance)
        self._edit_limit_upper.editingFinished.connect(self._emit_tolerance)
        self._edit_limit_lower.editingFinished.connect(self._emit_tolerance)
        self._edit_fit.editingFinished.connect(self._on_fit_changed)

        # Initial visibility
        self._update_field_visibility()

    def set_nominal(self, nominal: float) -> None:
        """Set the current nominal value (needed for fit class lookup)."""
        self._nominal = nominal

    def set_values(self, upper_tol: float, lower_tol: float, tol_type: ToleranceType) -> None:
        """Set the widget values from existing contributor data.

        Auto-selects the appropriate format based on the values.
        """
        if tol_type == ToleranceType.LIMIT:
            self._btn_limits.setChecked(True)
            self._format = ToleranceFormat.LIMITS
            self._edit_limit_upper.setText(f"{upper_tol:.4f}")
            self._edit_limit_lower.setText(f"{lower_tol:.4f}")
        elif abs(upper_tol - lower_tol) < 1e-10:
            # Symmetric bilateral
            self._btn_sym.setChecked(True)
            self._format = ToleranceFormat.BILATERAL_SYM
            self._edit_sym.setText(f"{upper_tol:.4f}")
        else:
            # Asymmetric
            self._btn_asym.setChecked(True)
            self._format = ToleranceFormat.BILATERAL_ASYM
            self._edit_upper.setText(f"{upper_tol:.4f}")
            self._edit_lower.setText(f"{lower_tol:.4f}")

        self._update_field_visibility()

    def get_values(self) -> Tuple[float, float, ToleranceType, Optional[float]]:
        """Get the current tolerance values.

        Returns:
            (upper_tol, lower_tol, tolerance_type, nominal_override)
            nominal_override is non-None only for limit dimensions.
        """
        if self._format == ToleranceFormat.BILATERAL_SYM:
            val = self._parse_float(self._edit_sym.text(), 0.0)
            return (val, val, ToleranceType.BILATERAL, None)

        elif self._format == ToleranceFormat.BILATERAL_ASYM:
            upper = self._parse_float(self._edit_upper.text(), 0.0)
            lower = self._parse_float(self._edit_lower.text(), 0.0)
            if upper == lower:
                return (upper, lower, ToleranceType.BILATERAL, None)
            else:
                return (upper, lower, ToleranceType.UNILATERAL, None)

        elif self._format == ToleranceFormat.LIMITS:
            upper_lim = self._parse_float(self._edit_limit_upper.text(), 0.0)
            lower_lim = self._parse_float(self._edit_limit_lower.text(), 0.0)
            return (upper_lim, lower_lim, ToleranceType.LIMIT, None)

        elif self._format == ToleranceFormat.FIT_CLASS:
            # Use the fit lookup result
            result = self._do_fit_lookup()
            if result is not None:
                return (result[0], result[1], ToleranceType.UNILATERAL, None)
            return (0.0, 0.0, ToleranceType.BILATERAL, None)

        return (0.0, 0.0, ToleranceType.BILATERAL, None)

    def _on_format_changed(self, button) -> None:
        """Handle format button click."""
        btn_id = self._btn_group.id(button)
        formats = [
            ToleranceFormat.BILATERAL_SYM,
            ToleranceFormat.BILATERAL_ASYM,
            ToleranceFormat.LIMITS,
            ToleranceFormat.FIT_CLASS,
        ]
        self._format = formats[btn_id]
        self._update_field_visibility()

    def _update_field_visibility(self) -> None:
        """Show/hide fields based on the active format."""
        fmt = self._format

        # Symmetric
        self._lbl_sym.setVisible(fmt == ToleranceFormat.BILATERAL_SYM)
        self._edit_sym.setVisible(fmt == ToleranceFormat.BILATERAL_SYM)

        # Asymmetric
        self._lbl_upper.setVisible(fmt == ToleranceFormat.BILATERAL_ASYM)
        self._edit_upper.setVisible(fmt == ToleranceFormat.BILATERAL_ASYM)
        self._lbl_lower.setVisible(fmt == ToleranceFormat.BILATERAL_ASYM)
        self._edit_lower.setVisible(fmt == ToleranceFormat.BILATERAL_ASYM)

        # Limits
        self._lbl_limit_upper.setVisible(fmt == ToleranceFormat.LIMITS)
        self._edit_limit_upper.setVisible(fmt == ToleranceFormat.LIMITS)
        self._lbl_limit_lower.setVisible(fmt == ToleranceFormat.LIMITS)
        self._edit_limit_lower.setVisible(fmt == ToleranceFormat.LIMITS)

        # Fit class
        self._lbl_fit.setVisible(fmt == ToleranceFormat.FIT_CLASS)
        self._edit_fit.setVisible(fmt == ToleranceFormat.FIT_CLASS)
        self._lbl_fit_result.setVisible(fmt == ToleranceFormat.FIT_CLASS)

    def _emit_tolerance(self) -> None:
        """Emit the tolerance_changed signal with current values."""
        upper, lower, tol_type, nom_override = self.get_values()
        self.tolerance_changed.emit(upper, lower, tol_type.value, nom_override)

    def _on_fit_changed(self) -> None:
        """Handle fit class code entry."""
        result = self._do_fit_lookup()
        if result is not None:
            upper_dev, lower_dev, desc = result
            self._lbl_fit_result.setText(
                f"+{upper_dev:.4f}\" / {lower_dev:.4f}\"\n{desc}"
            )
            self._lbl_fit_result.setStyleSheet("QLabel { color: #66bb6a; font-size: 8pt; }")
            self._emit_tolerance()
        else:
            code = self._edit_fit.text().strip()
            if code:
                self._lbl_fit_result.setText("Unknown fit code or nominal out of range")
                self._lbl_fit_result.setStyleSheet("QLabel { color: #ef5350; font-size: 8pt; }")

    def _do_fit_lookup(self) -> Optional[Tuple[float, float, str]]:
        """Perform the ISO 286 fit lookup.

        Returns:
            (upper_deviation_inch, lower_deviation_inch, description) or None.
        """
        from tolerance_analysis.engine.iso286 import lookup_fit_inch, FIT_DESCRIPTIONS

        code = self._edit_fit.text().strip()
        if not code:
            return None

        result = lookup_fit_inch(self._nominal, code)
        if result is None:
            return None

        # Get description if available
        desc = ""
        for key, val in FIT_DESCRIPTIONS.items():
            if code in key:
                desc = val
                break

        return (result.upper_deviation_inch, result.lower_deviation_inch, desc)

    @staticmethod
    def _parse_float(text: str, default: float = 0.0) -> float:
        """Safely parse a float from text."""
        try:
            return float(text.strip())
        except (ValueError, AttributeError):
            return default
