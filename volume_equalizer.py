from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt


class QVolumeEq(QtWidgets.QWidget):
    def __init__(self, start_color, end_color, bg_color=(0, 0, 0, 255), value=100,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        self.bg_color = QtGui.QColor(*bg_color)
        self.start_color = QtGui.QColor(*start_color)
        self.end_color = QtGui.QColor(*end_color)

        self.brush = QtGui.QBrush(self.bg_color)
        self.brush.setStyle(Qt.SolidPattern)

        self.value = value

    def setValue(self, value):
        """Функция передаёт значение в value"""
        self.value = value

    def value(self):
        """Статичная функция, возвращает значение value"""
        return self.value

    def paintEvent(self, event):
        try:
            qp = QtGui.QPainter()
            qp.begin(self)

            # Заполняем задний фон эквалайзера
            qp.fillRect(self.rect(), self.bg_color)

            # Создаём градиент
            self.gradient = QtGui.QLinearGradient(0, 0, self.width(), self.height())
            self.gradient.setColorAt(0, self.start_color)
            self.gradient.setColorAt(1, self.end_color)

            # Отрисовка
            qp.setBrush(QtGui.QBrush(self.gradient))
            qp.drawRect(-1, -1, self.width() * self.value / 100, self.height() + 1)

            qp.end()
        except Exception as e:
            print(e.__class__.__name__, ': ', e, sep='')
