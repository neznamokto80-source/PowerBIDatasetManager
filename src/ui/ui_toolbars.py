#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль панелей инструментов пользовательского интерфейса.
"""

from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction


class UIToolbars:
    """Класс для создания панелей инструментов."""
    
    def __init__(self, main_window):
        """
        Инициализация с ссылкой на главное окно.
        
        Args:
            main_window: Экземпляр PowerBIMonitorUI
        """
        self.main = main_window
    
    def create_toolbar(self):
        """Создает панель инструментов."""
        toolbar = QToolBar("Основные инструменты")
        self.main.addToolBar(toolbar)
        
        # Действия
        connect_action = QAction("Подключить", self.main)
        connect_action.triggered.connect(self.main.connect_to_powerbi)
        toolbar.addAction(connect_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction("Обновить данные", self.main)
        refresh_action.triggered.connect(self.main.refresh_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        auth_action = QAction("Аутентификация", self.main)
        auth_action.triggered.connect(self.main.reauthenticate)
        toolbar.addAction(auth_action)
        
        settings_action = QAction("Настройки", self.main)
        settings_action.triggered.connect(self.main.open_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        help_action = QAction("Справка", self.main)
        help_action.triggered.connect(self.main.show_help)
        toolbar.addAction(help_action)
        
        return toolbar