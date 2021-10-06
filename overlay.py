
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QMainWindow


class OverlayAction(object):
    def __init__(self, sequence, position, size):
        self.sequence = sequence
        self.position = position
        self.size = size

    def create_label(self, parent):
        label = QLabel(self.sequence, parent)
        label.setStyleSheet("\n".join(["color: white;"
            "border : 3px solid green;",
            "border-top-left-radius : 35px;",
            "border-top-right-radius : 20px; ",
            "border-bottom-left-radius : 50px; ",
            "border-bottom-right-radius : 10px"]))

        # print('sequence: {} position: {} size: {}'.format(self.sequence, self.position, self.size))

        # TODO(bkd): get taskbar height from?
        label.move(self.position[0], self.position[1] - 26)
        label.resize(self.size[0], self.size[1])

        return label


class Overlay(QMainWindow):
    def __init__(self, actions):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.showMaximized()
        self.actions = actions
        self.labels = []
        self.show_actions()
    
    def show_actions(self):
        for action in self.actions:
            label = action.create_label(self)
            self.labels.append(label)
            label.show()
