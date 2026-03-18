import sys
import locale

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


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
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
