import sys

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from cryptography.fernet import Fernet

from utils.auth_manager import AuthManager
from utils.resources import get_resource_path

_FONT = QFont("Times", 11)
_MIN_PASSWORD_LENGTH = 6


class LoginDialog(QDialog):
    """
    Shown at startup before the main window.

    - First run  (auth not configured): "Create Master Password" mode
    - Subsequent (auth configured)    : "Login" mode

    On success  → dialog is accepted  and self.fernet holds the Fernet key.
    On close/cancel without auth → application exits.
    """

    def __init__(self, auth_manager: AuthManager):
        super().__init__()
        self.auth_manager = auth_manager
        self.fernet: Fernet | None = None

        self.setWindowIcon(QIcon(get_resource_path("assets/Password.ico")))
        self.setFixedWidth(420)
        self.setModal(True)
        # Disable the ? help button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        if auth_manager.is_configured():
            self._build_login_ui()
        else:
            self._build_setup_ui()

    # ------------------------------------------------------------------ #
    #  UI builders                                                         #
    # ------------------------------------------------------------------ #

    def _build_login_ui(self):
        self.setWindowTitle("Password Manager — Login")

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(30, 24, 30, 24)

        title = QLabel("Enter your master password")
        title.setFont(QFont("Times", 13))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(8)

        self._pw_field = self._make_password_field()
        self._pw_field.returnPressed.connect(self._on_login)
        layout.addWidget(QLabel("Master Password:", font=_FONT))
        layout.addWidget(self._pw_field)

        show_cb = QCheckBox("Show password")
        show_cb.setFont(_FONT)
        show_cb.toggled.connect(self._toggle_visibility_single)
        layout.addWidget(show_cb)

        layout.addSpacing(8)

        login_btn = QPushButton("Login")
        login_btn.setFont(_FONT)
        login_btn.setMinimumHeight(40)
        login_btn.clicked.connect(self._on_login)
        layout.addWidget(login_btn)

        self.setLayout(layout)

    def _build_setup_ui(self):
        self.setWindowTitle("Password Manager — Create Master Password")

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(30, 24, 30, 24)

        title = QLabel("Welcome! Create a master password.")
        title.setFont(QFont("Times", 13))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        note = QLabel(
            "This password protects all your stored passwords.\n"
            "If you forget it, your data cannot be recovered."
        )
        note.setFont(QFont("Times", 10))
        note.setAlignment(Qt.AlignCenter)
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addSpacing(8)

        self._pw_field = self._make_password_field()
        layout.addWidget(QLabel("New Password:", font=_FONT))
        layout.addWidget(self._pw_field)

        self._pw_confirm_field = self._make_password_field()
        self._pw_confirm_field.returnPressed.connect(self._on_setup)
        layout.addWidget(QLabel("Confirm Password:", font=_FONT))
        layout.addWidget(self._pw_confirm_field)

        show_cb = QCheckBox("Show password")
        show_cb.setFont(_FONT)
        show_cb.toggled.connect(self._toggle_visibility_both)
        layout.addWidget(show_cb)

        layout.addSpacing(8)

        create_btn = QPushButton("Create")
        create_btn.setFont(_FONT)
        create_btn.setMinimumHeight(40)
        create_btn.clicked.connect(self._on_setup)
        layout.addWidget(create_btn)

        self.setLayout(layout)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _make_password_field() -> QLineEdit:
        field = QLineEdit()
        field.setFont(_FONT)
        field.setMinimumHeight(36)
        field.setEchoMode(QLineEdit.Password)
        return field

    def _toggle_visibility_single(self, checked: bool):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self._pw_field.setEchoMode(mode)

    def _toggle_visibility_both(self, checked: bool):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self._pw_field.setEchoMode(mode)
        self._pw_confirm_field.setEchoMode(mode)

    # ------------------------------------------------------------------ #
    #  Slots                                                               #
    # ------------------------------------------------------------------ #

    def _on_login(self):
        password = self._pw_field.text()
        if not password:
            QMessageBox.warning(self, "Warning", "Please enter your master password.")
            return

        fernet = self.auth_manager.login(password)
        if fernet is None:
            QMessageBox.critical(self, "Wrong Password",
                                 "Incorrect master password. Please try again.")
            self._pw_field.clear()
            self._pw_field.setFocus()
            return

        self.fernet = fernet
        self.accept()

    def _on_setup(self):
        password = self._pw_field.text()
        confirm  = self._pw_confirm_field.text()

        if len(password) < _MIN_PASSWORD_LENGTH:
            QMessageBox.warning(
                self, "Warning",
                f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
            )
            return

        if password != confirm:
            QMessageBox.warning(self, "Warning", "Passwords do not match.")
            self._pw_confirm_field.clear()
            self._pw_confirm_field.setFocus()
            return

        self.fernet = self.auth_manager.setup(password)
        self.accept()

    # ------------------------------------------------------------------ #
    #  Prevent closing without authentication                              #
    # ------------------------------------------------------------------ #

    def closeEvent(self, event):
        """Closing the login dialog exits the application."""
        sys.exit(0)
