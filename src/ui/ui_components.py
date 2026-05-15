#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный модуль компонентов пользовательского интерфейса.
Агрегирует функциональность из специализированных модулей.
"""

from .ui_panels import UIPanels
from .ui_toolbars import UIToolbars


class UIComponents:
    """
    Фасадный класс для создания UI компонентов.
    Предполагается, что экземпляр этого класса будет использоваться
    внутри главного окна PowerBIMonitorUI.
    """
    
    def __init__(self, main_window):
        """
        Инициализация с ссылкой на главное окно.
        
        Args:
            main_window: Экземпляр PowerBIMonitorUI
        """
        self.main = main_window
        self.panels = UIPanels(main_window)
        self.toolbars = UIToolbars(main_window)
    
    def create_toolbar(self):
        """Создает панель инструментов."""
        return self.toolbars.create_toolbar()
    
    def create_button_panel(self):
        """Создает панель с отдельными кнопками."""
        return self.toolbars.create_button_panel()
    
    def create_left_panel(self):
        """Создает левую панель навигации."""
        return self.panels.create_left_panel()
    
    def create_center_panel(self):
        """Создает центральную панель с информацией."""
        return self.panels.create_center_panel()
    
    def create_right_panel(self):
        """Создает правую панель с действиями."""
        # Используем метод из panels, если он там есть, иначе создаем заглушку
        if hasattr(self.panels, 'create_right_panel'):
            return self.panels.create_right_panel()
        else:
            # Заглушка - возвращаем пустой виджет
            from PyQt6.QtWidgets import QWidget
            QWidget()
    
    def create_logs_panel(self):
        """Создает панель логов для правой стороны."""
        # Используем метод из panels, если он там есть
        if hasattr(self.panels, 'create_logs_panel'):
            return self.panels.create_logs_panel()
        else:
            # Заглушка - возвращаем пустой виджет
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
            panel = QWidget()
            layout = QVBoxLayout(panel)
            layout.addWidget(QLabel("Логи (метод create_logs_panel не найден)"))
            return panel
            layout = QVBoxLayout(panel)
            layout.addWidget(QLabel("Правая панель не реализована"))
            layout.addStretch()
            return panel
    
    def create_overview_tab(self):
        """Создает вкладку обзора."""
        return self.panels.create_overview_tab()
    
    def create_details_tab(self):
        """Создает вкладку детальной информации."""
        return self.panels.create_details_tab()
    
    def create_history_tab(self):
        """Создает вкладку истории обновлений."""
        return self.panels.create_history_tab()
    
    def create_logs_tab(self):
        """Создает вкладку логов."""
        return self.panels.create_logs_tab()