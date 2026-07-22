"""
Dialog widgets for the Tolerance Analysis Tool.

Provides confirmation, error, validation, and new-chain dialogs
used throughout the application GUI layer.
"""

from typing import Optional, Tuple

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt


class ConfirmDeleteDialog:
    """Simple yes/no confirmation dialog for contributor deletion.

    Uses QMessageBox for a native-feeling confirmation prompt.
    Returns True if the user confirms deletion, False otherwise.
    """

    @staticmethod
    def confirm(parent: Optional[QWidget], name: str) -> bool:
        """Show a confirmation dialog for deleting a contributor.

        Args:
            parent: Parent widget for modal positioning.
            name: Name of the contributor to delete.

        Returns:
            True if user clicked Delete, False if cancelled.
        """
        msg = QMessageBox(parent)
        msg.setWindowTitle("Confirm Deletion")
        msg.setText(f"Are you sure you want to delete contributor '{name}'?")
        msg.setIcon(QMessageBox.Warning)

        delete_btn = msg.addButton("Delete", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.setDefaultButton(cancel_btn)

        msg.exec_()
        return msg.clickedButton() == delete_btn


class ErrorDialog:
    """Displays error messages to the user.

    Provides a static method for showing error dialogs with a custom
    title and message, using a single OK button.
    """

    @staticmethod
    def show_error(
        parent: Optional[QWidget],
        title: str = "Error",
        message: str = "",
    ) -> None:
        """Show an error dialog.

        Args:
            parent: Parent widget for modal positioning.
            title: Dialog window title.
            message: Error description to display.
        """
        msg = QMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


class ValidationErrorDialog:
    """Shows a list of validation errors.

    Displays multiple error messages in a scrollable list with a
    single OK button for dismissal.
    """

    @staticmethod
    def show_errors(
        parent: Optional[QWidget],
        errors: list,
    ) -> None:
        """Show a dialog listing validation errors.

        Args:
            parent: Parent widget for modal positioning.
            errors: List of error message strings.
        """
        dialog = QDialog(parent)
        dialog.setWindowTitle("Validation Error")
        dialog.setModal(True)
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout(dialog)

        label = QLabel("The following validation errors were found:")
        layout.addWidget(label)

        error_list = QListWidget()
        error_list.addItems(errors)
        layout.addWidget(error_list)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec_()


class NewChainDialog(QDialog):
    """Modal dialog for creating a new tolerance chain.

    Collects a chain name (1-100 characters, required) and an optional
    description (0-500 characters). Shows inline validation errors
    when the name field is empty on submission.

    Returns (name, description) tuple via get_result() after acceptance,
    or None if cancelled.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Tolerance Chain")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Name field
        name_label = QLabel("Chain Name (required):")
        layout.addWidget(name_label)

        self._name_edit = QLineEdit()
        self._name_edit.setMaxLength(100)
        self._name_edit.setPlaceholderText("Enter chain name (1-100 characters)")
        layout.addWidget(self._name_edit)

        # Inline error label for name
        self._name_error_label = QLabel("")
        self._name_error_label.setStyleSheet("color: #ef5350; font-size: 9pt;")
        self._name_error_label.setVisible(False)
        layout.addWidget(self._name_error_label)

        # Description field
        desc_label = QLabel("Description (optional):")
        layout.addWidget(desc_label)

        self._desc_edit = QPlainTextEdit()
        self._desc_edit.setMaximumBlockCount(0)  # no line limit
        self._desc_edit.setPlaceholderText("Enter description (0-500 characters)")
        self._desc_edit.setFixedHeight(100)
        layout.addWidget(self._desc_edit)

        # Character count label for description
        self._desc_count_label = QLabel("0 / 500")
        self._desc_count_label.setStyleSheet("color: #616161; font-size: 8pt;")
        self._desc_count_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self._desc_count_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton("OK")
        self._ok_btn.setDefault(True)
        self._ok_btn.clicked.connect(self._on_accept)
        button_layout.addWidget(self._ok_btn)

        layout.addLayout(button_layout)

        # Connect signals for live validation feedback
        self._name_edit.textChanged.connect(self._on_name_changed)
        self._desc_edit.textChanged.connect(self._on_desc_changed)

    def _on_name_changed(self, text: str) -> None:
        """Clear error when user starts typing."""
        if text.strip():
            self._name_error_label.setVisible(False)
            self._name_edit.setStyleSheet("")

    def _on_desc_changed(self) -> None:
        """Enforce 500-char limit on description and update counter."""
        text = self._desc_edit.toPlainText()
        if len(text) > 500:
            # Truncate to 500 characters
            cursor = self._desc_edit.textCursor()
            self._desc_edit.setPlainText(text[:500])
            cursor.movePosition(cursor.End)
            self._desc_edit.setTextCursor(cursor)
            text = text[:500]
        self._desc_count_label.setText(f"{len(text)} / 500")

    def _on_accept(self) -> None:
        """Validate inputs before accepting the dialog."""
        name = self._name_edit.text().strip()

        if not name:
            self._name_error_label.setText("Chain name cannot be empty.")
            self._name_error_label.setVisible(True)
            self._name_edit.setStyleSheet("border: 1px solid #ef5350;")
            self._name_edit.setFocus()
            return

        if len(name) > 100:
            self._name_error_label.setText("Chain name must be 100 characters or fewer.")
            self._name_error_label.setVisible(True)
            self._name_edit.setStyleSheet("border: 1px solid #ef5350;")
            self._name_edit.setFocus()
            return

        self.accept()

    def get_result(self) -> Optional[Tuple[str, str]]:
        """Get the dialog result after execution.

        Returns:
            A tuple of (name, description) if accepted, None if cancelled.
        """
        if self.result() == QDialog.Accepted:
            name = self._name_edit.text().strip()
            description = self._desc_edit.toPlainText()[:500]
            return (name, description)
        return None

    @staticmethod
    def get_new_chain(parent: Optional[QWidget] = None) -> Optional[Tuple[str, str]]:
        """Convenience static method to show the dialog and return result.

        Args:
            parent: Parent widget for modal positioning.

        Returns:
            A tuple of (name, description) if accepted, None if cancelled.
        """
        dialog = NewChainDialog(parent)
        dialog.exec_()
        return dialog.get_result()
