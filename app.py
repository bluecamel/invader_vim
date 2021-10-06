import sys
import math
from enum import Enum
import typing

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QLabel, QMainWindow, QMenu, QSystemTrayIcon, QWidget

from atspi import get_active_window
from keyboard import ALPHA_UPPER, DynamicHotKeyAndKeySequenceListener, KeySequence
from overlay import Overlay, OverlayAction


class Mode(Enum):
    CLICKABLE = 0
    PRESSABLES = 1
    SELECTABLES = 2


class GIR(QtCore.QObject):
    _activate = QtCore.pyqtSignal(Mode, name='activate')
    _quit = QtCore.pyqtSignal(name='quit')

    def __init__(self):
        super().__init__()
        self.init_hot_keys()
        self._activate.connect(self.on_activate)

    def create_overlay(self, actionable_objects, key_sequence_keys):
        overlay_actions = self.create_overlay_actions(actionable_objects, key_sequence_keys)
        self.overlay = Overlay(overlay_actions)
        self.hotkeys.key_sequence_activated.connect(self.on_destroy)

    def create_overlay_actions(self, actionable_objects, key_sequence_keys):
        if len(actionable_objects) != len(key_sequence_keys):
            raise AttributeError('Counts of objects and sequences do not match.')

        overlay_actions = []
        for i in range(0, len(actionable_objects)):
            sequence = key_sequence_keys[i]
            actionable_object = actionable_objects[i]
            overlay_actions.append(
                OverlayAction(sequence, actionable_object.position, actionable_object.size))

        return overlay_actions

    def create_key_sequences(self, actionable_objects):
        alpha_length = len(ALPHA_UPPER)
        objects_length = len(actionable_objects)

        key_sequence_keys = []

        for i in range(0, objects_length):
            actionable_object = actionable_objects[i]

            sequence = ''
            if objects_length < alpha_length:
                sequence = ALPHA_UPPER[i]
            else:
                alpha_1 = math.floor(i / alpha_length)
                alpha_2 = i % alpha_length
                sequence = '{}{}'.format(ALPHA_UPPER[alpha_1], ALPHA_UPPER[alpha_2])

            self.hotkeys.add_key_sequence(KeySequence(sequence, actionable_object.do_action))
            key_sequence_keys.append(sequence)

        return key_sequence_keys

    def init_hot_keys(self):
        self.hotkeys = DynamicHotKeyAndKeySequenceListener()
        self.hotkeys.add_hotkey('<ctrl>+<alt>+c', lambda: self.activate.emit(Mode.CLICKABLE))
        self.hotkeys.add_hotkey('<ctrl>+<alt>+p', lambda: self.activate.emit(Mode.PRESSABLES))
        self.hotkeys.add_hotkey('<ctrl>+<alt>+s', lambda: self.activate.emit(Mode.SELECTABLES))
        self.hotkeys.add_hotkey('<ctrl>+<alt>+q', self.quit.emit)
        self.hotkeys.start()

    def on_activate(self, mode):
        self.hotkeys.clear_key_sequences()

        active_window = get_active_window()

        actionable_objects = []
        if mode == Mode.CLICKABLE:
            actionable_objects = active_window.clickable_objects()
        elif mode == Mode.PRESSABLES:
            actionable_objects = active_window.pressable_objects()
        elif mode == Mode.SELECTABLES:
            actionable_objects = active_window.selectable_objects()

        if not actionable_objects:
            return

        key_sequence_keys = self.create_key_sequences(actionable_objects)
        self.create_overlay(actionable_objects, key_sequence_keys)

    def on_destroy(self):
        self.overlay.destroy()


class InvaderVim(QApplication):
    def __init__(self, argv: typing.List[str]):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        self.widget = QWidget()
        self.init()
    
    def init(self):
        self.init_menu()
        self.init_tray()
        self.init_gir()

    def init_menu(self):
        self.menu = QMenu(self.widget)

        quit = QAction("Quit", self.widget)
        quit.triggered.connect(self.quit)
        self.menu.addAction(quit)

    def init_gir(self):
        self.GIR = GIR()
        self.GIR.quit.connect(self.quit)

    def init_tray(self):
        self.icon = QIcon("icon.png")
        self.tray = QSystemTrayIcon(self.icon, self.widget)
        self.tray.setVisible(True)
        self.tray.setContextMenu(self.menu)


if __name__ == "__main__":
    invader = InvaderVim(sys.argv)
    sys.exit(invader.exec_())
