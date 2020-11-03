import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui  import *
from PyQt5.QtCore import *

class Example(QMainWindow):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.cols = len(self.data[0])
        self.row, self.col = 0, 0
        self.cell = []

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        self.label = QLabel(alignment=Qt.AlignCenter)

        self.tableWidget = QTableWidget(0, 4)
        self.tableWidget.setHorizontalHeaderLabels(["Id", "Test name", "Owner", "Script source"])
        self.tableWidget.cellClicked.connect(self.cellClick)
        self.setTableWidget()

        self.btnRun = QPushButton("btnRun")
        self.btnRun.clicked.connect(self.run_selected_test)

        lay = QGridLayout(centralWidget)
        lay.addWidget(self.label, 0, 0)
        lay.addWidget(self.tableWidget, 1, 0)
        lay.addWidget(self.btnRun, 2, 0)

    def run_selected_test(self):
        self.cell = []
        for col in range(self.cols):
            self.cell.append(self.tableWidget.item(self.row, col).text())        # <---
            print(self.cell)
        self.label.setText("{}".format(" {}  ; "*self.cols).format(*self.cell))

    def cellClick(self, row, col):
        self.row = row
        self.col = col

    def setTableWidget(self):
        for r, (_id, _name, _owner, _script) in enumerate(self.data):
            it_id     = QTableWidgetItem(_id)
            it_name   = QTableWidgetItem(_name)
            it_owner  = QTableWidgetItem(_owner)
            it_script = QTableWidgetItem(_script)

            self.tableWidget.insertRow(self.tableWidget.rowCount())
            for c, item in enumerate((it_id, it_name, it_owner, it_script)):
                self.tableWidget.setItem(r, c, item)


data = [("1", "Login",       "1", "test_login_s"),
        ("2", "Logout",      "1", "test_logout_s"),
        ("3", "User > Edit", "1", "test_user_edit_s")]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example(data)
    ex.setGeometry(300, 150, 450, 200)
    ex.show()
    sys.exit(app.exec_())