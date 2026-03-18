import sys

from pathlib import Path

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QFont

from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from utils.auth_manager import AuthManager
from utils.local_manager import setup_locale



def main():
    setup_locale()
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

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
