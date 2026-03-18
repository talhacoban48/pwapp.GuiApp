def get_stylesheet() -> str:
    """
    "Graphite Blue" — a comfortable medium-dark theme.

    Palette:
        WINDOW   #1a1d27  main background
        SURFACE  #22263a  panels / groupboxes
        PANEL    #262b40  slightly lighter panel
        INPUT    #2d3248  input fields
        HOVER    #343859  hover state
        SELECT   #3f4a6e  selection
        BORDER   #3e4565  default border
        ACCENT   #4e8bf0  blue accent
        ACCENT2  #6ba0f5  accent hover
        DANGER   #e05c6a  delete / error
        DANGER2  #ea7a86  danger hover
        TEXT1    #dce4f5  primary text
        TEXT2    #8b97b8  labels / secondary
        TEXT3    #5a6486  muted / placeholder
    """
    return """

/* ── Base ─────────────────────────────────────────────── */
QWidget {
    background-color: #1a1d27;
    color: #dce4f5;
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 11pt;
}

/* ── Window / Dialog ──────────────────────────────────── */
QMainWindow {
    background-color: #1a1d27;
}
QDialog {
    background-color: #1e2133;
}

/* ── Menu bar ─────────────────────────────────────────── */
QMenuBar {
    background-color: #151720;
    color: #dce4f5;
    border-bottom: 1px solid #2d3248;
    padding: 2px 6px;
    spacing: 2px;
    font-size: 9pt;
}
QMenuBar::item {
    padding: 5px 12px;
    border-radius: 5px;
}
QMenuBar::item:selected {
    background-color: #262b40;
}
QMenu {
    background-color: #22263a;
    color: #dce4f5;
    border: 1px solid #3e4565;
    border-radius: 8px;
    padding: 6px 0;
    font-size: 9pt;
}
QMenu::item {
    padding: 7px 32px 7px 16px;
    border-radius: 5px;
    margin: 1px 4px;
}
QMenu::item:selected {
    background-color: #343859;
}
QMenu::separator {
    height: 1px;
    background-color: #3e4565;
    margin: 5px 12px;
}
QMenu::shortcut {
    color: #5a6486;
    padding-left: 24px;
}

/* ── GroupBox ─────────────────────────────────────────── */
QGroupBox {
    background-color: #22263a;
    border: 1px solid #2d3248;
    border-radius: 12px;
    margin-top: 0px;
    padding: 12px 8px 8px 8px;
}

QLabel#leftPanelTitle {
    color: #60a5fa;
    font-weight: bold;
    font-size: 10pt;
    background-color: transparent;
}
QLabel#rightPanelTitle {
    color: #a78bfa;
    font-weight: bold;
    font-size: 10pt;
    background-color: transparent;
}

/* ── Labels ───────────────────────────────────────────── */
QLabel {
    background-color: transparent;
    color: #8b97b8;
    font-size: 10pt;
}

/* ── Line edit ────────────────────────────────────────── */
QLineEdit {
    background-color: #2d3248;
    color: #dce4f5;
    border: 1px solid #3e4565;
    border-radius: 7px;
    padding: 5px 12px;
    selection-background-color: #3f4a6e;
    selection-color: #dce4f5;
    font-size: 10pt;
}
QLineEdit:focus {
    border: 1.5px solid #4e8bf0;
    background-color: #303552;
}
QLineEdit:disabled {
    background-color: #22263a;
    color: #5a6486;
    border-color: #2d3248;
}
QLineEdit::placeholder-text {
    color: #5a6486;
}

/* ── Text edit ────────────────────────────────────────── */
QTextEdit {
    background-color: #2d3248;
    color: #dce4f5;
    border: 1px solid #3e4565;
    border-radius: 7px;
    padding: 5px 12px;
    selection-background-color: #3f4a6e;
    selection-color: #dce4f5;
    font-size: 10pt;
}
QTextEdit:focus {
    border: 1.5px solid #4e8bf0;
    background-color: #303552;
}

/* ── Buttons (default — neutral) ─────────────────────── */
QPushButton {
    background-color: #2d3248;
    color: #c4cee6;
    border: 1px solid #3e4565;
    border-radius: 7px;
    padding: 7px 20px;
    font-weight: 600;
    font-size: 10pt;
}
QPushButton:hover {
    background-color: #343859;
    border-color: #4e5a7a;
    color: #dce4f5;
}
QPushButton:pressed {
    background-color: #3f4a6e;
    border-color: #4e8bf0;
}
QPushButton:disabled {
    background-color: #1e2133;
    color: #5a6486;
    border-color: #2d3248;
}

/* Clear — amber */
QPushButton[role="clear"] {
    background-color: #3a2e10;
    color: #f59e0b;
    border: 1px solid #6b5010;
}
QPushButton[role="clear"]:hover {
    background-color: #4a3a14;
    border-color: #f59e0b;
    color: #fbbf24;
}
QPushButton[role="clear"]:pressed {
    background-color: #2e2308;
}

/* Insert — blue */
QPushButton[role="insert"] {
    background-color: #1a2f5a;
    color: #60a5fa;
    border: 1px solid #2a4580;
}
QPushButton[role="insert"]:hover {
    background-color: #1e3870;
    border-color: #60a5fa;
    color: #93c5fd;
}
QPushButton[role="insert"]:pressed {
    background-color: #142244;
}

/* Update — green */
QPushButton[role="update"] {
    background-color: #1e4d35;
    color: #4ade80;
    border: 1px solid #2a6b47;
}
QPushButton[role="update"]:hover {
    background-color: #255c3f;
    border-color: #4ade80;
    color: #6ee89a;
}
QPushButton[role="update"]:pressed {
    background-color: #1a4030;
}

/* Generate — purple */
QPushButton[role="generate"] {
    background-color: #2d1f4a;
    color: #a78bfa;
    border: 1px solid #3f2d6b;
}
QPushButton[role="generate"]:hover {
    background-color: #38266e;
    border-color: #a78bfa;
    color: #c4b5fd;
}
QPushButton[role="generate"]:pressed {
    background-color: #251844;
}

/* Delete — soft red */
QPushButton[role="delete"] {
    background-color: #3d2430;
    color: #e05c6a;
    border: 1px solid #5c2d38;
}
QPushButton[role="delete"]:hover {
    background-color: #4d2d3c;
    border-color: #e05c6a;
    color: #ea7a86;
}
QPushButton[role="delete"]:pressed {
    background-color: #5a2040;
}

/* ── List widget ──────────────────────────────────────── */
QListWidget {
    background-color: #1e2133;
    color: #dce4f5;
    border: 1px solid #2d3248;
    border-radius: 8px;
    outline: none;
    padding: 4px;
    font-size: 10pt;
}
QListWidget::item {
    padding: 8px 8px;
    border-radius: 6px;
    color: #c4cee6;
}
QListWidget::item:hover {
    background-color: #262b40;
    color: #dce4f5;
}
QListWidget::item:selected {
    background-color: #2d3a5e;
    color: #7ab3f8;
    border-left: 3px solid #4e8bf0;
    padding-left: 5px;
}

/* ── Checkbox ─────────────────────────────────────────── */
QCheckBox {
    color: #c4cee6;
    spacing: 8px;
    background-color: transparent;
    font-size: 10pt;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #3e4565;
    border-radius: 5px;
    background-color: #2d3248;
}
QCheckBox::indicator:hover {
    border-color: #4e8bf0;
    background-color: #303552;
}
QCheckBox::indicator:checked {
    background-color: #4e8bf0;
    border-color: #4e8bf0;
}
QCheckBox::indicator:disabled {
    background-color: #22263a;
    border-color: #2d3248;
}

/* ── Scrollbars ───────────────────────────────────────── */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background-color: #3e4565;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background-color: #4e5a7a;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
    height: 0;
}
QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background-color: #3e4565;
    border-radius: 4px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #4e5a7a;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
    width: 0;
}

/* ── MessageBox ───────────────────────────────────────── */
QMessageBox {
    background-color: #22263a;
}
QMessageBox QLabel {
    color: #dce4f5;
    font-size: 11pt;
    background-color: transparent;
}

/* ── Copy buttons ─────────────────────────────────────── */
QPushButton#copyBtn {
    background-color: transparent;
    color: #8b97b8;
    border: 1px solid #3e4565;
    border-radius: 5px;
    font-size: 14px;
    padding: 0;
}
QPushButton#copyBtn:hover {
    color: #60a5fa;
    border-color: #60a5fa;
    background-color: #1a2f5a;
}
QPushButton#copyBtn:pressed {
    background-color: #1e3870;
}

/* ── Cancel search button ────────────────────────────── */
QPushButton#cancelSearchBtn {
    background-color: transparent;
    border: 1px solid #3e4565;
    border-radius: 5px;
    padding: 0;
}
QPushButton#cancelSearchBtn:hover {
    border-color: #e05252;
    background-color: #3a1a1a;
}
QPushButton#cancelSearchBtn:pressed {
    background-color: #4a2020;
}

/* ── ToolTip ──────────────────────────────────────────── */
QToolTip {
    background-color: #262b40;
    color: #dce4f5;
    border: 1px solid #3e4565;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 10pt;
}

"""
