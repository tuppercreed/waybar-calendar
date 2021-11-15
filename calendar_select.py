import sys, json, sqlite3, os
from typing import NamedTuple
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication,
    QCommonStyle,
    QFormLayout,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QScrollArea,
    QWidget,
    QGroupBox,
    QLabel,
)
from PyQt5.QtCore import Qt
from lib.switch import Switch

from cal import Calendar, Calendars


class Dialog(QDialog):
    """Dialog."""

    _sample_items = ["asdffs", "Thing two", "3rd goes here", "Numba 4", "Fifth and most elegant"]
    _switches = {}

    def __init__(self, calendars=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QDialog")
        # self.setModal(True)
        # self.setGeometry(200, 200, 200, 200)
        self.setFixedSize(300, 450)

        self.calendars = calendars

        formContainer = QWidget()
        formLayout = QFormLayout()

        formLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        formLayout.maximumSize()

        for cal in self.calendars:
            self._switches[cal.id] = Switch(thumb_radius=11, track_radius=8)
            if cal.active:
                self._switches[cal.id].setChecked(True)
            # self._switches[item].toggled.connect(lambda c: print("toggled", c))
            label = QLabel(f"{cal.name}:")
            label.setMaximumWidth(200)
            formLayout.addRow(label, self._switches[cal[0]])

        formContainer.setLayout(formLayout)
        formContainer.setMaximumWidth(275)

        scroll = QScrollArea()
        scroll.setWidget(formContainer)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(400)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

        btns = QDialogButtonBox()
        btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout.addWidget(btns)
        # self.setLayout(dlgLayout)

        btns.accepted.connect(self.accepted)
        btns.rejected.connect(self.rejected)

    def accepted(self):
        results = {key: switch.isChecked() for key, switch in self._switches.items()}

        overwrites = []
        for i, cal in enumerate(self.calendars):
            if cal.active != results[cal.id]:
                overwrites.append(
                    (
                        i,
                        Calendar(
                            id=cal.id,
                            name=cal.name,
                            description=cal.description,
                            time_zone=cal.time_zone,
                            active=results[cal.id],
                        ),
                    )
                )

        for overwrite in overwrites:
            calendars[overwrite[0]] = overwrite[1]
        if len(overwrites) > 0:
            calendars.write()

        print("Accepted")
        self.close()

    def rejected(self):
        print("Rejected")
        self.close()


if __name__ == "__main__":
    calendars = Calendars()

    app = QApplication(sys.argv)
    app.setStyle("breeze")
    dlg = Dialog(calendars=calendars)
    dlg.show()
    sys.exit(app.exec())
