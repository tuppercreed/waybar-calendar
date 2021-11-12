import sys
from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt
from lib.switch import Switch


class Dialog(QDialog):
    """Dialog."""

    _sample_items = ["asdffs", "Thing two", "3rd goes here", "Numba 4", "Fifth and most elegant"]
    _switches = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QDialog")
        # self.setModal(True)
        # self.setGeometry(200, 200, 200, 200)
        self.setFixedSize(235, 235)
        dlgLayout = QVBoxLayout()
        formLayout = QFormLayout()

        for item in self._sample_items:
            self._switches[item] = Switch(thumb_radius=11, track_radius=8)
            self._switches[item].toggled.connect(lambda c: print("toggled", c))
            formLayout.addRow(f"{item}:", self._switches[item])

        dlgLayout.addLayout(formLayout)
        btns = QDialogButtonBox()
        btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        dlgLayout.addWidget(btns)
        self.setLayout(dlgLayout)

        btns.accepted.connect(self.accepted)
        btns.rejected.connect(self.rejected)

    def accepted(self):
        print("Accepted")
        self.close()

    def rejected(self):
        print("Rejected")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = Dialog()
    dlg.show()
    sys.exit(app.exec())
