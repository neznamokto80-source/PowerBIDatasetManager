#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Темы оформления для GUI Power BI Dataset Monitor & Manager.
Стиль: Catppuccin Mocha (тёмная) / Catppuccin Latte (светлая),
адаптированный из D:\\git\\BO\\gui\\themes.py под виджеты этого проекта.

Содержит:
  - DARK_THEME / LIGHT_THEME — CSS-строки стилей
  - THEMES — словарь имя -> CSS
  - LOG_COLORS — цвета уровней логов для каждой темы
  - THEME_NAMES — список имён тем (для комбобокса)
"""

# ======================================================================
# ТЁМНАЯ ТЕМА — Catppuccin Mocha
# ======================================================================

DARK_THEME = """
QMainWindow { background-color: #1e1e2e; }
QWidget { background-color: #1e1e2e; color: #cdd6f4; }

/* --- Боковая панель / левая колонка --- */
#sidebar { background-color: #181825; border-right: 1px solid #313244; }
#sidebar QPushButton { background-color: transparent; color: #cdd6f4; border: none; border-radius: 8px; padding: 10px 14px; text-align: left; font-size: 13px; font-weight: 500; }
#sidebar QPushButton:hover { background-color: #313244; }
#sidebar QPushButton:checked { background-color: #45475a; color: #89b4fa; font-weight: 600; }
#sidebar_title { color: #89b4fa; font-size: 15px; font-weight: 700; padding: 16px; }
#sidebar_separator { background-color: #313244; max-height: 1px; min-height: 1px; }
#content_area { background-color: #1e1e2e; }
#log_frame { background-color: #181825; border-top: 1px solid #313244; }
#log_title { color: #6c7086; font-size: 11px; font-weight: 600; padding: 6px 12px; text-transform: uppercase; letter-spacing: 1px; }

/* --- Группы --- */
QGroupBox { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 10px; margin-top: 12px; padding-top: 20px; font-size: 13px; font-weight: 600; color: #cdd6f4; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 8px; color: #89b4fa; }

/* --- Метки --- */
QLabel { color: #cdd6f4; }
QLabel#subtitle { color: #6c7086; font-size: 12px; }
QLabel#section_title { color: #cdd6f4; font-size: 16px; font-weight: 700; }
QLabel#tooltip { color: #6c7086; font-size: 11px; font-style: italic; }

/* --- Кнопки --- */
QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 8px; padding: 8px 16px; font-size: 12px; }
QPushButton:hover { background-color: #45475a; border-color: #585b70; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled { background-color: #313244; color: #6c7086; border-color: #313244; }
QPushButton#primary { background-color: #89b4fa; color: #1e1e2e; border: none; border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; }
QPushButton#primary:hover { background-color: #74c7ec; }
QPushButton#primary:pressed { background-color: #89dceb; }
QPushButton#primary:disabled { background-color: #45475a; color: #6c7086; }
QPushButton#secondary { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 8px; padding: 8px 16px; font-size: 12px; }
QPushButton#secondary:hover { background-color: #45475a; border-color: #585b70; }
QPushButton#danger { background-color: #45475a; color: #f38ba8; border: 1px solid #f38ba8; border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; }
QPushButton#danger:hover { background-color: #f38ba8; color: #1e1e2e; }

/* --- Поля ввода --- */
QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 8px 12px; font-size: 13px; selection-background-color: #89b4fa; }
QLineEdit:focus { border-color: #89b4fa; }
QTextEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; font-size: 12px; selection-background-color: #89b4fa; }
QTextEdit:focus { border-color: #89b4fa; }
QPlainTextEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; font-size: 12px; }
QSpinBox, QDoubleSpinBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 4px 8px; font-size: 13px; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #89b4fa; }

/* --- Комбобокс --- */
QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 8px 12px; font-size: 13px; min-width: 120px; }
QComboBox:hover { border-color: #89b4fa; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; selection-background-color: #45475a; outline: none; }

/* --- Флажки и переключатели --- */
QCheckBox { color: #cdd6f4; spacing: 8px; font-size: 13px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #45475a; background-color: transparent; }
QCheckBox::indicator:checked { border-color: #89b4fa; background-color: #89b4fa; }
QCheckBox::indicator:hover { border-color: #89b4fa; }
QRadioButton { color: #cdd6f4; spacing: 8px; font-size: 13px; }
QRadioButton::indicator { width: 18px; height: 18px; border-radius: 10px; border: 2px solid #45475a; background-color: transparent; }
QRadioButton::indicator:checked { border-color: #89b4fa; background-color: #89b4fa; }
QRadioButton::indicator:hover { border-color: #89b4fa; }

/* --- Таблицы --- */
QTableWidget, QTableView { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 8px; gridline-color: #313244; font-size: 12px; selection-background-color: #45475a; }
QTableWidget::item, QTableView::item { padding: 6px; }
QTableWidget::item:selected, QTableView::item:selected { background-color: #45475a; color: #cdd6f4; }
QHeaderView::section { background-color: #181825; color: #89b4fa; border: none; border-bottom: 1px solid #313244; padding: 8px; font-weight: 600; font-size: 12px; }
QTableCornerButton::section { background-color: #181825; border: none; }

/* --- Дерево --- */
QTreeWidget, QTreeView { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 8px; font-size: 12px; selection-background-color: #45475a; }
QTreeWidget::item, QTreeView::item { padding: 6px; }
QTreeWidget::item:selected, QTreeView::item:selected { background-color: #45475a; color: #cdd6f4; }
QTreeWidget::branch, QTreeView::branch { background-color: transparent; }

/* --- Списки --- */
QListWidget, QListView { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 8px; font-size: 12px; selection-background-color: #45475a; outline: none; }
QListWidget::item, QListView::item { padding: 6px; }
QListWidget::item:selected, QListView::item:selected { background-color: #45475a; color: #cdd6f4; }

/* --- Вкладки --- */
QTabWidget::pane { border: 1px solid #313244; border-radius: 8px; background-color: #1e1e2e; }
QTabBar::tab { background-color: #181825; color: #6c7086; border: none; border-bottom: 2px solid transparent; padding: 10px 12px; font-size: 12px; font-weight: 500; min-width: 120px; }
QTabBar::tab:selected { color: #89b4fa; border-bottom-color: #89b4fa; }
QTabBar::tab:hover { color: #cdd6f4; background-color: #1e1e2e; }

/* --- Сплиттер --- */
QSplitter::handle { background-color: #313244; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QSplitter::handle:hover { background-color: #89b4fa; }

/* --- Прогресс-бар --- */
QProgressBar { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; text-align: center; font-size: 11px; }
QProgressBar::chunk { background-color: #89b4fa; border-radius: 5px; }

/* --- Статус-бар --- */
QStatusBar { background-color: #181825; color: #6c7086; border-top: 1px solid #313244; font-size: 11px; padding: 4px 12px; }
QStatusBar::item { border: none; }

/* --- Диалоги и окна сообщений --- */
QDialog { background-color: #1e1e2e; }
QMessageBox { background-color: #1e1e2e; }
QMessageBox QLabel { color: #cdd6f4; }

/* --- Подсказки --- */
QToolTip { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 6px; }

/* --- Поле лога --- */
#log_area { background-color: #11111b; border: none; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; color: #cdd6f4; padding: 8px; }
#log_title { color: #6c7086; font-size: 11px; font-weight: 600; padding: 6px 12px; text-transform: uppercase; letter-spacing: 1px; }

/* --- Прокрутки --- */
QScrollBar:vertical { background-color: #181825; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background-color: #45475a; min-height: 20px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background-color: #585b70; }
QScrollBar:horizontal { background-color: #181825; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background-color: #45475a; min-width: 20px; border-radius: 6px; }
QScrollBar::handle:horizontal:hover { background-color: #585b70; }
QScrollBar::add-line, QScrollBar::sub-line { background: none; border: none; height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; }
"""

# ======================================================================
# СВЕТЛАЯ ТЕМА — Catppuccin Latte
# ======================================================================

LIGHT_THEME = """
QMainWindow { background-color: #eff1f5; }
QWidget { background-color: #eff1f5; color: #4c4f69; }

/* --- Боковая панель / левая колонка --- */
#sidebar { background-color: #e6e9ef; border-right: 1px solid #ccd0da; }
#sidebar QPushButton { background-color: transparent; color: #4c4f69; border: none; border-radius: 8px; padding: 10px 14px; text-align: left; font-size: 13px; font-weight: 500; }
#sidebar QPushButton:hover { background-color: #ccd0da; }
#sidebar QPushButton:checked { background-color: #bcc0cc; color: #1e66f5; font-weight: 600; }
#sidebar_title { color: #1e66f5; font-size: 15px; font-weight: 700; padding: 16px; }
#sidebar_separator { background-color: #ccd0da; max-height: 1px; min-height: 1px; }
#content_area { background-color: #eff1f5; }
#log_frame { background-color: #e6e9ef; border-top: 1px solid #ccd0da; }
#log_title { color: #9ca0b0; font-size: 11px; font-weight: 600; padding: 6px 12px; text-transform: uppercase; letter-spacing: 1px; }

/* --- Группы --- */
QGroupBox { background-color: #eff1f5; border: 1px solid #ccd0da; border-radius: 10px; margin-top: 12px; padding-top: 20px; font-size: 13px; font-weight: 600; color: #4c4f69; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 8px; color: #1e66f5; }

/* --- Метки --- */
QLabel { color: #4c4f69; }
QLabel#subtitle { color: #9ca0b0; font-size: 12px; }
QLabel#section_title { color: #4c4f69; font-size: 16px; font-weight: 700; }
QLabel#tooltip { color: #9ca0b0; font-size: 11px; font-style: italic; }

/* --- Кнопки --- */
QPushButton { background-color: #e6e9ef; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 8px; padding: 8px 16px; font-size: 12px; }
QPushButton:hover { background-color: #ccd0da; border-color: #bcc0cc; }
QPushButton:pressed { background-color: #bcc0cc; }
QPushButton:disabled { background-color: #e6e9ef; color: #9ca0b0; border-color: #e6e9ef; }
QPushButton#primary { background-color: #1e66f5; color: #ffffff; border: none; border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; }
QPushButton#primary:hover { background-color: #2a7ae9; }
QPushButton#primary:pressed { background-color: #1a5cd4; }
QPushButton#primary:disabled { background-color: #ccd0da; color: #9ca0b0; }
QPushButton#secondary { background-color: #e6e9ef; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 8px; padding: 8px 16px; font-size: 12px; }
QPushButton#secondary:hover { background-color: #ccd0da; border-color: #bcc0cc; }
QPushButton#danger { background-color: #e6e9ef; color: #d20f39; border: 1px solid #d20f39; border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; }
QPushButton#danger:hover { background-color: #d20f39; color: #ffffff; }

/* --- Поля ввода --- */
QLineEdit { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 6px; padding: 8px 12px; font-size: 13px; selection-background-color: #1e66f5; }
QLineEdit:focus { border-color: #1e66f5; }
QTextEdit { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 6px; padding: 6px; font-size: 12px; selection-background-color: #1e66f5; }
QTextEdit:focus { border-color: #1e66f5; }
QPlainTextEdit { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 6px; padding: 6px; font-size: 12px; }
QSpinBox, QDoubleSpinBox { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 6px; padding: 4px 8px; font-size: 13px; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #1e66f5; }

/* --- Комбобокс --- */
QComboBox { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 6px; padding: 8px 12px; font-size: 13px; min-width: 120px; }
QComboBox:hover { border-color: #1e66f5; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; selection-background-color: #e6e9ef; outline: none; }

/* --- Флажки и переключатели --- */
QCheckBox { color: #4c4f69; spacing: 8px; font-size: 13px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #bcc0cc; background-color: transparent; }
QCheckBox::indicator:checked { border-color: #1e66f5; background-color: #1e66f5; }
QCheckBox::indicator:hover { border-color: #1e66f5; }
QRadioButton { color: #4c4f69; spacing: 8px; font-size: 13px; }
QRadioButton::indicator { width: 18px; height: 18px; border-radius: 10px; border: 2px solid #bcc0cc; background-color: transparent; }
QRadioButton::indicator:checked { border-color: #1e66f5; background-color: #1e66f5; }
QRadioButton::indicator:hover { border-color: #1e66f5; }

/* --- Таблицы --- */
QTableWidget, QTableView { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 8px; gridline-color: #ccd0da; font-size: 12px; selection-background-color: #e6e9ef; }
QTableWidget::item, QTableView::item { padding: 6px; }
QTableWidget::item:selected, QTableView::item:selected { background-color: #e6e9ef; color: #4c4f69; }
QHeaderView::section { background-color: #e6e9ef; color: #1e66f5; border: none; border-bottom: 1px solid #ccd0da; padding: 8px; font-weight: 600; font-size: 12px; }
QTableCornerButton::section { background-color: #e6e9ef; border: none; }

/* --- Дерево --- */
QTreeWidget, QTreeView { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 8px; font-size: 12px; selection-background-color: #e6e9ef; }
QTreeWidget::item, QTreeView::item { padding: 6px; }
QTreeWidget::item:selected, QTreeView::item:selected { background-color: #e6e9ef; color: #4c4f69; }
QTreeWidget::branch, QTreeView::branch { background-color: transparent; }

/* --- Списки --- */
QListWidget, QListView { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 8px; font-size: 12px; selection-background-color: #e6e9ef; outline: none; }
QListWidget::item, QListView::item { padding: 6px; }
QListWidget::item:selected, QListView::item:selected { background-color: #e6e9ef; color: #4c4f69; }

/* --- Вкладки --- */
QTabWidget::pane { border: 1px solid #ccd0da; border-radius: 8px; background-color: #eff1f5; }
QTabBar::tab { background-color: #e6e9ef; color: #9ca0b0; border: none; border-bottom: 2px solid transparent; padding: 10px 12px; font-size: 12px; font-weight: 500; min-width: 120px; }
QTabBar::tab:selected { color: #1e66f5; border-bottom-color: #1e66f5; }
QTabBar::tab:hover { color: #4c4f69; background-color: #eff1f5; }

/* --- Сплиттер --- */
QSplitter::handle { background-color: #ccd0da; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QSplitter::handle:hover { background-color: #1e66f5; }

/* --- Прогресс-бар --- */
QProgressBar { background-color: #e6e9ef; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 6px; text-align: center; font-size: 11px; }
QProgressBar::chunk { background-color: #1e66f5; border-radius: 5px; }

/* --- Статус-бар --- */
QStatusBar { background-color: #e6e9ef; color: #9ca0b0; border-top: 1px solid #ccd0da; font-size: 11px; padding: 4px 12px; }
QStatusBar::item { border: none; }

/* --- Диалоги и окна сообщений --- */
QDialog { background-color: #eff1f5; }
QMessageBox { background-color: #eff1f5; }
QMessageBox QLabel { color: #4c4f69; }

/* --- Подсказки --- */
QToolTip { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 4px; padding: 6px; }

/* --- Поле лога --- */
#log_area { background-color: #ffffff; border: none; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; color: #4c4f69; padding: 8px; }
#log_title { color: #9ca0b0; font-size: 11px; font-weight: 600; padding: 6px 12px; text-transform: uppercase; letter-spacing: 1px; }

/* --- Прокрутки --- */
QScrollBar:vertical { background-color: #e6e9ef; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background-color: #bcc0cc; min-height: 20px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background-color: #a6adc8; }
QScrollBar:horizontal { background-color: #e6e9ef; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background-color: #bcc0cc; min-width: 20px; border-radius: 6px; }
QScrollBar::handle:horizontal:hover { background-color: #a6adc8; }
QScrollBar::add-line, QScrollBar::sub-line { background: none; border: none; height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; }
"""

# ======================================================================
# СЛОВАРИ ТЕМ
# ======================================================================

THEMES = {
    "Тёмная (Catppuccin Mocha)": DARK_THEME,
    "Светлая (Catppuccin Latte)": LIGHT_THEME,
}

# Имена тем по порядку (для комбобоксов)
THEME_NAMES = list(THEMES.keys())

# Имя темы, используемой по умолчанию
DEFAULT_THEME_NAME = "Тёмная (Catppuccin Mocha)"

# ======================================================================
# ЦВЕТА ЛОГА ДЛЯ РАЗНЫХ ТЕМ
# ======================================================================

LOG_COLORS = {
    "dark": {"ok": "#a6e3a1", "error": "#f38ba8", "warning": "#f9e2af", "info": "#6c7086"},
    "light": {"ok": "#40a02b", "error": "#d20f39", "warning": "#df8e1d", "info": "#9ca0b0"},
}


def get_log_colors(theme_name: str = DEFAULT_THEME_NAME):
    """Возвращает словарь цветов логов для заданной темы."""
    if "Светлая" in theme_name:
        return LOG_COLORS["light"]
    return LOG_COLORS["dark"]