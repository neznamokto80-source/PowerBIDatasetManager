#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль экспорта таблиц в буфер обмена для вставки в Excel.

Предоставляет:
- TableExportFilter — фильтр событий клавиатуры для перехвата Ctrl+A
  (выделить все строки) и Ctrl+C (копирование в буфер обмена);
- install_table_export — установка фильтра на таблицу;
- copy_table_to_clipboard — копирование содержимого таблицы (TSV,
  с заголовками колонок, только видимые колонки);
- select_all_rows — выделение всех строк таблицы;
- add_export_menu_items — добавление пунктов «Выделить все» и
  «Копировать в Excel» в контекстное меню.
"""

import logging

from PyQt5.QtCore import QObject, Qt, QEvent
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMenu, QTableWidget, QAction

logger = logging.getLogger(__name__)

# Атрибут, под которым фильтр хранится на таблице (чтобы не был собран GC)
_FILTER_ATTR = '_table_export_filter'


def _sanitize_cell(text):
    """
    Заменяет символы табуляции и переносов строк в ячейке на пробелы,
    чтобы не ломать TSV-разметку при вставке в Excel.
    """
    if not text:
        return ''
    return text.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')


def copy_table_to_clipboard(table):
    """
    Копирует содержимое таблицы в буфер обмена в формате TSV:
    заголовки колонок + данные. Включаются только видимые колонки.

    Args:
        table: Таблица QTableWidget

    Returns:
        Количество скопированных строк данных (без учёта заголовка)
    """
    if table is None:
        return 0

    visible_cols = [c for c in range(table.columnCount()) if not table.isColumnHidden(c)]

    lines = []

    # Заголовки видимых колонок
    headers = []
    for col in visible_cols:
        header_item = table.horizontalHeaderItem(col)
        headers.append(header_item.text() if header_item else '')
    lines.append('\t'.join(headers))

    # Данные
    row_count = table.rowCount()
    for row in range(row_count):
        cells = []
        for col in visible_cols:
            item = table.item(row, col)
            cells.append(_sanitize_cell(item.text() if item else ''))
        lines.append('\t'.join(cells))

    text = '\n'.join(lines)

    if text:
        try:
            QApplication.clipboard().setText(text)
        except Exception as e:
            logger.error("Ошибка записи в буфер обмена: %s", e)

    return row_count


def select_all_rows(table):
    """Выделяет все строки таблицы."""
    if table is None:
        return
    table.selectAll()


def _notify_copied(table, count):
    """
    Выводит сообщение о результате копирования в статус-бар главного окна.
    """
    try:
        window = table.window()
        if window is not None and hasattr(window, 'status_bar') and window.status_bar is not None:
            if count > 0:
                window.status_bar.showMessage("Скопировано строк: %d" % count, 3000)
            else:
                window.status_bar.showMessage("Таблица пуста — скопированы только заголовки", 3000)
    except Exception as e:
        logger.debug("Не удалось показать сообщение о копировании: %s", e)


def copy_table_to_clipboard_and_notify(table):
    """Копирует таблицу в буфер обмена и выводит сообщение в статус-бар."""
    count = copy_table_to_clipboard(table)
    _notify_copied(table, count)
    return count


class TableExportFilter(QObject):
    """
    Фильтр событий клавиатуры для таблицы:

    - Ctrl+A — выделить все строки таблицы;
    - Ctrl+C — скопировать содержимое таблицы в буфер обмена
      (с заголовками, только видимые колонки).
    """

    def __init__(self, table, parent=None):
        super(TableExportFilter, self).__init__(parent)
        self._table = table

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key_event = event
            modifiers = key_event.modifiers()

            if modifiers == Qt.ControlModifier:
                if key_event.key() == Qt.Key_A:
                    select_all_rows(self._table)
                    return True
                elif key_event.key() == Qt.Key_C:
                    copy_table_to_clipboard_and_notify(self._table)
                    return True

        return super(TableExportFilter, self).eventFilter(obj, event)


def install_table_export(table):
    """
    Устанавливает обработчик Ctrl+A / Ctrl+C на таблицу.
    Безопасно вызывать повторно — фильтр не дублируется.
    """
    if table is None:
        return

    if getattr(table, _FILTER_ATTR, None) is not None:
        return

    filter_obj = TableExportFilter(table)
    table.installEventFilter(filter_obj)
    setattr(table, _FILTER_ATTR, filter_obj)


def add_export_menu_items(menu, table):
    """
    Добавляет в контекстное меню пункты «Выделить все» и «Копировать в Excel».

    Args:
        menu: Меню, в которое добавляются пункты
        table: Таблица, для которой выполняются действия
    """
    if menu is None or table is None:
        return

    menu.addSeparator()

    select_action = QAction("Выделить все", menu)
    select_action.setShortcut(QKeySequence.SelectAll)  # Ctrl+A
    select_action.triggered.connect(lambda: select_all_rows(table))
    menu.addAction(select_action)

    copy_action = QAction("Копировать в Excel", menu)
    copy_action.setShortcut(QKeySequence.Copy)  # Ctrl+C
    copy_action.triggered.connect(lambda: copy_table_to_clipboard_and_notify(table))
    menu.addAction(copy_action)