from PyQt5.QtWidgets import QHBoxLayout, QLabel
from PyQt5.QtGui import QFont

_LABEL_FONT = QFont("Segoe UI", 10)


def make_field_row(label_text: str, *field_widgets) -> QHBoxLayout:
    """
    Return a QHBoxLayout with:
      - a right-aligned label taking 30% of the width
      - one or more field widgets left-aligned in the remaining 70%

    Usage:
        row = make_field_row("App Name :", self.app_name_field)
        row = make_field_row("Status :",   self.status_cb, self.status_label)
    """
    label = QLabel(label_text)
    label.setFont(_LABEL_FONT)

    label_layout = QHBoxLayout()
    label_layout.addStretch()
    label_layout.addWidget(label)

    field_layout = QHBoxLayout()
    for widget in field_widgets:
        field_layout.addWidget(widget)
    field_layout.addStretch()

    row = QHBoxLayout()
    row.addLayout(label_layout, 30)
    row.addLayout(field_layout, 70)
    return row
