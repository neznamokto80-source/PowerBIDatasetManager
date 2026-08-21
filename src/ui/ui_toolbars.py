#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль панелей инструментов пользовательского интерфейса.
"""

from PyQt5.QtWidgets import QToolBar, QWidget, QHBoxLayout, QPushButton, QAction
from PyQt5.QtCore import Qt

from .widgets import create_button


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
        connect_cloud_action = QAction("Подключить Power BI Service (облако)", self.main)
        connect_cloud_action.triggered.connect(self.main.connect_to_powerbi)
        toolbar.addAction(connect_cloud_action)

        connect_server_action = QAction("Подключить Power BI Report Server", self.main)
        connect_server_action.triggered.connect(self.main.connect_to_powerbi_report_server)
        toolbar.addAction(connect_server_action)

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
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Кнопка "Подключить Power BI Service (облако)"
        connect_cloud_btn = create_button(
            "Подключить Power BI Service (облако)",
            callback=self.main.connect_to_powerbi,
            style="primary",
            fixed_height=36,
        )
        layout.addWidget(connect_cloud_btn)

        # Кнопка "Подключить Power BI Report Server"
        connect_server_btn = create_button(
            "Подключить Power BI Report Server",
            callback=self.main.connect_to_powerbi_report_server,
            style="secondary",
            fixed_height=36,
        )
        layout.addWidget(connect_server_btn)

        # Кнопка "Обновить"
        refresh_btn = create_button(
            "Обновить",
            callback=self.main.refresh_data,
            style="secondary",
            fixed_height=36,
        )
        layout.addWidget(refresh_btn)

        # Растягиваемое пространство между левыми и правыми кнопками
        layout.addStretch()

        # Кнопка "Тестовые данные"
        test_data_btn = create_button(
            "Тестовые данные",
            callback=self.main.load_test_data,
            fixed_height=36,
        )
        layout.addWidget(test_data_btn)

        # Кнопка "Справка"
        help_btn = create_button(
            "Справка",
            callback=self.main.show_help,
            fixed_height=36,
        )
        layout.addWidget(help_btn)

        return panel