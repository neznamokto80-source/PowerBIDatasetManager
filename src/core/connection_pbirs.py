#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы подключения и инициализации Power BI Report Server.
"""

import logging

from PyQt6.QtWidgets import QMessageBox, QInputDialog

from src.core.dependencies import DependencyManager
from src.core.powerbi_report_server_client import PowerBIReportServerClient
from src.core.refresh_manager_pbirs import PBIRSRefreshManager
from src.integration.ui_integration import UIIntegration, UIDataProvider

logger = logging.getLogger(__name__)


class PBIRSConnectionMethods:
    """Методы для подключения к Power BI Report Server и инициализации бэкенда."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы подключения.

        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def initialize_backend_pbirs(self, server_url: str, username: str = None, password: str = None):
        """
        Инициализация бэкенда приложения для Power BI Report Server.
        
        Args:
            server_url: URL сервера PBIRS (например, http://PBIRSServer/Reports)
            username: Имя пользователя для NTLM аутентификации (опционально)
            password: Пароль для NTLM аутентификации (опционально)
        """
        try:
            # Проверяем и устанавливаем зависимости
            DependencyManager.ensure_dependencies()
            
            # Создаем клиент для PBIRS
            debug_data_path = None  # Можно включить для отладки
            # Проверяем, включен ли чекбокс сохранения сырых логов
            if hasattr(self.main_window, 'debug_checkbox') and self.main_window.debug_checkbox.isChecked():
                debug_data_path = "debug"
            self.main_window.client = PowerBIReportServerClient(
                server_url=server_url,
                username=username,
                password=password,
                debug_data_path=debug_data_path
            )
            
            # Создаем менеджер обновлений для PBIRS
            self.main_window.refresh_manager = PBIRSRefreshManager(self.main_window.client)
            
            # Используем существующую интеграцию UI (может потребоваться адаптация)
            self.main_window.integration = UIIntegration(
                self.main_window.client,
                self.main_window.refresh_manager
            )
            self.main_window.data_provider = UIDataProvider(self.main_window.integration)
            
            # Устанавливаем режим работы
            self.main_window.current_mode = 'server'
            
            self.main_window.log_message(f"Система готова к подключению к Power BI Report Server: {server_url}")
            self.main_window.status_bar.showMessage("Готов к подключению к PBIRS")
            
            # Очищаем UI, показываем состояние "не подключено"
            self.main_window.update_ui_for_disconnected_state()
            
        except ImportError as e:
            self.main_window.log_message(f"✗ Ошибка зависимостей: {e}")
            self.main_window.status_bar.showMessage("Ошибка зависимостей", 5000)
            QMessageBox.critical(
                self.main_window, 
                "Ошибка зависимостей",
                f"Не удалось загрузить необходимые библиотеки для работы с Power BI Report Server:\n{str(e)}\n\n"
                f"Установите библиотеку requests_ntlm2: pip install requests_ntlm2"
            )
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка инициализации PBIRS: {e}")
            self.main_window.status_bar.showMessage("Ошибка инициализации PBIRS", 5000)
            QMessageBox.critical(
                self.main_window, 
                "Ошибка инициализации",
                f"Не удалось инициализировать систему для Power BI Report Server:\n{str(e)}"
            )
    
    def connect_to_powerbi_report_server(self):
        """Подключение к Power BI Report Server с запросом параметров."""
        try:
            # Запрос URL сервера
            server_url, ok = QInputDialog.getText(
                self.main_window, 
                "Подключение к Power BI Report Server",
                "Введите URL сервера (например, http://PBIRSServer/Reports):"
            )
            
            if not ok or not server_url:
                return
            
            # Запрос учетных данных (опционально)
            username = None
            password = None
            
            use_credentials, ok = QInputDialog.getItem(
                self.main_window,
                "Аутентификация",
                "Использовать учетные данные?",
                ["Использовать текущего пользователя Windows", "Ввести логин и пароль"],
                0,
                False
            )
            
            if ok and use_credentials == "Ввести логин и пароль":
                username, ok1 = QInputDialog.getText(
                    self.main_window,
                    "Учетные данные",
                    "Имя пользователя (DOMAIN\\username):"
                )
                if ok1 and username:
                    password, ok2 = QInputDialog.getText(
                        self.main_window,
                        "Учетные данные",
                        "Пароль:",
                        QInputDialog.TextEchoMode.Password
                    )
                    if not ok2 or not password:
                        return
            
            self.main_window.log_message(f"Попытка подключения к Power BI Report Server: {server_url}")
            self.main_window.status_bar.showMessage("Подключение к PBIRS...")
            
            # Инициализация бэкенда
            self.initialize_backend_pbirs(server_url, username, password)
            
            # Проверка подключения
            if self.main_window.client.test_connection():
                self.main_window.log_message(f"✓ Подключение к Power BI Report Server успешно")
                
                # Обновление UI для подключенного состояния
                self.main_window.update_ui_for_connected_state()
                
                # Загрузка отчетов
                self.load_pbirs_reports()
                
                self.main_window.status_bar.showMessage("Подключено к PBIRS", 3000)
            else:
                self.main_window.log_message(f"✗ Не удалось подключиться к серверу")
                self.main_window.status_bar.showMessage("Ошибка подключения к PBIRS", 5000)
                QMessageBox.warning(
                    self.main_window,
                    "Ошибка подключения",
                    f"Не удалось подключиться к серверу: {server_url}"
                )
                self.main_window.update_ui_for_disconnected_state()
                
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка подключения к PBIRS: {e}")
            self.main_window.status_bar.showMessage("Ошибка подключения к PBIRS", 5000)
            QMessageBox.critical(
                self.main_window,
                "Ошибка",
                f"Ошибка при подключении к Power BI Report Server:\n{str(e)}"
            )
            self.main_window.update_ui_for_disconnected_state()
    
    def load_pbirs_reports(self):
        """Загружает отчеты Power BI Report Server."""
        if not self.main_window.client or not hasattr(self.main_window.client, 'get_powerbi_reports'):
            return
        
        try:
            reports = self.main_window.client.get_powerbi_reports()
            self.main_window.log_message(f"✓ Загружено отчетов Power BI Report Server: {len(reports)}")
            
            # Сохраняем отчеты для использования в UI
            self.main_window.pbirs_reports = reports
            
            # TODO: Адаптировать UI для отображения отчетов вместо датасетов
            # Временно выводим информацию в лог
            for i, report in enumerate(reports[:5]):  # Первые 5 отчетов
                name = report.get('Name', 'Без имени')
                report_id = report.get('Id', 'N/A')
                self.main_window.log_message(f"  {i+1}. {name} (ID: {report_id[:20]}...)")
            
            if len(reports) > 5:
                self.main_window.log_message(f"  ... и еще {len(reports) - 5} отчетов")
                
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка при загрузке отчетов PBIRS: {e}")


if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    print("Тестирование модуля PBIRS Connection Methods...")
    print("Модуль готов к использованию.")