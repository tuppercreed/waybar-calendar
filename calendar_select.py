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


class Calendar(NamedTuple):
    id: str
    summary: str
    active: bool


class sql_calendar:
    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.path = f"{dir_path}/cal.db"

    def _connect(self):
        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()

    def read(self):
        self._connect()
        results = list(self.cur.execute("SELECT id, summary, active FROM calendars;"))

        results = [Calendar(id=result[0], summary=result[1], active=bool(result[2])) for result in results]

        self.con.close()
        return results

    def write(self, active, inactive):
        self._connect()
        active_string = ",".join(["?"] * len(active))
        self.cur.execute(f"UPDATE calendars SET active=1 WHERE id IN ({active_string})", active)
        inactive_string = ",".join(["?"] * len(inactive))
        self.cur.execute(f"UPDATE calendars SET active=0 WHERE id IN ({inactive_string})", inactive)

        self.con.commit()
        self.con.close()


class Dialog(QDialog):
    """Dialog."""

    _sample_items = ["asdffs", "Thing two", "3rd goes here", "Numba 4", "Fifth and most elegant"]
    _switches = {}

    def __init__(self, names=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QDialog")
        # self.setModal(True)
        # self.setGeometry(200, 200, 200, 200)
        self.setFixedSize(300, 450)

        formContainer = QWidget()
        formLayout = QFormLayout()

        formLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        formLayout.maximumSize()

        for item in names:
            self._switches[item[0]] = Switch(thumb_radius=11, track_radius=8)
            if item[2]:
                self._switches[item[0]].setChecked(True)
            # self._switches[item].toggled.connect(lambda c: print("toggled", c))
            label = QLabel(f"{item[1]}:")
            label.setMaximumWidth(200)
            formLayout.addRow(label, self._switches[item[0]])

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

        checked = [id for id, switch in self._switches.items() if switch.isChecked()]
        not_checked = [id for id, switch in self._switches.items() if not switch.isChecked()]

        cal = sql_calendar()
        cal.write(checked, not_checked)

        print("Accepted")
        self.close()

    def rejected(self):
        print("Rejected")
        self.close()


if __name__ == "__main__":
    cal = sql_calendar()
    names = cal.read()

    app = QApplication(sys.argv)
    app.setStyle("breeze")
    dlg = Dialog(names=names)
    dlg.show()
    sys.exit(app.exec())
