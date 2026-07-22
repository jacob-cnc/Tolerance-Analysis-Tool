"""
Detail panel for displaying and editing a selected contributor's properties.

Provides an expanded card view with distribution picker, notes field, and
material name when a contributor is selected in the contributor table.
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from tolerance_analysis.engine.models import Contributor, DistributionType


class DetailPanel(QWidget):
    """Expanded card view for a selected contributor.

    Displays distribution type picker, notes field, material name, and
    description for the currently selected contributor. Shows a placeholder
    message when no contributor is selected.

    Signals:
        distribution_changed(contributor_id, distribution): Emitted when the
            user changes the distribution type.
        notes_changed(contributor_id, notes): Emitted when the user edits
            the notes field.
        material_changed(contributor_id, material): Emitted when the user
            edits the material field.
    """

    distribution_changed = pyqtSignal(str, str)  # contributor_id, distribution value
    notes_changed = pyqtSignal(str, str)  # contributor_id, notes text
    material_changed = pyqtSignal(str, str)  # contributor_id, material text

    # Maximum character limits
    MAX_NOTES_CHARS = 500
    MAX_DESCRIPTION_CHARS = 200

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_contributor_id: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the panel UI with placeholder and detail views."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder shown when no contributor is selected
        self._placeholder = QLabel("Select a contributor to view details")
        self._placeholder.setStyleSheet(
            "color: #616161; font-style: italic; padding: 20px;"
        )
        self._layout.addWidget(self._placeholder)

        # Detail group box (hidden until a contributor is selected)
        self._detail_group = QGroupBox("Contributor Details")
        detail_layout = QFormLayout(self._detail_group)
        detail_layout.setContentsMargins(12, 16, 12, 12)
        detail_layout.setSpacing(8)

        # Contributor name (read-only label)
        self._name_label = QLabel()
        self._name_label.setStyleSheet("font-weight: 600;")
        detail_layout.addRow("Name:", self._name_label)

        # Distribution type picker
        self._distribution_combo = QComboBox()
        self._distribution_combo.addItem("Normal", DistributionType.NORMAL.value)
        self._distribution_combo.addItem("Uniform", DistributionType.UNIFORM.value)
        self._distribution_combo.addItem("Triangular", DistributionType.TRIANGULAR.value)
        self._distribution_combo.currentIndexChanged.connect(self._on_distribution_changed)
        detail_layout.addRow("Distribution:", self._distribution_combo)

        # Material field
        self._material_edit = QLineEdit()
        self._material_edit.setPlaceholderText("e.g., 6061-T6 Aluminum")
        self._material_edit.textChanged.connect(self._on_material_changed)
        detail_layout.addRow("Material:", self._material_edit)

        # Description field (up to 200 chars)
        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("Brief description (max 200 chars)")
        self._description_edit.setMaxLength(self.MAX_DESCRIPTION_CHARS)
        detail_layout.addRow("Description:", self._description_edit)

        # Notes field (up to 500 chars)
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setPlaceholderText("Notes (max 500 chars)")
        self._notes_edit.setMaximumHeight(100)
        self._notes_edit.textChanged.connect(self._on_notes_changed)
        detail_layout.addRow("Notes:", self._notes_edit)

        # Character count label for notes
        self._notes_count_label = QLabel("0 / 500")
        self._notes_count_label.setStyleSheet("color: #616161; font-size: 8pt;")
        detail_layout.addRow("", self._notes_count_label)

        self._detail_group.setVisible(False)
        self._layout.addWidget(self._detail_group)

        self._layout.addStretch()

    def set_contributor(self, contributor: Contributor | None) -> None:
        """Update the panel to display the given contributor's details.

        Args:
            contributor: The contributor to display, or None to show the
                placeholder message.
        """
        if contributor is None:
            self._current_contributor_id = None
            self._detail_group.setVisible(False)
            self._placeholder.setVisible(True)
            return

        self._current_contributor_id = contributor.id
        self._placeholder.setVisible(False)
        self._detail_group.setVisible(True)

        # Block signals while populating to avoid spurious emissions
        self._distribution_combo.blockSignals(True)
        self._material_edit.blockSignals(True)
        self._notes_edit.blockSignals(True)

        # Populate fields
        self._name_label.setText(contributor.name)

        # Set distribution combo to match contributor's distribution
        dist_index = self._distribution_combo.findData(contributor.distribution.value)
        if dist_index >= 0:
            self._distribution_combo.setCurrentIndex(dist_index)

        self._material_edit.setText(contributor.material)
        self._description_edit.setText(contributor.description)
        self._notes_edit.setPlainText(contributor.notes)
        self._update_notes_count()

        # Restore signals
        self._distribution_combo.blockSignals(False)
        self._material_edit.blockSignals(False)
        self._notes_edit.blockSignals(False)

    def clear(self) -> None:
        """Reset the panel to its placeholder state."""
        self.set_contributor(None)

    @property
    def current_contributor_id(self) -> str | None:
        """The ID of the currently displayed contributor, or None."""
        return self._current_contributor_id

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_distribution_changed(self, index: int) -> None:
        """Handle distribution combo box selection change."""
        if self._current_contributor_id is None:
            return
        dist_value = self._distribution_combo.itemData(index)
        if dist_value is not None:
            self.distribution_changed.emit(self._current_contributor_id, dist_value)

    def _on_notes_changed(self) -> None:
        """Handle notes text edit change, enforcing 500 char limit."""
        if self._current_contributor_id is None:
            return

        text = self._notes_edit.toPlainText()
        if len(text) > self.MAX_NOTES_CHARS:
            # Truncate and reposition cursor
            self._notes_edit.blockSignals(True)
            cursor = self._notes_edit.textCursor()
            pos = cursor.position()
            self._notes_edit.setPlainText(text[: self.MAX_NOTES_CHARS])
            cursor.setPosition(min(pos, self.MAX_NOTES_CHARS))
            self._notes_edit.setTextCursor(cursor)
            self._notes_edit.blockSignals(False)
            text = text[: self.MAX_NOTES_CHARS]

        self._update_notes_count()
        self.notes_changed.emit(self._current_contributor_id, text)

    def _on_material_changed(self, text: str) -> None:
        """Handle material line edit text change."""
        if self._current_contributor_id is None:
            return
        self.material_changed.emit(self._current_contributor_id, text)

    def _update_notes_count(self) -> None:
        """Update the character count label for the notes field."""
        count = len(self._notes_edit.toPlainText())
        self._notes_count_label.setText(f"{count} / {self.MAX_NOTES_CHARS}")
