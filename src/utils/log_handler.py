#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчик логов для вывода в QTextEdit с цветовой кодировкой.

Цвета уровней берутся из темы Catppuccin (см. src/ui/themes.py), как в проекте
SAP BO Data Collector.
"""

import logging

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor, QTextCursor

from ..ui.themes import get_log_colors, DEFAULT_THEME_NAME


class QTextEditLogHandler(logging.Handler, QObject):
    """Обработчик логов, который отправляет сообщения в QTextEdit через сигнал."""

    log_signal = pyqtSignal(str, str)  # (текст, уровень)

    def __init__(self, text_edit=None, theme_name=DEFAULT_THEME_NAME):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.text_edit = text_edit
        self.theme_name = theme_name
        self.log_colors = get_log_colors(theme_name)
        self.log_signal.connect(self._append_log)
        # Атрибут, необходимый для корректного завершения logging.shutdown
        self.flushOnClose = False

    def set_text_edit(self, text_edit):
        """Установить QTextEdit для вывода логов."""
        self.text_edit = text_edit

    def set_theme(self, theme_name: str):
        """Обновляет палитру цветов логов при смене темы интерфейса."""
        self.theme_name = theme_name
        self.log_colors = get_log_colors(theme_name)

    @staticmethod
    def _level_to_key(levelno: int) -> str:
        """Преобразует числовой уровень logging в ключ палитры LOG_COLORS."""
        if levelno >= logging.ERROR:
            return "error"
        if levelno == logging.WARNING:
            return "warning"
        return "info"

    def emit(self, record):
        """Переопределение emit для отправки сообщения в UI."""
        try:
            msg = self.format(record)
            level_key = self._level_to_key(record.levelno)
            self.log_signal.emit(msg, level_key)
        except Exception:
            self.handleError(record)

    def close(self):
        """Корректно закрыть обработчик, отключив сигнал."""
        try:
            self.log_signal.disconnect()
        except Exception:
            pass
        self.text_edit = None
        logging.Handler.close(self)

    def _append_log(self, msg, level_key):
        """Добавить сообщение в QTextEdit с цветом по уровню (в основном потоке)."""
        if self.text_edit is None:
            return

        color_hex = self.log_colors.get(level_key, self.log_colors.get("info", "#6c7086"))
        self.text_edit.setTextColor(QColor(color_hex))
        self.text_edit.append(msg)
        self.text_edit.setTextColor(QColor(self.log_colors.get("info", "#6c7086")))

        # Прокрутка вниз
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()