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
        
        help_action = QAction("Справка", self.main)
        help_action.triggered.connect(self.main.show_help)
        toolbar.addAction(help_action)
        
        return toolbar

    def create_button_panel(self):
        """Создает панель с отдельными кнопками (замена панели инструментов)."""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
        
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Кнопка "Подключить"
        connect_btn = QPushButton("Подключить")
        connect_btn.clicked.connect(self.main.connect_to_powerbi)
        layout.addWidget(connect_btn)
        
        # Кнопка "Обновить" (добавлена по требованию)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.main.refresh_data)
        layout.addWidget(refresh_btn)
        
        # Растягиваемое пространство между левыми и правыми кнопками
        layout.addStretch()
        
        # Кнопка "Тестовые данные"
        test_data_btn = QPushButton("Тестовые данные")
        test_data_btn.clicked.connect(self.main.load_test_data)
        layout.addWidget(test_data_btn)
        
        # Кнопка "Справка"
        help_btn = QPushButton("Справка")
        help_btn.clicked.connect(self.main.show_help)
        layout.addWidget(help_btn)
        
        return panel