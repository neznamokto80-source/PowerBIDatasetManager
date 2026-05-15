#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчик логов для вывода в QTextEdit.
"""

import logging
from PyQt6.QtCore import QObject, pyqtSignal


class QTextEditLogHandler(logging.Handler, QObject):
    """Обработчик логов, который отправляет сообщения в QTextEdit через сигнал."""
    
    log_signal = pyqtSignal(str)
    
    def __init__(self, text_edit=None):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.text_edit = text_edit
        self.log_signal.connect(self._append_log)
        # Атрибут, необходимый для корректного завершения logging.shutdown
        self.flushOnClose = False
    
    def set_text_edit(self, text_edit):
        """Установить QTextEdit для вывода логов."""
        self.text_edit = text_edit
    
    def emit(self, record):
        """Переопределение emit для отправки сообщения в UI."""
        try:
            msg = self.format(record)
            self.log_signal.emit(msg)
        except Exception:
            self.handleError(record)
    
    def close(self):
        """Корректно закрыть обработчик, отключив сигнал."""
        try:
            self.log_signal.disconnect()
        except:
            pass
        self.text_edit = None
        logging.Handler.close(self)
    
    def _append_log(self, msg):
        """Добавить сообщение в QTextEdit (выполняется в основном потоке)."""
        if self.text_edit is not None:
            self.text_edit.append(msg)
            # Прокрутка вниз
            cursor = self.text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.text_edit.setTextCursor(cursor)
            self.text_edit.ensureCursorVisible()