from PyQt5.QtWidgets import QMainWindow
from PyQt5 import uic
from PyQt5.QtGui import QIcon


class QAbout(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('icons/about.ui', self)
        self.setFixedSize(353, 202)
        self.setWindowTitle('О программе: DJust Audio Player')
        self.setWindowIcon(QIcon('icons/icon.ico'))
        self.show()


class QHelp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('icons/help.ui', self)
        self.setFixedSize(330, 460)
        self.setWindowTitle('Справка: DJust Audio Player')
        self.setWindowIcon(QIcon('icons/icon.ico'))
        self.show()
