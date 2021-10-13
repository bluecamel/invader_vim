import sys
import math
from enum import Enum
import typing
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QLabel, QMainWindow, QMenu, QSystemTrayIcon, QWidget

from atspi import ClickableObject, PressableObject, Registry, SelectableObject
from keyboard import ALPHA_UPPER, DynamicHotKeyAndKeySequenceListener, KeySequence
from logger import create_logger
from overlay import Overlay, OverlayAction


class Mode(Enum):
    PAUSED = 0
    CLICKABLE = 1
    PRESSABLES = 2
    SELECTABLES = 3


class GIR(QObject):
    _activate = pyqtSignal(Mode, name='activate')
    _quit = pyqtSignal(name='quit')

    def __init__(self, logger):
        QObject.__init__(self)
        self.active_window = None
        self.logger = logger
        self.logger.info('GIR initializing')
        self.overlay = None
        self.init_hot_keys()
        self.init_atspi_registry()
        self.activate.connect(self.on_activate)
        self.logger.info('GIR reporting for duty')

    def create_overlay(self, actionable_objects, key_sequence_keys):
        overlay_actions = self.create_overlay_actions(actionable_objects, key_sequence_keys)
        self.overlay = Overlay(overlay_actions)
        self.hotkeys.key_sequence_activated.connect(self.destroy_overlay)

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

    def destroy_overlay(self, keep_active_window=False):
        if not keep_active_window:
            self.active_window = None

        if self.overlay:
            self.overlay.destroy()

    def init_atspi_registry(self):
        self.registry = Registry(self.logger)

    def init_hot_keys(self):
        self.hotkeys = DynamicHotKeyAndKeySequenceListener()
        self.hotkeys.add_hotkey('<ctrl>+<alt>+c', lambda: self.activate.emit(Mode.CLICKABLE))
        self.hotkeys.add_hotkey('<ctrl>+<alt>+p', lambda: self.activate.emit(Mode.PRESSABLES))
        self.hotkeys.add_hotkey('<ctrl>+<alt>+s', lambda: self.activate.emit(Mode.SELECTABLES))
        self.hotkeys.add_hotkey('<ctrl>+<alt>+f', lambda: self.activate.emit(Mode.PAUSED))
        self.hotkeys.add_hotkey('<ctrl>+<alt>+q', self.on_quit)
        self.hotkeys.start()

    def on_activate(self, mode):
        self.logger.info({'message': 'activate', 'mode': mode})

        self.destroy_overlay(keep_active_window=True)
        self.hotkeys.clear_key_sequences()

        actionable_object_types = []
        if mode == Mode.CLICKABLE:
            actionable_object_types.append(ClickableObject)
        elif mode == Mode.PRESSABLES:
            actionable_object_types.append(PressableObject)
        elif mode == Mode.SELECTABLES:
            actionable_object_types.append(SelectableObject)
        elif mode == Mode.PAUSED:
            self.destroy_overlay()
            return

        if not self.active_window:
            self.active_window = self.registry.active_window()

        if not self.active_window:
            self.logger.warning('Active window not found.')
            return

        actionable_objects = self.active_window.filter_actionable_objects(actionable_object_types)

        if not actionable_objects:
            self.logger.warning('No actionable objects found in the active window.')
            return

        self.logger.info({'message': 'Found actionable objects.', 'count': len(actionable_objects)})

        key_sequence_keys = self.create_key_sequences(actionable_objects)
        self.create_overlay(actionable_objects, key_sequence_keys)

    def on_quit(self):
        self.destroy_overlay()
        self.quit.emit()


class InvaderVim(QApplication):
    def __init__(self, argv: typing.List[str]):
        QApplication.__init__(self, argv)
        self.setQuitOnLastWindowClosed(False)
        self.logger = create_logger()
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
        self.GIR = GIR(self.logger)
        self.GIR.quit.connect(self.quit)

    def init_tray(self):
        self.icon = QIcon("icon.png")
        self.tray = QSystemTrayIcon(self.icon, self.widget)
        self.tray.setVisible(True)
        self.tray.setContextMenu(self.menu)


if __name__ == "__main__":
    invader = InvaderVim(sys.argv)
    sys.exit(invader.exec_())
