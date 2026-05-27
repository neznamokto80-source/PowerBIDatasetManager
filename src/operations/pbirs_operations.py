#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для операций, специфичных для Power BI Report Server.
Содержит методы для подключения, загрузки отчётов, управления папками и источниками данных.
"""

import logging
import traceback
from typing import List, Dict, Any

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt

from src.core.powerbi_report_server_client import PowerBIReportServerClient
from src.core.connection_manager import ConnectionManager
from src.operations.base_operations import BaseOperations
from src.utils.pbirs_data_enricher import enrich_reports_list, extract_data_sources_for_table

logger = logging.getLogger(__name__)


class PBIRSOperations(BaseOperations):
    """Операции для работы с Power BI Report Server."""
    
    def __init__(self, main_window):
        """
        Инициализация операций PBIRS.
        
        Args:
            main_window: Экземпляр главного окна
        """
        super().__init__(main_window)
    
    def initialize_backend_pbirs(self, server_url: str, username: str = None, password: str = None):
        """
        Инициализация бэкенда для Power BI Report Server.
        
        Args:
            server_url: Базовый URL сервера (например, http://PBIRSServer/Reports)
            username: Имя пользователя для NTLM аутентификации
            password: Пароль для NTLM аутентификации
        """
        try:
            # Создаем клиент PBIRS
            client = PowerBIReportServerClient(
                server_url=server_url,
                username=username,
                password=password,
                use_session=True,
                debug_data_path=self.main_window.debug_data_path if hasattr(self.main_window, 'debug_data_path') else None
            )
            
            # Проверяем подключение
            if not client.test_connection():
                raise ConnectionError("Не удалось подключиться к серверу PBIRS")
            
            # Сохраняем клиент в главном окне
            self.main_window.client = client
            self.main_window.refresh_manager = None  # Для PBIRS менеджер обновлений не используется
            self.main_window.data_provider = None
            
            # Инициализируем менеджер подключений (синглтон)
            self.main_window.connection_manager = ConnectionManager()
            
            # Устанавливаем режим server
            self.main_window.current_mode = 'server'
            
            # Обновляем UI
            self.main_window.update_ui_for_connected_state()
            self.main_window._update_workspace_group_title()
            self.main_window.update_tabs_visibility()
            
            self.main_window.log_message(f"✓ Подключено к Power BI Report Server: {server_url}")
            
            # Автоматически загружаем отчеты после подключения
            self.load_pbirs_reports()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации бэкенда PBIRS: {e}")
            self.main_window.log_message(f"✗ Ошибка подключения к PBIRS: {e}")
            QMessageBox.critical(self.main_window, "Ошибка подключения", 
                                f"Не удалось подключиться к Power BI Report Server:\n{str(e)}")
            return False
    
    def connect_to_powerbi_report_server(self):
        """Подключение к Power BI Report Server с запросом параметров."""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        # Запрашиваем URL сервера
        server_url, ok = QInputDialog.getText(
            self.main_window,
            "Подключение к Power BI Report Server",
            "Введите URL сервера (например, http://PBIRSServer/Reports):",
            QLineEdit.EchoMode.Normal,
            "http://localhost/Reports"
        )
        
        if not ok or not server_url.strip():
            return
        
        # Запрашиваем тип авторизации через выпадающий список
        auth_options = ["Авторизация Windows", "Ввести данные"]
        auth_choice, ok_auth = QInputDialog.getItem(
            self.main_window,
            "Тип авторизации",
            "Выберите тип авторизации:",
            auth_options,
            0,  # индекс по умолчанию (Авторизация Windows)
            False  # не редактируемый
        )
        
        if not ok_auth:
            return  # пользователь отменил
        
        username = None
        password = None
        
        if auth_choice == "Ввести данные":
            # Запрашиваем учетные данные
            username, ok1 = QInputDialog.getText(
                self.main_window, "Учетные данные", "Имя пользователя (домен\\пользователь):"
            )
            if ok1 and username:
                password, ok2 = QInputDialog.getText(
                    self.main_window, "Учетные данные", "Пароль:", QLineEdit.EchoMode.Password
                )
                if not ok2:
                    password = None
        
        # Инициализируем бэкенд
        return self.initialize_backend_pbirs(server_url.strip(), username, password)
    
    def load_pbirs_reports(self):
        """Загружает отчеты Power BI Report Server с расширенными данными (источники, расписания)."""
        if not self.main_window.client or not hasattr(self.main_window.client, 'get_extended_reports'):
            return
        
        try:
            # Используем новый метод для получения расширенных данных
            reports = self.main_window.client.get_extended_reports(include_ssrs=True)
            self.main_window.log_message(f"✓ Загружено отчетов Power BI Report Server: {len(reports)}")
            
            # Обогащаем данные отчетов (добавляем вычисляемые поля)
            enriched_reports = enrich_reports_list(reports)
            
            # Сохраняем обогащенные отчеты для использования в UI
            self.main_window.pbirs_reports = enriched_reports
            
            # Извлекаем папки и обновляем комбобокс
            folders = self._extract_folders_from_reports(enriched_reports)
            self.main_window.pbirs_folders = folders
            # Вызываем метод обновления UI (если он существует)
            if hasattr(self.main_window, 'update_folders_combo'):
                self.main_window.update_folders_combo(folders)
            else:
                # Логируем папки
                self.main_window.log_message(f"  Найдено папок: {len(folders)}")
                for folder in folders[:10]:
                    self.main_window.log_message(f"    - {folder}")
            
            # Временно выводим информацию в лог
            for i, report in enumerate(enriched_reports[:5]):  # Первые 5 отчетов
                name = report.get('Name', 'Без имени')
                report_id = report.get('Id', 'N/A')
                sources = report.get('DataSourcesBrief', 'Нет источников')
                self.main_window.log_message(f"  {i+1}. {name} (ID: {report_id[:20]}...) - {sources}")
            
            if len(enriched_reports) > 5:
                self.main_window.log_message(f"  ... и еще {len(enriched_reports) - 5} отчетов")
            
            # Обновляем таблицу отчётов в UI с учетом текущего выбора папки и фильтра по названию
            if hasattr(self.main_window, 'update_pbirs_reports_table'):
                # Определяем текущую выбранную папку (если комбобокс существует)
                selected_folder = None
                if hasattr(self.main_window, 'workspace_combo') and self.main_window.workspace_combo.count() > 0:
                    selected_folder = self.main_window.workspace_combo.currentText()
                # Определяем текущий фильтр по названию (если поле существует)
                name_filter = None
                if hasattr(self.main_window, 'pbirs_report_name_filter'):
                    name_filter = self.main_window.pbirs_report_name_filter.text()
                self.main_window.update_pbirs_reports_table(enriched_reports, selected_folder, name_filter)
                self.main_window.log_message("✓ Таблица отчётов PBIRS обновлена")
            
            # Формируем данные для вкладки источников
            sources_data = []
            for report in enriched_reports:
                folder = report.get('FolderDisplay', '/')
                report_name = report.get('Name', 'Без имени')
                data_sources = report.get('DataSourcesList', [])
                for ds in data_sources:
                    if ds is None:
                        continue
                    # Извлекаем имя источника данных, гарантируя, что это строка
                    ds_name = ds.get('Name', 'Без имени')
                    if not isinstance(ds_name, str):
                        ds_name = str(ds_name)
                    source_item = {
                        'Folder': folder,
                        'ReportName': report_name,
                        'DataSource': ds_name,
                        'ConnectionString': ds.get('ConnectionString', ''),
                        'DataSourceType': ds.get('DataSourceType', 'Unknown')
                    }
                    sources_data.append(source_item)
            
            # Сохраняем данные источников для использования в UI
            self.main_window.pbirs_sources_data = sources_data
            
            # Обновляем таблицу источников в UI
            if hasattr(self.main_window, 'update_pbirs_sources_table'):
                # Определяем текущие фильтры (если поля существуют)
                report_filter = None
                source_filter = None
                if hasattr(self.main_window, 'pbirs_sources_report_filter'):
                    report_filter = self.main_window.pbirs_sources_report_filter.text()
                if hasattr(self.main_window, 'pbirs_sources_source_filter'):
                    index = self.main_window.pbirs_sources_source_filter.currentIndex()
                    if index >= 0:
                        source_filter = self.main_window.pbirs_sources_source_filter.currentText()
                        if source_filter == "Все источники":
                            source_filter = None
                
                self.main_window.update_pbirs_sources_table(sources_data, report_filter, source_filter)
                self.main_window.log_message(f"✓ Таблица источников PBIRS обновлена (записей: {len(sources_data)})")
            
            # Заполняем комбобокс фильтра источников данных уникальными значениями
            if hasattr(self.main_window, 'pbirs_sources_source_filter'):
                combo = self.main_window.pbirs_sources_source_filter
                combo.clear()
                combo.addItem("Все источники")
                # Собираем уникальные ConnectionString
                unique_connections = set()
                for source_item in sources_data:
                    connection_string = source_item.get('ConnectionString', '')
                    if connection_string:
                        # Убедимся, что connection_string - строка (хэшируемый тип)
                        if not isinstance(connection_string, str):
                            try:
                                connection_string = str(connection_string)
                            except Exception:
                                # Если не удается преобразовать, пропускаем
                                self.main_window.log_message(f"⚠ Невозможно преобразовать ConnectionString: {type(connection_string)}")
                                continue
                        unique_connections.add(connection_string)
                for conn_string in sorted(unique_connections):
                    # Обрезаем длинные строки для отображения в комбобоксе
                    display_string = conn_string
                    if len(display_string) > 100:
                        display_string = display_string[:97] + '...'
                    combo.addItem(display_string)
                    # Сохраняем полный ConnectionString в userData
                    combo.setItemData(combo.count() - 1, conn_string, Qt.ItemDataRole.UserRole)
                self.main_window.log_message(f"  Заполнен фильтр источников данных: {len(unique_connections)} уникальных значений")
            
            # Обновляем таблицу детальной информации PBIRS
            if hasattr(self.main_window, 'update_pbirs_details_table'):
                # Сохраняем данные для фильтрации
                self.main_window.pbirs_details_data = enriched_reports
                # Определяем текущий фильтр по названию (если поле существует)
                name_filter = None
                if hasattr(self.main_window, 'pbirs_details_name_filter'):
                    name_filter = self.main_window.pbirs_details_name_filter.text()
                self.main_window.update_pbirs_details_table(enriched_reports, name_filter)
                self.main_window.log_message("✓ Таблица деталей PBIRS обновлена")
            
            # Обновляем комбобокс выбора отчета на вкладке "Детали PBIRS"
            if hasattr(self.main_window, 'pbirs_details_report_combo'):
                self._update_pbirs_details_report_combo(enriched_reports)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка при загрузке отчетов PBIRS: {e}")
            self.main_window.log_message(f"Детали ошибки: {traceback.format_exc()}")
    
    def _extract_folders_from_reports(self, reports: list) -> list:
        """
        Извлекает уникальные папки из списка отчетов.
        
        Args:
            reports: Список отчетов (каждый отчет - словарь с полем 'Path')
        
        Returns:
            Список уникальных папок (строки), включая корневую '/'
        """
        folders = set()
        folders.add('/')  # Корневая папка
        for report in reports:
            path = report.get('Path', '')
            if path:
                # Убедимся, что path - строка
                if not isinstance(path, str):
                    path = str(path)
                # Путь вида "/folder/subfolder/report"
                # Добавляем все родительские директории
                parts = path.strip('/').split('/')
                current = ''
                for part in parts[:-1]:  # Исключаем последний элемент (имя отчета)
                    current += '/' + part
                    folders.add(current)
                # Также добавляем полный путь как папку (если отчет лежит прямо в папке)
                # Но обычно Path указывает на сам отчет, а не папку.
                # Для простоты добавляем директорию отчета (убираем последний элемент)
                dir_path = '/'.join(parts[:-1]) if len(parts) > 1 else '/'
                if dir_path:
                    folders.add('/' + dir_path if not dir_path.startswith('/') else dir_path)
        # Преобразуем в список и сортируем
        return sorted(list(folders))
    
    def get_report_data_sources_for_table(self, report_id: str) -> str:
        """
        Получает источники данных для отчёта и форматирует их для отображения в таблице.
        
        Args:
            report_id: ID отчета
        
        Returns:
            Строка с перечислением источников данных
        """
        if not hasattr(self.main_window.client, 'get_report_data_sources'):
            return "Нет данных"
        
        try:
            data_sources = self.main_window.client.get_report_data_sources(report_id)
            if not data_sources:
                return "Нет источников"
            
            # Формируем строку с именами источников
            names = []
            for ds in data_sources[:3]:  # Ограничим тремя источниками
                name = ds.get('Name', 'Без имени')
                ds_type = ds.get('DataSourceType', '')
                if ds_type:
                    names.append(f"{name} ({ds_type})")
                else:
                    names.append(name)
            
            result = ", ".join(names)
            if len(data_sources) > 3:
                result += f" ... (+{len(data_sources) - 3})"
            return result
        except Exception:
            return "Ошибка загрузки"
    
    def _update_pbirs_details_report_combo(self, reports):
        """
        Обновляет комбобокс выбора отчета на вкладке "Детали PBIRS".
        
        Args:
            reports: Список отчетов (обогащенные данные)
        """
        if not hasattr(self.main_window, 'pbirs_details_report_combo'):
            return
        
        combo = self.main_window.pbirs_details_report_combo
        current_text = combo.currentText()
        
        combo.clear()
        combo.addItem("-- Выберите отчет --", None)
        
        for report in reports:
            name = report.get('Name', 'Без имени')
            report_id = report.get('Id', '')
            # Добавляем в комбобокс
            combo.addItem(name, report)
        
        # Восстанавливаем предыдущий выбор, если возможно
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentIndex(0)
        
        self.main_window.log_message(f"✓ Комбобокс отчетов PBIRS обновлен: {len(reports)} отчетов")


if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    print("Тестирование модуля PBIRS Operations...")
    print("Модуль готов к использованию.")