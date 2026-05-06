#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль цветового оформления приложения Power BI Monitor.
Содержит определения цветов для светлой и тёмной тем,
а также утилиты для применения темы к приложению.
"""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


class ThemeColors:
    """
    Класс, содержащий цветовые константы для тем приложения.
    Все цвета определены как статические свойства для удобства использования.
    """
    
    # ===== Цвета для тёмной темы =====
    
    # Основные цвета палитры
    DARK_WINDOW = QColor(53, 53, 53)
    DARK_WINDOW_TEXT = Qt.GlobalColor.white
    DARK_BASE = QColor(25, 25, 25)
    DARK_ALTERNATE_BASE = QColor(53, 53, 53)
    DARK_TOOLTIP_BASE = Qt.GlobalColor.black
    DARK_TOOLTIP_TEXT = Qt.GlobalColor.white
    DARK_TEXT = Qt.GlobalColor.white
    DARK_BUTTON = QColor(53, 53, 53)
    DARK_BUTTON_TEXT = Qt.GlobalColor.white
    DARK_BRIGHT_TEXT = Qt.GlobalColor.red
    DARK_LINK = QColor(42, 130, 218)
    DARK_HIGHLIGHT = QColor(42, 130, 218)
    DARK_HIGHLIGHTED_TEXT = Qt.GlobalColor.black
    
    # Цвета для выделения строк
    DARK_ERROR = QColor(255, 200, 200)  # светло-красный (одинаковый для обеих тем)
    DARK_DISABLED = QColor(60, 60, 60)  # тёмно-серый для выключенного автообновления
    DARK_NOT_SCHEDULED = QColor(170, 170, 40)  # тёмно-жёлтый для "не запланировано"
    
    # ===== Цвета для светлой темы =====
    
    # Основные цвета палитры (используется стандартная палитра Qt)
    # Определяем только цвета для выделения строк
    LIGHT_ERROR = QColor(255, 200, 200)  # светло-красный
    LIGHT_DISABLED = QColor(200, 200, 200)  # светло-серый для выключенного автообновления
    LIGHT_NOT_SCHEDULED = QColor(204, 204, 80)  # очень светло-жёлтый для "не запланировано"
    
    # ===== Утилитарные методы =====
    
    @staticmethod
    def get_error_color(theme="Светлая"):
        """
        Возвращает цвет для выделения ошибок.
        
        Args:
            theme: Название темы ("Светлая" или "Тёмная")
            
        Returns:
            QColor: Цвет для ошибок
        """
        return ThemeColors.DARK_ERROR  # Одинаковый для обеих тем
    
    @staticmethod
    def get_disabled_color(theme="Светлая"):
        """
        Возвращает цвет для выключенного автообновления.
        
        Args:
            theme: Название темы ("Светлая" или "Тёмная")
            
        Returns:
            QColor: Цвет для выключенного автообновления
        """
        if theme == "Тёмная":
            return ThemeColors.DARK_DISABLED
        else:
            # Возвращаем основной цвет для светлой темы
            return ThemeColors.LIGHT_DISABLED
    
    @staticmethod
    def get_disabled_color_alt(theme="Светлая"):
        """
        Возвращает альтернативный цвет для выключенного автообновления
        (используется в некоторых таблицах).
        
        Args:
            theme: Название темы ("Светлая" или "Тёмная")
            
        Returns:
            QColor: Альтернативный цвет для выключенного автообновления
        """
        # Используем тот же цвет, что и get_disabled_color
        return ThemeColors.get_disabled_color(theme)
    
    @staticmethod
    def get_not_scheduled_color(theme="Светлая"):
        """
        Возвращает цвет для строк, где следующее обновление не запланировано.
        
        Args:
            theme: Название темы ("Светлая" или "Тёмная")
            
        Returns:
            QColor: Цвет для "не запланировано"
        """
        if theme == "Тёмная":
            return ThemeColors.DARK_NOT_SCHEDULED
        else:
            return ThemeColors.LIGHT_NOT_SCHEDULED
    
    @staticmethod
    def get_dataset_background_color(dataset, theme="Светлая"):
        """
        Возвращает цвет фона для датасета.
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
            # Сравниваем как строку (приводим к нижнему регистру)
            if isinstance(next_refresh, str) and next_refresh.strip().lower() == 'не запланировано':
                return ThemeColors.get_not_scheduled_color(theme)

        # 5. Все остальные случаи — без подсветки
        return None
    
    @staticmethod
    def get_palette_for_theme(theme_name):
        """
        Создаёт и возвращает палитру для указанной темы.
        
        Args:
            theme_name: Название темы ("Светлая" или "Тёмная")
            
        Returns:
            QPalette: Палитра для применения к приложению
        """
        palette = QPalette()
        
        if theme_name == "Тёмная":
            palette.setColor(QPalette.ColorRole.Window, ThemeColors.DARK_WINDOW)
            palette.setColor(QPalette.ColorRole.WindowText, ThemeColors.DARK_WINDOW_TEXT)
            palette.setColor(QPalette.ColorRole.Base, ThemeColors.DARK_BASE)
            palette.setColor(QPalette.ColorRole.AlternateBase, ThemeColors.DARK_ALTERNATE_BASE)
            palette.setColor(QPalette.ColorRole.ToolTipBase, ThemeColors.DARK_TOOLTIP_BASE)
            palette.setColor(QPalette.ColorRole.ToolTipText, ThemeColors.DARK_TOOLTIP_TEXT)
            palette.setColor(QPalette.ColorRole.Text, ThemeColors.DARK_TEXT)
            palette.setColor(QPalette.ColorRole.Button, ThemeColors.DARK_BUTTON)
            palette.setColor(QPalette.ColorRole.ButtonText, ThemeColors.DARK_BUTTON_TEXT)
            palette.setColor(QPalette.ColorRole.BrightText, ThemeColors.DARK_BRIGHT_TEXT)
            palette.setColor(QPalette.ColorRole.Link, ThemeColors.DARK_LINK)
            palette.setColor(QPalette.ColorRole.Highlight, ThemeColors.DARK_HIGHLIGHT)
            palette.setColor(QPalette.ColorRole.HighlightedText, ThemeColors.DARK_HIGHLIGHTED_TEXT)
        else:
            # Для светлой темы используем стандартную палитру Qt
            palette = QApplication.style().standardPalette()
        
        return palette


def apply_theme_to_app(theme_name):
    """
    Применяет тему ко всему приложению.
    
    Args:
        theme_name: Название темы ("Светлая" или "Тёмная")
    """
    palette = ThemeColors.get_palette_for_theme(theme_name)
    QApplication.instance().setPalette(palette)