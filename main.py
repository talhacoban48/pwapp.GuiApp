import sys
import locale
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QDialog

from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from utils.auth_manager import AuthManager


def _setup_locale():
    """
    Try to set Turkish locale for correct alphabetical sorting (locale.strxfrm).
    Tries platform-specific names; silently skips if unavailable.
    """
    candidates = [
        "Turkish_Turkey.1254",  # Windows
        "tr_TR.UTF-8",          # Linux / macOS
        "tr_TR.utf8",
        "tr_TR",
    ]
    for name in candidates:
        try:
            locale.setlocale(locale.LC_ALL, name)
            return
        except locale.Error:
            continue


def main():
    _setup_locale()
    app = QApplication(sys.argv)

    basepath = Path.home() / "pwapp"
    basepath.mkdir(parents=True, exist_ok=True)

    auth = AuthManager(basepath)
    first_run = not auth.is_configured()

    dialog = LoginDialog(auth)
    if dialog.exec_() != QDialog.Accepted:
        sys.exit(0)

    fernet = dialog.fernet
    window = MainWindow(fernet=fernet, auth_manager=auth, first_run=first_run)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
