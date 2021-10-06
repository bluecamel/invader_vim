from typing import Any
from PyQt5.QtCore import QObject, pyqtSignal
from pynput.keyboard import HotKey, KeyCode, Listener, Key, Controller
from pynput._util.xorg import display_manager

keyboard = Controller()

ALPHA_LOWER = 'abcdefghijklmnopqrstuvwxyz'
ALPHA_UPPER = ALPHA_LOWER.upper()


class KeySequence(QObject):
    _activate = pyqtSignal(name='activate')
    _activated = pyqtSignal(name='activated')

    def __init__(self, sequence, on_activate):
        super(QObject, self).__init__()
        self.sequence = sequence
        self.on_activate = on_activate
        self.activate.connect(self.do_activate)

    def check(self, sequence):
        if self.sequence == sequence:
            self.activate.emit()

    def do_activate(self):
        self.on_activate()
        self.activated.emit()


class QHotKey(HotKey, QObject):
    _activate = pyqtSignal(name='activate')

    def __init__(self, keys, on_activate):
        self.on_activate = on_activate
        QObject.__init__(self)
        HotKey.__init__(self, keys, self.activate.emit)
        self.activate.connect(self.do_activate)

    def do_activate(self):
        self.on_activate()


class DynamicHotKeyAndKeySequenceListener(Listener, QObject):
    _key_sequence_activated = pyqtSignal(name='key_sequence_activated')
    _pass_press = pyqtSignal(KeyCode, name='pass_press')

    def __init__(self, *args, **kwargs):
        Listener.__init__(self,
            on_press=self.on_press,
            on_release=self.on_release,
            *args,
            **kwargs)
        QObject.__init__(self)

        self.hotkeys = {}
        self.key_sequences = []
        self.current_sequence = ''
        self.suppressed = False

    def add_hotkey(self, key, hotkey):
        self.hotkeys[key] = QHotKey(HotKey.parse(key), hotkey)

    def add_key_sequence(self, key_sequence):
        self.key_sequences.append(key_sequence)
        key_sequence.activated.connect(self.clear_key_sequences)
        key_sequence.activated.connect(self.key_sequence_activated)

        if not self.suppressed:
            with display_manager(keyboard._display) as dm:
                self._suppress_start(dm)
                self.suppressed = True

    def clear_key_sequences(self):
        key_sequences_copy = self.key_sequences.copy()
        for key_sequence in key_sequences_copy:
            self.remove_key_sequence(key_sequence)
        self.current_sequence = ''

        if self.suppressed:
            with display_manager(keyboard._display) as dm:
                self._suppress_stop(dm)
                self.suppressed = False

    def key_char(self, key):
        char = None
        try:
            char = key.char.upper()
        except AttributeError as error:
            pass
        except Exception as error:
            pass

        return char

    def on_press(self, key):
        for hotkey in self.hotkeys.values():
            hotkey.press(self.canonical(key))
        
        char = self.key_char(key)
        if not char:
            if key == Key.backspace:
                self.current_sequence = self.current_sequence[0:-1]
            return

        if len(self.key_sequences) > 0:
            self.current_sequence += char
            # print('current_sequence: {}'.format(self.current_sequence))

            for key_sequence in self.key_sequences:
                key_sequence.check(self.current_sequence)

    def on_release(self, key):
        for hotkey in self.hotkeys.values():
            hotkey.release(self.canonical(key))

    def remove_hotkey(self, key):
        self.hotkeys.pop(key, None)

    def remove_key_sequence(self, key_sequence):
        self.key_sequences.remove(key_sequence)
        key_sequence.activate.disconnect()
