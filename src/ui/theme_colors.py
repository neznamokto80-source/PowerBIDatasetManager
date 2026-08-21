#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль цветового оформления приложения Power BI Monitor.

Применяет CSS-темы Catppuccin (Mocha / Latte) через setStyleSheet,
адаптированные из проекта SAP BO Data Collector.

Содержит:
  - ThemeColors — класс с цветами для подсветки строк таблиц
  - Применение темы ко всему приложению через apply_theme_to_app
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor

from .themes import (
    THEMES,
    THEME_NAMES,
    DEFAULT_THEME_NAME,
    get_log_colors,
)


class ThemeColors:
    """
    Класс, содержащий цветовые константы для тем приложения.

    Отвечает за подсветку строк таблиц (ошибки, выключенное автообновление,
    отсутствие расписания). Сами темы (CSS) лежат в модуле themes.
    """

    # ===== Цвета для тёмной темы (Catppuccin Mocha) =====

    # Цвета для выделения строк
    DARK_ERROR = "#f38ba8"          # красный (розовый) для ошибок
    DARK_DISABLED = "#313244"       # тёмно-серый для выключенного автообновления
    DARK_NOT_SCHEDULED = "#f9e2af"  # жёлтый для "не запланировано"

    # ===== Цвета для светлой темы (Catppuccin Latte) =====

    LIGHT_ERROR = "#d20f39"         # красный для ошибок
    LIGHT_DISABLED = "#ccd0da"      # светло-серый для выключенного автообновления
    LIGHT_NOT_SCHEDULED = "#df8e1d" # жёлтый для "не запланировано"

    # ===== Утилитарные методы =====

    @staticmethod
    def get_error_color(theme="Светлая"):
        """Возвращает QColor для выделения ошибок."""
        if theme == "Тёмная":
            return QColor(ThemeColors.DARK_ERROR)
        return QColor(ThemeColors.LIGHT_ERROR)

    @staticmethod
    def get_disabled_color(theme="Светлая"):
        """Возвращает QColor для выключенного автообновления."""
        if theme == "Тёмная":
            return QColor(ThemeColors.DARK_DISABLED)
        return QColor(ThemeColors.LIGHT_DISABLED)

    @staticmethod
    def get_disabled_color_alt(theme="Светлая"):
        """Возвращает альтернативный цвет для выключенного автообновления."""
        return ThemeColors.get_disabled_color(theme)

    @staticmethod
    def get_not_scheduled_color(theme="Светлая"):
        """Возвращает QColor для строк, где следующее обновление не запланировано."""
        if theme == "Тёмная":
            return QColor(ThemeColors.DARK_NOT_SCHEDULED)
        return QColor(ThemeColors.LIGHT_NOT_SCHEDULED)

    @staticmethod
    def get_dataset_background_color(dataset, theme="Светлая"):
        """
        Возвращает цвет фона для датасета (строка в таблице).

        Логика приоритета:
          1. Ошибка (status failed/error) -> красный
          2. Автообновление выключено     -> серый
          3. Автообновление включено, но "не запланировано" -> жёлтый
          4. Все остальные случаи         -> None (без подсветки)
        """
        # 1. Сначала ошибки (красный)
        status = dataset.get('status', 'unknown').lower()
        if status in ('failed', 'error'):
            return ThemeColors.get_error_color(theme)

        # 2. Получаем статус автообновления
        refresh_schedule = dataset.get('refresh_schedule', {})
        enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None

        # 3. Если автообновление выключено — серый
        if enabled is False:
            return ThemeColors.get_disabled_color(theme)

        # 4. Если автообновление включено — проверяем, есть ли расписание
        if enabled is True:
            next_refresh = dataset.get('nextRefreshTime', '')
            if isinstance(next_refresh, str) and next_refresh.strip().lower() == 'не запланировано':
                return ThemeColors.get_not_scheduled_color(theme)

        # 5. Все остальные случаи — без подсветки
        return None


def get_active_theme():
    """
    Возвращает имя активной темы по умолчанию.
    Если на приложении уже применена одна из известных тем, возвращает её.
    """
    app = QApplication.instance()
    if app is not None:
        sheet = app.styleSheet()
        for name, css in THEMES.items():
            if sheet == css:
                return name
    return DEFAULT_THEME_NAME


def apply_theme_to_app(theme_name=None):
    """
    Применяет тему ко всему приложению через setStyleSheet.

    Args:
        theme_name: Имя темы (см. THEME_NAMES). Если None — применяется тема по умолчанию.
    """
    if theme_name is None:
        theme_name = DEFAULT_THEME_NAME
    if theme_name not in THEMES:
        theme_name = DEFAULT_THEME_NAME

    app = QApplication.instance()
    if app is None:
        return

    # Важно: Fusion-стиль обеспечивает корректную работу кастомных QSS
    app.setStyle("Fusion")
    app.setStyleSheet(THEMES[theme_name])

    # Обновляем стиль всех виджетов
    for widget in app.topLevelWidgets():
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()