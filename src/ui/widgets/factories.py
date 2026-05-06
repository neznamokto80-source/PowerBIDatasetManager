#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фабрики для создания переиспользуемых UI виджетов.
"""

from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QProgressBar, QTextEdit, QComboBox, QCheckBox, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush


def create_group_box(title: str, layout=None) -> QGroupBox:
    """
    Создает групповую рамку с заголовком.
    
    Args:
        title: Заголовок группы
        layout: Опциональный макет для установки (если None, создается QVBoxLayout)
    
    Returns:
        QGroupBox
    """
    group = QGroupBox(title)
    if layout is None:
        layout = QVBoxLayout()
    group.setLayout(layout)
    return group


def create_button(text: str, tooltip: str = None, callback=None) -> QPushButton:
    """
    Создает кнопку с текстом и опциональным обработчиком.
    
    Args:
        text: Текст кнопки
        tooltip: Всплывающая подсказка
        callback: Функция, вызываемая при нажатии
    
    Returns:
        QPushButton
    """
    btn = QPushButton(text)
    if tooltip:
        btn.setToolTip(tooltip)
    if callback:
        btn.clicked.connect(callback)
    return btn


def create_table_widget(columns: list, editable=False) -> QTableWidget:
    """
    Создает таблицу с заданными колонками.
    
    Args:
        columns: Список заголовков колонок
        editable: Разрешить редактирование ячеек
    
    Returns:
        QTableWidget
    """
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked if editable else QTableWidget.EditTrigger.NoEditTriggers)
    return table


def create_tree_widget(columns: list) -> QTreeWidget:
    """
    Создает дерево с заданными колонками.
    
    Args:
        columns: Список заголовков колонок
    
    Returns:
        QTreeWidget
    """
    tree = QTreeWidget()
    tree.setHeaderLabels(columns)
    tree.setAlternatingRowColors(True)
    tree.header().setStretchLastSection(True)
    return tree


def create_label(text: str, bold=False, color=None) -> QLabel:
    """
    Создает метку с текстом.
    
    Args:
        text: Текст метки
        bold: Жирный шрифт
        color: Цвет текста (строка "#RRGGBB" или QColor)
    
    Returns:
        QLabel
    """
    label = QLabel(text)
    if bold:
        font = label.font()
        font.setBold(True)
        label.setFont(font)
    if color:
        if isinstance(color, str):
            label.setStyleSheet(f"color: {color};")
        else:
            label.setStyleSheet(f"color: {color.name()};")
    return label


def create_progress_bar(indeterminate=False) -> QProgressBar:
    """
    Создает прогресс-бар.
    
    Args:
        indeterminate: Индетерминированный (бегущий) режим
    
    Returns:
        QProgressBar
    """
    bar = QProgressBar()
    if indeterminate:
        bar.setRange(0, 0)
    return bar


def create_text_edit(readonly=True) -> QTextEdit:
    """
    Создает текстовое поле.
    
    Args:
        readonly: Только для чтения
    
    Returns:
        QTextEdit
    """
    text_edit = QTextEdit()
    text_edit.setReadOnly(readonly)
    return text_edit


def create_combo_box(items: list = None) -> QComboBox:
    """
    Создает выпадающий список.
    
    Args:
        items: Список элементов для добавления
    
    Returns:
        QComboBox
    """
    combo = QComboBox()
    if items:
        combo.addItems(items)
    return combo


def create_check_box(text: str, checked=False) -> QCheckBox:
    """
    Создает флажок.
    
    Args:
        text: Текст флажка
        checked: Выбран ли по умолчанию
    
    Returns:
        QCheckBox
    """
    check = QCheckBox(text)
    check.setChecked(checked)
    return check


def create_tab_widget() -> QTabWidget:
    """
    Создает виджет вкладок.
    
    Returns:
        QTabWidget
    """
    return QTabWidget()