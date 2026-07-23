"""Chain tab widget containing the contributor table.

Provides a spreadsheet-style table for viewing and editing tolerance chain
contributors, with chain selection, reordering controls, and inline editing
with validation feedback.

Validates: Requirements 1.5, 11.1, 11.2, 11.5
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QItemDelegate,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tolerance_analysis.boundary.controller import AnalysisController
from tolerance_analysis.engine.models import (
    Contributor,
    Direction,
    ToleranceType,
)


# Maximum number of contributors supported per chain
MAX_CONTRIBUTORS = 100

# Column indices
COL_INDEX = 0
COL_NAME = 1
COL_NOMINAL = 2
COL_TOLERANCE = 3
COL_DIRECTION = 4

COLUMN_HEADERS = ["#", "Name", "Nominal", "Tolerance", "Direction"]

# Direction display mapping
DIRECTION_OPTIONS = ["Positive", "Negative"]
DIRECTION_MAP = {"Positive": Direction.POSITIVE, "Negative": Direction.NEGATIVE}
DIRECTION_REVERSE = {Direction.POSITIVE: "Positive", Direction.NEGATIVE: "Negative"}

# Tolerance type display mapping
TYPE_OPTIONS = ["Bilateral", "Unilateral", "Limit"]
TYPE_MAP = {
    "Bilateral": ToleranceType.BILATERAL,
    "Unilateral": ToleranceType.UNILATERAL,
    "Limit": ToleranceType.LIMIT,
}
TYPE_REVERSE = {
    ToleranceType.BILATERAL: "Bilateral",
    ToleranceType.UNILATERAL: "Unilateral",
    ToleranceType.LIMIT: "Limit",
}

# Error styling
ERROR_COLOR = QColor(239, 83, 80, 60)  # Red with transparency


class NumericDelegate(QItemDelegate):
    """Delegate for inline editing of numeric cells with validation."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index
    ) -> QWidget:
        """Create a QLineEdit editor for numeric input."""
        editor = QLineEdit(parent)
        editor.setFrame(False)
        return editor

    def setEditorData(self, editor: QLineEdit, index) -> None:
        """Set the editor text from the model data."""
        value = index.data(Qt.EditRole)
        if value is not None:
            editor.setText(str(value))

    def setModelData(self, editor: QLineEdit, model, index) -> None:
        """Validate and commit the editor data to the model."""
        model.setData(index, editor.text(), Qt.EditRole)


class ComboDelegate(QItemDelegate):
    """Delegate for inline editing of combo box cells."""

    def __init__(self, options: list[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._options = options

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index
    ) -> QWidget:
        """Create a QComboBox editor."""
        editor = QComboBox(parent)
        editor.addItems(self._options)
        editor.setFrame(False)
        return editor

    def setEditorData(self, editor: QComboBox, index) -> None:
        """Set the combo box selection from the model data."""
        value = index.data(Qt.EditRole)
        idx = editor.findText(str(value))
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor: QComboBox, model, index) -> None:
        """Commit the combo box selection to the model."""
        model.setData(index, editor.currentText(), Qt.EditRole)


class ChainTab(QWidget):
    """Widget containing chain selection and contributor table.

    Provides:
    - Chain selector combo box
    - New/Delete chain buttons
    - QTableWidget with inline editing for contributors
    - Add/Remove contributor buttons
    - Move Up/Move Down reordering buttons

    Signals:
        contributor_selected(str): Emitted when a row is clicked (contributor ID).
        chain_changed(): Emitted when any contributor data changes.
    """

    contributor_selected = pyqtSignal(str)
    chain_changed = pyqtSignal()

    def __init__(self, controller: AnalysisController, parent: Optional[QWidget] = None) -> None:
        """Initialize ChainTab with a reference to the AnalysisController.

        Args:
            controller: The AnalysisController instance for data operations.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._controller = controller
        self._current_chain_id: Optional[str] = None
        self._updating = False  # Guard against recursive updates
        self._table_edit_in_progress = False  # Guard against table refresh during cell edit

        self._setup_ui()
        self._connect_signals()
        self._refresh_chain_selector()

    def _setup_ui(self) -> None:
        """Build the widget layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- Chain selector row ---
        chain_row = QHBoxLayout()
        chain_row.setSpacing(6)

        self._chain_combo = QComboBox()
        self._chain_combo.setMinimumWidth(200)
        chain_row.addWidget(self._chain_combo)

        self._new_chain_btn = QPushButton("New Chain")
        chain_row.addWidget(self._new_chain_btn)

        self._delete_chain_btn = QPushButton("Delete Chain")
        chain_row.addWidget(self._delete_chain_btn)

        chain_row.addStretch()
        layout.addLayout(chain_row)

        # --- Contributor table ---
        self._table = QTableWidget()
        self._table.setColumnCount(len(COLUMN_HEADERS))
        self._table.setHorizontalHeaderLabels(COLUMN_HEADERS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(COL_INDEX, QHeaderView.Fixed)
        self._table.setColumnWidth(COL_INDEX, 40)
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_NOMINAL, QHeaderView.Interactive)
        self._table.setColumnWidth(COL_NOMINAL, 135)
        header.setSectionResizeMode(COL_TOLERANCE, QHeaderView.Interactive)
        self._table.setColumnWidth(COL_TOLERANCE, 180)
        header.setSectionResizeMode(COL_DIRECTION, QHeaderView.Interactive)
        self._table.setColumnWidth(COL_DIRECTION, 120)

        # Set delegates for inline editing
        self._table.setItemDelegateForColumn(COL_NOMINAL, NumericDelegate(self._table))
        self._table.setItemDelegateForColumn(
            COL_DIRECTION, ComboDelegate(DIRECTION_OPTIONS, self._table)
        )

        layout.addWidget(self._table)

        # --- Button row ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._add_btn = QPushButton("Add Contributor")
        btn_row.addWidget(self._add_btn)

        self._remove_btn = QPushButton("Remove Contributor")
        btn_row.addWidget(self._remove_btn)

        btn_row.addStretch()

        self._move_up_btn = QPushButton("Move Up")
        btn_row.addWidget(self._move_up_btn)

        self._move_down_btn = QPushButton("Move Down")
        btn_row.addWidget(self._move_down_btn)

        layout.addLayout(btn_row)

    def _connect_signals(self) -> None:
        """Wire up signals and slots."""
        self._chain_combo.currentIndexChanged.connect(self._on_chain_selected)
        self._new_chain_btn.clicked.connect(self._on_new_chain)
        self._delete_chain_btn.clicked.connect(self._on_delete_chain)
        self._add_btn.clicked.connect(self._on_add_contributor)
        self._remove_btn.clicked.connect(self._on_remove_contributor)
        self._move_up_btn.clicked.connect(self._on_move_up)
        self._move_down_btn.clicked.connect(self._on_move_down)
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.cellChanged.connect(self._on_cell_changed)

    # --- Chain management ---

    def _refresh_chain_selector(self) -> None:
        """Repopulate the chain combo box from the controller."""
        self._updating = True
        self._chain_combo.clear()
        for chain in self._controller.project.tolerance_chains:
            self._chain_combo.addItem(chain.name, chain.id)

        # Restore selection if possible, otherwise select first chain
        if self._current_chain_id:
            for i in range(self._chain_combo.count()):
                if self._chain_combo.itemData(i) == self._current_chain_id:
                    self._chain_combo.setCurrentIndex(i)
                    break
        elif self._chain_combo.count() > 0:
            self._current_chain_id = self._chain_combo.itemData(0)
            self._chain_combo.setCurrentIndex(0)

        self._updating = False
        self._refresh_table()

    def _on_chain_selected(self, index: int) -> None:
        """Handle chain selection change."""
        if self._updating or index < 0:
            return
        self._current_chain_id = self._chain_combo.itemData(index)
        self._refresh_table()

    def _on_new_chain(self) -> None:
        """Create a new chain with a default name."""
        existing = [c.name for c in self._controller.project.tolerance_chains]
        base_name = "New Chain"
        name = base_name
        counter = 1
        while name in existing:
            counter += 1
            name = f"{base_name} {counter}"

        chain_id = self._controller.create_chain(name)
        if chain_id:
            self._current_chain_id = chain_id
            self._refresh_chain_selector()
            self.chain_changed.emit()

    def _on_delete_chain(self) -> None:
        """Delete the currently selected chain after confirmation."""
        if not self._current_chain_id:
            return

        reply = QMessageBox.question(
            self,
            "Delete Chain",
            "Are you sure you want to delete this chain?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._controller.delete_chain(self._current_chain_id)
            self._current_chain_id = None
            self._refresh_chain_selector()
            self.chain_changed.emit()

    # --- Contributor management ---

    def _on_add_contributor(self) -> None:
        """Add a new default contributor to the current chain."""
        if not self._current_chain_id:
            return

        chain = self._controller.get_chain(self._current_chain_id)
        if chain and len(chain.contributors) >= MAX_CONTRIBUTORS:
            QMessageBox.warning(
                self,
                "Limit Reached",
                f"A chain supports up to {MAX_CONTRIBUTORS} contributors.",
            )
            return

        contributor = Contributor(
            name="New Contributor",
            nominal=1.0,
            direction=Direction.POSITIVE,
            tolerance_type=ToleranceType.BILATERAL,
            upper_tolerance=0.001,
            lower_tolerance=0.001,
        )
        self._controller.add_contributor(self._current_chain_id, contributor)
        self._refresh_table()
        self.chain_changed.emit()

    def _on_remove_contributor(self) -> None:
        """Remove the currently selected contributor."""
        if not self._current_chain_id:
            return

        row = self._table.currentRow()
        if row < 0:
            return

        chain = self._controller.get_chain(self._current_chain_id)
        if not chain or row >= len(chain.contributors):
            return

        contributor_id = chain.contributors[row].id
        self._controller.remove_contributor(self._current_chain_id, contributor_id)
        self._refresh_table()
        self.chain_changed.emit()

    def _on_move_up(self) -> None:
        """Move the selected contributor up one position."""
        self._move_contributor(-1)

    def _on_move_down(self) -> None:
        """Move the selected contributor down one position."""
        self._move_contributor(1)

    def _move_contributor(self, direction: int) -> None:
        """Reorder the selected contributor by swapping with adjacent.

        Args:
            direction: -1 for up, +1 for down.
        """
        if not self._current_chain_id:
            return

        row = self._table.currentRow()
        if row < 0:
            return

        chain = self._controller.get_chain(self._current_chain_id)
        if not chain:
            return

        new_row = row + direction
        if new_row < 0 or new_row >= len(chain.contributors):
            return

        # Build new order by swapping
        ids = [c.id for c in chain.contributors]
        ids[row], ids[new_row] = ids[new_row], ids[row]
        self._controller.reorder_contributors(self._current_chain_id, ids)

        self._refresh_table()
        self._table.selectRow(new_row)
        self.chain_changed.emit()

    # --- Table refresh ---

    def _refresh_table(self) -> None:
        """Reload the table from the controller's data model."""
        self._updating = True
        self._table.setRowCount(0)

        if not self._current_chain_id:
            self._updating = False
            return

        chain = self._controller.get_chain(self._current_chain_id)
        if not chain:
            self._updating = False
            return

        self._table.setRowCount(len(chain.contributors))

        for row, contrib in enumerate(chain.contributors):
            # Index column (read-only)
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setFlags(index_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, COL_INDEX, index_item)

            # Name
            name_item = QTableWidgetItem(contrib.name)
            self._table.setItem(row, COL_NAME, name_item)

            # Nominal
            nom_item = QTableWidgetItem(str(contrib.nominal))
            self._table.setItem(row, COL_NOMINAL, nom_item)

            # Tolerance (formatted display string, read-only — edit via detail panel)
            tol_str = self._format_tolerance(contrib)
            tol_item = QTableWidgetItem(tol_str)
            tol_item.setFlags(tol_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, COL_TOLERANCE, tol_item)

            # Direction
            dir_item = QTableWidgetItem(DIRECTION_REVERSE.get(contrib.direction, "Positive"))
            self._table.setItem(row, COL_DIRECTION, dir_item)

        self._updating = False

    # --- Cell editing ---

    def _on_cell_changed(self, row: int, col: int) -> None:
        """Handle cell edits — validate and push to the controller."""
        if self._updating:
            return

        if not self._current_chain_id:
            return

        chain = self._controller.get_chain(self._current_chain_id)
        if not chain or row >= len(chain.contributors):
            return

        contributor = chain.contributors[row]
        item = self._table.item(row, col)
        if item is None:
            return

        value = item.text()

        if col == COL_NAME:
            contributor.name = value
            self._clear_cell_error(item)

        elif col == COL_NOMINAL:
            valid, parsed, error_msg = self._controller.validator.validate_numeric_input(
                value,
                COLUMN_HEADERS[col],
            )
            if valid and parsed is not None:
                contributor.nominal = parsed
                self._clear_cell_error(item)
            else:
                self._set_cell_error(item, error_msg)
                return  # Don't emit chain_changed on invalid input

        elif col == COL_DIRECTION:
            direction = DIRECTION_MAP.get(value)
            if direction:
                contributor.direction = direction
                self._clear_cell_error(item)

        # COL_TOLERANCE is read-only (edited via detail panel)

        # Emit signal — but mark that change came from table so refresh
        # doesn't destroy the items we're still referencing
        self._table_edit_in_progress = True
        self.chain_changed.emit()
        self._table_edit_in_progress = False

    def _on_cell_clicked(self, row: int, col: int) -> None:
        """Emit contributor_selected when a row is clicked."""
        if not self._current_chain_id:
            return

        chain = self._controller.get_chain(self._current_chain_id)
        if not chain or row >= len(chain.contributors):
            return

        contributor_id = chain.contributors[row].id
        self.contributor_selected.emit(contributor_id)

    # --- Validation feedback ---

    @staticmethod
    def _format_tolerance(contrib: Contributor) -> str:
        """Format a contributor's tolerance for display in the table.

        Examples: "±0.0010", "+0.0020 / −0.0010", "Lim [1.000, 1.002]"
        """
        if contrib.tolerance_type == ToleranceType.LIMIT:
            return f"Lim [{contrib.lower_tolerance:.4f}, {contrib.upper_tolerance:.4f}]"
        elif abs(contrib.upper_tolerance - contrib.lower_tolerance) < 1e-10:
            return f"±{contrib.upper_tolerance:.4f}"
        else:
            return f"+{contrib.upper_tolerance:.4f} / −{contrib.lower_tolerance:.4f}"

    def _set_cell_error(self, item: QTableWidgetItem, message: str) -> None:
        """Mark a cell as invalid with red background and error tooltip.

        Args:
            item: The table item to mark.
            message: Error message for the tooltip.
        """
        item.setBackground(ERROR_COLOR)
        item.setToolTip(message)

    def _clear_cell_error(self, item: QTableWidgetItem) -> None:
        """Clear error styling from a cell.

        Args:
            item: The table item to clear.
        """
        item.setBackground(QColor(0, 0, 0, 0))  # Transparent
        item.setToolTip("")
