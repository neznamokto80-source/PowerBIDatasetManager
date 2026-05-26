#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы подключения и инициализации Power BI.
"""

import logging

from PyQt6.QtWidgets import QMessageBox

from src.core.dependencies import DependencyManager
from src.core.powerbi_client import PowerBIClient
from src.core.refresh_manager import RefreshManager
from src.integration.ui_integration import UIIntegration, UIDataProvider

logger = logging.getLogger(__name__)


class ConnectionMethods:
    """Методы для подключения к Power BI и инициализации бэкенда."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы подключения.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def initialize_backend(self):
        """Инициализация бэкенда приложения (без автоматического подключения)."""
        try:
            # Проверяем и устанавливаем зависимости
            DependencyManager.ensure_dependencies()
            
            # Создаем клиент и менеджер (но не аутентифицируемся)
            # Путь для сохранения сырых данных: C:\temp\work\PBI_DATA\data
            # Для отключения сохранения сырых данных установить debug_data_path = None
            debug_data_path =  None #r"C:\temp\work\PBI_DATA\data"
            self.main_window.client = PowerBIClient(debug_data_path=debug_data_path)
            self.main_window.refresh_manager = RefreshManager(self.main_window.client)
            self.main_window.integration = UIIntegration(
                self.main_window.client,
                self.main_window.refresh_manager
            )
            self.main_window.data_provider = UIDataProvider(self.main_window.integration)
            
            # Устанавливаем режим работы
            self.main_window.current_mode = 'service'
            
            self.main_window.log_message("Система готова к подключению. Нажмите кнопку 'Подключить'.")
            self.main_window.status_bar.showMessage("Готов к подключению")
            
            # Очищаем UI, показываем состояние "не подключено"
            self.main_window.update_ui_for_disconnected_state()
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка инициализации: {e}")
            self.main_window.status_bar.showMessage("Ошибка инициализации", 5000)
            QMessageBox.critical(
                self.main_window, 
                "Ошибка инициализации",
                f"Не удалось инициализировать систему:\n{str(e)}"
            )
    
    def connect_to_powerbi(self):
        """Подключение к Power BI."""
        try:
            # Проверяем, что клиент правильного типа
            if not isinstance(self.main_window.client, PowerBIClient):
                raise TypeError(
                    f"Клиент имеет неверный тип {type(self.main_window.client).__name__}. "
                    f"Ожидается PowerBIClient. Возможно, вы пытаетесь подключиться к Power BI Service "
                    f"в режиме Power BI Report Server. Переключите режим."
                )
            
            self.main_window.log_message("Попытка подключения к Power BI...")
            self.main_window.status_bar.showMessage("Аутентификация...")
            
            # Аутентификация
            self.main_window.client.authenticate()
            self.main_window.log_message(
                f"✓ Аутентификация успешна (метод: {self.main_window.client._auth_method})"
            )
            
            # Загрузка рабочих областей
            self.main_window.workspaces = self.main_window.client.get_workspaces()
            self.main_window.log_message(f"✓ Загружено рабочих областей: {len(self.main_window.workspaces)}")
            
            # Обновление UI
            self.main_window.update_ui_for_connected_state()
            
            # Загрузка датасетов (опционально)
            if self.main_window.workspaces:
                self.main_window.current_workspace = self.main_window.workspaces[0].get('id')
                self.main_window.load_datasets()
            
            self.main_window.status_bar.showMessage("Подключено", 3000)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка подключения: {e}")
            self.main_window.status_bar.showMessage("Ошибка подключения", 5000)
            QMessageBox.critical(
                self.main_window, 
                "Ошибка подключения",
                f"Не удалось подключиться к Power BI:\n{str(e)}"
            )