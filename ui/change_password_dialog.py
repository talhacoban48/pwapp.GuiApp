from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

from utils.auth_manager import AuthManager
from utils.resources import get_resource_path

_FONT = QFont("Times", 11)
_MIN_PASSWORD_LENGTH = 4


class ChangePasswordDialog(QDialog):

    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.new_password: str | None = None

        self.setWindowTitle("Change Master Password")
        self.setWindowIcon(QIcon(get_resource_path("assets/Password.ico")))
        self.setFixedWidth(420)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(30, 24, 30, 24)

        title = QLabel("Change Master Password")
        title.setFont(QFont("Times", 13))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(8)

        self._current_pw = self._make_field()
        layout.addWidget(QLabel("Current Password:", font=_FONT))
        layout.addWidget(self._current_pw)

        self._new_pw = self._make_field()
        layout.addWidget(QLabel("New Password:", font=_FONT))
        layout.addWidget(self._new_pw)

        self._confirm_pw = self._make_field()
        self._confirm_pw.returnPressed.connect(self._on_change)
        layout.addWidget(QLabel("Confirm New Password:", font=_FONT))
        layout.addWidget(self._confirm_pw)

        show_cb = QCheckBox("Show passwords")
        show_cb.setFont(_FONT)
        show_cb.toggled.connect(self._toggle_visibility)
        layout.addWidget(show_cb)

        layout.addSpacing(8)

        change_btn = QPushButton("Change Password")
        change_btn.setFont(_FONT)
        change_btn.setMinimumHeight(40)
        change_btn.clicked.connect(self._on_change)
        layout.addWidget(change_btn)

        self.setLayout(layout)

    @staticmethod
    def _make_field() -> QLineEdit:
        field = QLineEdit()
        field.setFont(_FONT)
        field.setMinimumHeight(36)
        field.setEchoMode(QLineEdit.Password)
        return field

    def _toggle_visibility(self, checked: bool):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        for field in (self._current_pw, self._new_pw, self._confirm_pw):
            field.setEchoMode(mode)

    def _on_change(self):
        current = self._current_pw.text()
        new_pw  = self._new_pw.text()
        confirm = self._confirm_pw.text()

        if not current:
            QMessageBox.warning(self, "Warning", "Enter your current password.")
            return

        if self.auth_manager.login(current) is None:
            QMessageBox.critical(self, "Wrong Password",
                                 "Current password is incorrect.")
            self._current_pw.clear()
            self._current_pw.setFocus()
            return

        if len(new_pw) < _MIN_PASSWORD_LENGTH:
            QMessageBox.warning(
                self, "Warning",
                f"New password must be at least {_MIN_PASSWORD_LENGTH} characters."
            )
            return

        if new_pw != confirm:
            QMessageBox.warning(self, "Warning", "New passwords do not match.")
            self._confirm_pw.clear()
            self._confirm_pw.setFocus()
            return

        self.new_password = new_pw
        self.accept()
