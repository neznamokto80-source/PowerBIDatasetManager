#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно приложения мониторинга Power BI.
Содержит основной интерфейс и управление состоянием приложения.
"""

import logging

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QStatusBar,
    QTableWidgetItem, QDialog, QFormLayout, QLabel, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush

from src.ui.ui_components import UIComponents
from src.ui.theme_colors import ThemeColors, apply_theme_to_app, get_active_theme
from src.ui.themes import THEMES

# Импорт классов операций (после рефакторинга)
from src.core.connection import ConnectionMethods
from src.core.connection_pbirs import PBIRSConnectionMethods
from src.core.powerbi_client import PowerBIClient
from src.core.powerbi_report_server_client import PowerBIReportServerClient
from src.operations.data_loading_ops import DataLoadingMethods
from src.operations.ui_operations import UIOperations
from src.operations.data_filtering_ops import DataFilteringOperations
from src.operations.refresh_operations import RefreshOperations, ProgressManager
from src.operations.pbirs_operations import PBIRSOperations
from src.utils.log_handler import QTextEditLogHandler
from src.utils.pbirs_data_enricher import enrich_reports_list, enrich_report_data
from src.utils.pbirs_formatter import format_report_details

logger = logging.getLogger(__name__)


class PowerBIMonitorUI(QMainWindow):
    """Главное окно приложения мониторинга Power BI."""
    
    # Сигналы для межпоточного взаимодействия (если понадобится)
    data_loaded = pyqtSignal()
    refresh_completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.refresh_manager = None
        self.integration = None
        self.data_provider = None
        self.current_workspace = None
        self.current_dataset = None
        self.workspaces = []
        self.datasets = []
        self.auto_refresh_enabled = False  # Флаг автообновления
        # Текущая тема интерфейса (имя темы; по умолчанию — тёмная Catppuccin Mocha)
        self.current_theme = list(THEMES.keys())[0]
        self.current_mode = None  # 'service' или 'server'
        self.debug_data_path = None  # Путь для сохранения сырых логов
        
        # Состояние сортировки для таблиц PBIRS
        self._pbirs_sort_states = {}
        
        # Инициализация компонентов UI
        self.ui_components = UIComponents(self)
        
        # Инициализация классов методов
        self._init_method_classes()
        
        self.init_ui()
        self.initialize_backend()
    
    def _init_method_classes(self):
        """Инициализирует классы операций (после рефакторинга)."""
        self.connection_methods = ConnectionMethods(self)
        self.pbirs_connection_methods = PBIRSConnectionMethods(self)  # Для обратной совместимости
        self.pbirs_operations = PBIRSOperations(self)  # Новый модуль PBIRS операций
        self.data_loading_methods = DataLoadingMethods(self)
        self.ui_operations = UIOperations(self)
        self.data_filtering_operations = DataFilteringOperations(self)
        self.refresh_operations = RefreshOperations(self)
        self.progress_manager = ProgressManager(self)
    
    def _update_workspace_group_title(self):
        """Обновляет заголовок группы 'Рабочие области' в зависимости от текущего режима."""
        if hasattr(self, 'workspace_group'):
            if self.current_mode == 'server':
                self.workspace_group.setTitle("Расположение отчетов")
            else:
                self.workspace_group.setTitle("Рабочие области")
    
    def _reset_backend_for_mode_switch(self, target_mode: str):
        """
        Сбрасывает бэкенд и UI при переключении между режимами Service и Server.
        
        Args:
            target_mode: 'service' или 'server'
        """
        if self.current_mode == target_mode:
            return  # Уже в нужном режиме, ничего не делаем
        
        logger.info(f"Переключение режима с {self.current_mode} на {target_mode}")
        
        # Очищаем данные
        self.workspaces = []
        self.datasets = []
        self.current_workspace = None
        self.current_dataset = None
        
        # Сбрасываем UI в состояние "не подключено"
        self.update_ui_for_disconnected_state()
        
        # Останавливаем таймер автообновления, если запущен
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.log_message("Таймер автообновления остановлен при переключении режима.")
        
        # Сбрасываем клиент и менеджер (они будут созданы заново при инициализации)
        self.client = None
        self.refresh_manager = None
        self.integration = None
        self.data_provider = None
        
        # Обновляем текущий режим
        self.current_mode = target_mode
        
        # Обновляем заголовок группы
        self._update_workspace_group_title()
        
        # Обновляем видимость вкладок
        self.update_tabs_visibility()
        
        self.log_message(f"Режим переключен на {target_mode}. Готов к подключению.")
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        self.setWindowTitle("Power BI Dataset Monitor & Manager")
        self.setGeometry(100, 100, 1400, 800)

        # Применяем текущую тему оформления (Catppuccin)
        apply_theme_to_app(self.current_theme)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        
        # Панель с отдельными кнопками (вместо панели инструментов)
        button_panel = self.ui_components.create_button_panel()
        main_layout.addWidget(button_panel)
        
        # Вертикальный разделитель для основной области и логов
        vertical_splitter = QSplitter(Qt.Vertical)

        # Горизонтальный разделитель для левой и центральной панели
        horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель (навигация)
        left_panel = self.ui_components.create_left_panel()
        horizontal_splitter.addWidget(left_panel)
        
        # Центральная панель (контент)
        center_panel = self.ui_components.create_center_panel()
        horizontal_splitter.addWidget(center_panel)
        
        # Правая панель удалена по требованию
        # right_panel = self.ui_components.create_right_panel()
        # horizontal_splitter.addWidget(right_panel)
        
        horizontal_splitter.setSizes([300, 1100])
        vertical_splitter.addWidget(horizontal_splitter)
        
        # Панель логов (нижний блок)
        logs_panel = self.ui_components.create_logs_panel()
        vertical_splitter.addWidget(logs_panel)
        
        # Установим начальные размеры: 70% для основной области, 30% для логов
        vertical_splitter.setSizes([600, 200])
        
        main_layout.addWidget(vertical_splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        
        # Таймер для обновления данных (не запускается автоматически)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        # Таймер не запускается - будет запускаться только при включении мониторинга
        
        # Настройка обработчика логов для отображения в панели логов
        self.setup_log_handler()
        
        # Обновляем видимость вкладок в соответствии с текущим режимом
        self.update_tabs_visibility()
    
    # Делегирование методов классам методов
    
    def setup_log_handler(self):
        """Настраивает обработчик логов для вывода в панель логов."""
        # Убедимся, что logs_text существует
        if not hasattr(self, 'logs_text'):
            # logs_text создается в create_logs_panel, должен быть уже создан
            logger.warning("logs_text не найден, обработчик логов не будет настроен.")
            return
        
        if self.logs_text is None:
            logger.warning("logs_text равен None, обработчик логов не будет настроен.")
            return
        
        logger.info("Настройка обработчика логов для UI...")
        
        # Создаем обработчик и привязываем к logs_text
        handler = QTextEditLogHandler(self.logs_text)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Добавляем обработчик к корневому логгеру
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
        # Также добавим обработчик к логгеру этого модуля
        logger.addHandler(handler)
        
        logger.info("Обработчик логов для UI настроен.")
    
    def initialize_backend(self):
        """Инициализация бэкенда приложения (без автоматического подключения)."""
        return self.connection_methods.initialize_backend()
    
    def connect_to_powerbi(self):
        """Подключение к Power BI."""
        # Проверяем, нужен ли переход между режимами
        if self.current_mode != 'service' or not isinstance(self.client, PowerBIClient):
            self._reset_backend_for_mode_switch('service')
            # После сброса клиент = None, нужно инициализировать бэкенд
            self.initialize_backend()
        return self.connection_methods.connect_to_powerbi()
    
    def connect_to_powerbi_report_server(self):
        """Подключение к Power BI Report Server."""
        # Проверяем, нужен ли переход между режимами
        if self.current_mode != 'server' or not isinstance(self.client, PowerBIReportServerClient):
            self._reset_backend_for_mode_switch('server')
            # После сброса клиент = None, бэкенд будет инициализирован в connect_to_powerbi_report_server
            # (там запрашиваются параметры сервера и вызывается initialize_backend_pbirs)
        return self.pbirs_operations.connect_to_powerbi_report_server()
    
    def load_pbirs_reports(self):
        """Загружает отчеты Power BI Report Server."""
        if hasattr(self, 'pbirs_operations'):
            return self.pbirs_operations.load_pbirs_reports()
    
    def update_folders_combo(self, folders):
        """
        Обновляет комбобокс папок (в режиме server) или рабочие области (в режиме service).
        
        Args:
            folders: Список путей папок (для режима server)
        """
        if not hasattr(self, 'workspace_combo'):
            return
        
        # Сохраняем текущий выбор
        current_text = self.workspace_combo.currentText()
        
        self.workspace_combo.clear()
        if self.current_mode == 'server':
            # Добавляем опцию "Все папки" в начало
            self.workspace_combo.addItem("Все папки")
            # Добавляем папки
            for folder in folders:
                self.workspace_combo.addItem(folder)
            # Если есть предыдущий выбор, пытаемся восстановить
            index = self.workspace_combo.findText(current_text)
            if index >= 0:
                self.workspace_combo.setCurrentIndex(index)
            else:
                self.workspace_combo.setCurrentIndex(0)  # По умолчанию "Все папки"
        else:
            # Для service комбобокс будет заполняться отдельно
            pass
    
    def update_pbirs_reports_table(self, reports, selected_folder=None, name_filter=None):
        """
        Заполняет таблицу отчётов PBIRS данными с фильтрацией по выбранной папке и названию.
        
        Args:
            reports: Список словарей с информацией об отчётах (уже обогащенные данные)
            selected_folder: Выбранная папка для фильтрации (None или "Все папки" - показывать все)
            name_filter: Строка для фильтрации по названию отчета (None или пустая - без фильтра)
        """
        if not hasattr(self, 'pbirs_reports_table'):
            return
        
        table = self.pbirs_reports_table
        table.setRowCount(0)
        
        if not reports:
            return
        
        # Обогащаем данные отчетов, если они еще не обогащены
        # Проверяем, есть ли уже обогащенные поля
        if reports and 'DataSourcesBrief' not in reports[0]:
            reports = enrich_reports_list(reports)
        
        # Фильтруем отчеты по выбранной папке
        filtered_reports = []
        if selected_folder and selected_folder != "Все папки":
            # Нормализуем выбранную папку: добавляем ведущий слеш если отсутствует
            if not selected_folder.startswith('/'):
                selected_folder = '/' + selected_folder
            # Для каждой папки включаем ее подпапки
            for report in reports:
                path = report.get('Path', '')
                # Убедимся, что path - строка
                if not isinstance(path, str):
                    path = str(path)
                # Получаем папку отчета (убираем имя файла)
                report_folder = '/'.join(path.split('/')[:-1]) if '/' in path else '/'
                if not report_folder.startswith('/'):
                    report_folder = '/' + report_folder
                # Проверяем, начинается ли папка отчета с выбранной папки (включая подпапки)
                if report_folder == selected_folder or report_folder.startswith(selected_folder + '/'):
                    filtered_reports.append(report)
        else:
            filtered_reports = reports
        
        # Дополнительная фильтрация по названию отчета
        if name_filter and name_filter.strip():
            name_filter_lower = name_filter.strip().lower()
            filtered_reports = [r for r in filtered_reports if name_filter_lower in r.get('Name', '').lower()]
        
        # Устанавливаем количество строк
        table.setRowCount(len(filtered_reports))
        
        for row, report in enumerate(filtered_reports):
            # Колонка 0: Папка
            folder = report.get('FolderDisplay', '/')
            table.setItem(row, 0, QTableWidgetItem(folder))
            
            # Колонка 1: Название отчёта
            name = report.get('Name', 'Без имени')
            table.setItem(row, 1, QTableWidgetItem(name))
            
            # Колонка 2: Размер в МБ
            size_display = report.get('SizeDisplay', '0 МБ')
            table.setItem(row, 2, QTableWidgetItem(size_display))
            
            # Колонка 3: Тип отчёта
            report_type_display = report.get('ReportTypeDisplay', 'Unknown')
            table.setItem(row, 3, QTableWidgetItem(report_type_display))
            
            # Колонка 4: Источники данных (полный текст + tooltip)
            sources_brief = report.get('DataSourcesBrief', 'Нет источников')
            sources_item = QTableWidgetItem(sources_brief)
            table.setItem(row, 4, sources_item)
            # Tooltip с полными ConnectionString
            data_sources = report.get('DataSourcesList', [])
            if data_sources:
                tooltip_lines = []
                for ds in data_sources:
                    if ds is None:
                        continue
                    conn_str = ds.get('ConnectionString', '')
                    if conn_str:
                        tooltip_lines.append(f"• {conn_str}")
                if tooltip_lines:
                    sources_item.setToolTip("Полные строки подключения:\n" + "\n".join(tooltip_lines))
            
            # Колонка 5: Последний статус (полный текст + tooltip)
            last_status = report.get('LastStatus', 'Не запускался')
            last_run_time = report.get('LastRunTime')
            # Если есть планы обновления, но нет времени последнего запуска, показываем "Новое расписание обновления"
            if not last_run_time and report.get('RefreshPlansList'):
                last_status = 'Новое расписание обновления'
            
            status_item = QTableWidgetItem(last_status)
            status_item.setToolTip(f"{last_status}")
            table.setItem(row, 5, status_item)
            
            # Колонка 6: Последнее обновление (полный формат)
            last_run_display = report.get('LastRunDisplayFull', report.get('LastRunDisplay', 'Никогда'))
            table.setItem(row, 6, QTableWidgetItem(last_run_display))
            
            # Колонка 7: Следующее обновление (детализированный формат)
            next_run_display = report.get('NextRunDisplayDetailed', report.get('NextRunDisplay', 'Не запланировано'))
            table.setItem(row, 7, QTableWidgetItem(next_run_display))
            
            # Сохраняем полные данные отчета в userData для доступа при двойном клике
            table.item(row, 0).setData(Qt.UserRole, report)

            # Цветовое выделение строки отчёта PBIRS
            background_color = ThemeColors.get_pbirs_background_color(report, self.current_theme)
            if background_color:
                brush = QBrush(background_color)
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        item.setBackground(brush)
        
        # Автоматически подгоняем ширину колонок
        #table.resizeColumnsToContents()
        
        # Обновляем статистику PBIRS на основе отфильтрованных данных
        self.update_pbirs_stats(filtered_reports)
    
    def update_pbirs_sources_table(self, sources_data, report_filter=None, source_filter=None, kind_filter=None, user_filter=None):
        """
        Заполняет таблицу источников данных PBIRS.
        
        Args:
            sources_data: Список словарей с информацией об источниках данных.
                Каждый словарь должен содержать ключи: Folder, ReportName, DataSource, ConnectionString
            report_filter: Строка для фильтрации по названию отчета (None - без фильтра)
            source_filter: Строка для фильтрации по ConnectionString (None - без фильтра)
            kind_filter: Строка для фильтрации по типу Kind (None - без фильтра, строгое соответствие)
            user_filter: Строка для фильтрации по пользователю (None - без фильтра, строгое соответствие)
        """
        if not hasattr(self, 'pbirs_sources_table'):
            return
        
        table = self.pbirs_sources_table
        table.setRowCount(0)
        
        if not sources_data:
            return
        
        # Фильтрация данных
        filtered_sources = []
        for source_item in sources_data:
            folder = source_item.get('Folder', '')
            report_name = source_item.get('ReportName', '')
            connection_string = source_item.get('ConnectionString', '')
            kind = source_item.get('Kind', '')
            username = source_item.get('Username', '')
            
            # Проверяем фильтр по названию отчета
            report_match = True
            if report_filter and report_filter.strip():
                report_match = report_filter.lower() in report_name.lower()
            
            # Проверяем фильтр по ConnectionString
            source_match = True
            if source_filter and source_filter.strip():
                filter_lower = source_filter.lower()
                connection_string_lower = connection_string.lower()
                source_match = filter_lower in connection_string_lower
            
            # Проверяем фильтр по типу (Kind) — строгое соответствие
            kind_match = True
            if kind_filter and kind_filter.strip():
                kind_match = kind.lower() == kind_filter.lower()
            
            # Проверяем фильтр по пользователю — строгое соответствие
            user_match = True
            if user_filter and user_filter.strip():
                user_match = username.lower() == user_filter.lower()
            
            if report_match and source_match and kind_match and user_match:
                filtered_sources.append(source_item)
        
        # Устанавливаем количество строк
        table.setRowCount(len(filtered_sources))
        
        for row, source_item in enumerate(filtered_sources):
            # Колонка 0: Папка
            folder = source_item.get('Folder', '/')
            table.setItem(row, 0, QTableWidgetItem(folder))
            
            # Колонка 1: Название отчета
            report_name = source_item.get('ReportName', 'Без имени')
            table.setItem(row, 1, QTableWidgetItem(report_name))
            
            # Колонка 2: ConnectionString (сокращенный вид) с дополнительной информацией в tooltip
            connection_string = source_item.get('ConnectionString', '')
            data_source_type = source_item.get('DataSourceType', '')
            created_by = source_item.get('CreatedBy', '')
            created_date = source_item.get('CreatedDateFormatted', '')
            modified_date = source_item.get('ModifiedDateFormatted', '')
            
            # Обрезаем длинные строки
            if len(connection_string) > 100:
                display_string = connection_string[:97] + '...'
            else:
                display_string = connection_string
            table.setItem(row, 2, QTableWidgetItem(display_string))
            
            # Колонка 3: Тип (Kind)
            kind = source_item.get('Kind', '')
            table.setItem(row, 3, QTableWidgetItem(kind))
            
            # Колонка 4: Дата изменения
            table.setItem(row, 4, QTableWidgetItem(modified_date))
            
            # Колонка 5: Пользователь
            username = source_item.get('Username', '')
            table.setItem(row, 5, QTableWidgetItem(username))
            
            # Колонка 6: Следующее обновление
            next_run = source_item.get('NextRunDisplay', 'Не запланировано')
            table.setItem(row, 6, QTableWidgetItem(next_run))
            
            # Создаем расширенный tooltip с дополнительной информацией
            tooltip_lines = []
            if connection_string:
                tooltip_lines.append(f"Источник: {connection_string}")
            if data_source_type:
                tooltip_lines.append(f"Тип источника: {data_source_type}")
            if kind:
                tooltip_lines.append(f"Тип: {kind}")
            if created_by:
                tooltip_lines.append(f"Создатель: {created_by}")
            if created_date:
                tooltip_lines.append(f"Создан: {created_date}")
            if modified_date:
                tooltip_lines.append(f"Изменён: {modified_date}")
            if username:
                tooltip_lines.append(f"Пользователь: {username}")
            
            if tooltip_lines:
                table.item(row, 2).setToolTip("\n".join(tooltip_lines))
        
        # Автоматически подгоняем ширину колонок
        #table.resizeColumnsToContents()
    
    def update_pbirs_details_table(self, reports, name_filter=None):
        """
        Обновляет таблицу детальной информации об отчетах PBIRS.
        
        Args:
            reports: Список отчетов с расширенными данными
            name_filter: Фильтр по названию отчета (часть строки)
        """
        if not hasattr(self, 'pbirs_details_table'):
            return
        
        table = self.pbirs_details_table
        table.setRowCount(0)
        
        # Фильтрация отчетов
        filtered_reports = []
        for report in reports:
            if name_filter:
                report_name = report.get('Name', '')
                if name_filter.lower() not in report_name.lower():
                    continue
            filtered_reports.append(report)
        
        # Сохраняем отфильтрованные данные для использования в фильтрации
        self.pbirs_details_data = filtered_reports
        
        table.setRowCount(len(filtered_reports))
        
        for row, report in enumerate(filtered_reports):
            # ID
            report_id = report.get('Id', '')
            table.setItem(row, 0, QTableWidgetItem(str(report_id)))
            
            # Название
            name = report.get('Name', '')
            table.setItem(row, 1, QTableWidgetItem(name))
            
            # Путь
            path = report.get('Path', '')
            table.setItem(row, 2, QTableWidgetItem(path))
            
            # Тип
            report_type = report.get('ReportTypeDisplay', report.get('Type', ''))
            table.setItem(row, 3, QTableWidgetItem(report_type))
            
            # Размер (МБ)
            size_mb = report.get('SizeDisplay', '0')
            table.setItem(row, 4, QTableWidgetItem(size_mb))
            
            # Источники данных
            data_sources = report.get('DataSourcesDisplay', '')
            table.setItem(row, 5, QTableWidgetItem(data_sources))
            
            # Последний статус
            last_status = report.get('LastStatusDisplay', '')
            table.setItem(row, 6, QTableWidgetItem(last_status))
            
            # Последнее обновление
            last_refresh = report.get('LastRefreshDisplay', '')
            table.setItem(row, 7, QTableWidgetItem(last_refresh))
            
            # Следующее обновление
            next_refresh = report.get('NextRefreshDisplay', '')
            table.setItem(row, 8, QTableWidgetItem(next_refresh))
            
            # Создатель
            created_by = report.get('CreatedBy', '')
            table.setItem(row, 9, QTableWidgetItem(created_by))
        
        # Автоматически подгоняем ширину колонок
        #table.resizeColumnsToContents()
    
    def sort_pbirs_table(self, table_key: str, column: int):
        """
        Сортирует таблицу PBIRS по выбранной колонке.
        Первый двойной клик — сортировка по возрастанию,
        повторный по той же колонке — по убыванию.
        
        Args:
            table_key: Ключ таблицы ('reports' или 'sources')
            column: Индекс колонки для сортировки
        """
        table_map = {
            'reports': getattr(self, 'pbirs_reports_table', None),
            'sources': getattr(self, 'pbirs_sources_table', None),
        }
        table = table_map.get(table_key)
        if not table:
            return
        
        state = self._pbirs_sort_states.get(table_key, {})
        prev_col = state.get('column')
        prev_order = state.get('order', Qt.AscendingOrder)
        
        if prev_col == column:
            # Та же колонка — инвертируем порядок
            new_order = (Qt.DescendingOrder
                         if prev_order == Qt.AscendingOrder
                         else Qt.AscendingOrder)
        else:
            # Другая колонка — сортируем по возрастанию
            new_order = Qt.AscendingOrder
        
        self._pbirs_sort_states[table_key] = {'column': column, 'order': new_order}
        table.sortItems(column, new_order)
    
    def update_pbirs_stats(self, reports):
        """
        Обновляет блок статистики PBIRS на основе отфильтрованных данных.
        Считает: всего отчётов, с ошибками, общий размер в МБ.
        
        Args:
            reports: Список отфильтрованных отчётов PBIRS
        """
        if not hasattr(self, 'pbirs_stats_total'):
            return
        
        total = len(reports)
        
        # Считаем отчёты с ошибками
        errors = 0
        total_size_mb = 0.0
        for report in reports:
            # Проверка статуса ошибки
            last_status = report.get('LastStatus', '')
            if last_status and ('error' in last_status.lower()
                                or 'failed' in last_status.lower()
                                or 'ошибк' in last_status.lower()):
                errors += 1
            
            # Суммируем размер
            size_str = report.get('SizeDisplay', '0 МБ')
            try:
                size_val = float(size_str.replace(' МБ', '').replace(',', '.').strip())
                total_size_mb += size_val
            except (ValueError, AttributeError):
                pass
        
        self.pbirs_stats_total.setText(f"Всего: {total}")
        self.pbirs_stats_errors.setText(f"С ошибками: {errors}")
        self.pbirs_stats_size.setText(f"Общий размер: {total_size_mb:.1f} МБ")
    
    def update_tabs_visibility(self):
        """
        Обновляет видимость вкладок в зависимости от текущего режима.
        В режиме server скрывает вкладки "Обзор" и "Детали", показывает "Отчёты PBIRS", "Источники PBIRS" и "Детали PBIRS".
        В режиме service показывает "Обзор" и "Детали", скрывает вкладки PBIRS.
        """
        if not hasattr(self, 'tab_widget'):
            return
        
        if self.current_mode == 'server':
            # Скрываем вкладки 0 и 1, показываем вкладки 2, 3 и 4
            self.tab_widget.setTabVisible(0, False)  # Обзор
            self.tab_widget.setTabVisible(1, False)  # Детали (облачная версия)
            self.tab_widget.setTabVisible(2, True)   # Отчёты PBIRS
            self.tab_widget.setTabVisible(3, True)   # Источники PBIRS
            self.tab_widget.setTabVisible(4, True)   # Детали PBIRS
        else:
            # Показываем вкладки 0 и 1, скрываем вкладки 2, 3 и 4
            self.tab_widget.setTabVisible(0, True)
            self.tab_widget.setTabVisible(1, True)
            self.tab_widget.setTabVisible(2, False)
            self.tab_widget.setTabVisible(3, False)
            self.tab_widget.setTabVisible(4, False)
        
        # Показываем/скрываем блок статистики PBIRS в зависимости от режима
        if hasattr(self, 'pbirs_stats_widget'):
            self.pbirs_stats_widget.setVisible(self.current_mode == 'server')
    
    def set_pbirs_filters_visible(self, visible: bool):
        """Переключает видимость PBIRS-фильтров в левой панели.
        
        Args:
            visible: True — показать PBIRS-фильтры (режим server),
                     False — показать Service-фильтры (режим service)
        """
        if hasattr(self, 'ui_components') and hasattr(self.ui_components, 'panels'):
            self.ui_components.panels._set_pbirs_filters_visible(visible)
    
    def refresh_data(self):
        """Обновление данных."""
        return self.data_loading_methods.refresh_data()
    
    def load_test_data(self):
        """Загружает тестовые данные (демо-режим) для скриншотов."""
        return self.data_loading_methods.load_test_data()
    
    def load_workspaces(self):
        """Загружает список рабочих областей из Power BI."""
        return self.data_loading_methods.load_workspaces()
    
    def load_datasets(self):
        """Загружает датасеты из выбранной рабочей области."""
        return self.data_loading_methods.load_datasets()
    
    def update_dataset_table(self, datasets):
        """Обновляет таблицу датасетов."""
        return self.data_loading_methods.update_dataset_table(datasets)
    
    def update_stats(self, datasets):
        """Обновляет статистику."""
        return self.data_loading_methods.update_stats(datasets)
    
    def get_workspace_name(self, workspace_id):
        """Возвращает имя рабочей области по ID."""
        return self.data_loading_methods.get_workspace_name(workspace_id)
    
    def update_dataset_details(self, dataset):
        """Обновляет детальную информацию о выбранном датасете."""
        return self.data_loading_methods.update_dataset_details(dataset)
    
    def update_ui_for_disconnected_state(self):
        """Обновляет UI для состояния 'не подключено'."""
        return self.ui_operations.update_ui_for_disconnected_state()
    
    def update_ui_for_connected_state(self):
        """Обновляет UI для состояния 'подключено'."""
        return self.ui_operations.update_ui_for_connected_state()
    
    def log_message(self, message: str):
        """Добавляет сообщение в лог."""
        return self.ui_operations.log_message(message)
    
    def on_workspace_selected(self, index):
        """Обработчик выбора рабочей области."""
        return self.ui_operations.on_workspace_selected(index)
    
    def on_dataset_selected(self, item, column):
        """Обработчик выбора датасета."""
        return self.ui_operations.on_dataset_selected(item, column)
    
    def on_pbirs_name_filter_changed(self):
        """Обработчик изменения текста в поле фильтра по названию отчета PBIRS."""
        return self.ui_operations.on_pbirs_name_filter_changed()
    
    def on_pbirs_sources_filter_changed(self):
        """Обработчик изменения фильтров на вкладке источников данных PBIRS."""
        return self.ui_operations.on_pbirs_sources_filter_changed()
    
    def on_pbirs_details_filter_changed(self):
        """Обработчик изменения фильтра на вкладке детальной информации PBIRS."""
        return self.ui_operations.on_pbirs_details_filter_changed()
    
    def on_pbirs_report_double_clicked(self, index):
        """Обработчик двойного клика на отчете PBIRS для открытия детальной информации."""
        # Определяем, из какой таблицы пришел сигнал
        sender_table = self.sender()
        if not sender_table:
            # Если sender не определен, используем таблицу отчетов по умолчанию
            if hasattr(self, 'pbirs_reports_table'):
                table = self.pbirs_reports_table
            else:
                return
        else:
            table = sender_table
        
        row = index.row()
        
        if row < 0 or row >= table.rowCount():
            return
        
        # Получаем данные отчета из userData
        item = table.item(row, 0)
        if not item:
            return
        
        report_data = item.data(Qt.UserRole)
        if not report_data:
            return
        
        # Открываем диалоговое окно с детальной информацией
        self.show_report_details_dialog(report_data)
    
    # ========== Методы для вкладки "Детали PBIRS" ==========
    
    def on_pbirs_details_report_selected(self):
        """Обработчик выбора отчета в выпадающем списке на вкладке Детали PBIRS."""
        return self.ui_operations.on_pbirs_details_report_selected()
    
    def enable_pbirs_refresh(self):
        """Включение автоматического обновления для выбранного отчета PBIRS."""
        return self.ui_operations.enable_pbirs_refresh()
    
    def disable_pbirs_refresh(self):
        """Отключение автоматического обновления для выбранного отчета PBIRS."""
        return self.ui_operations.disable_pbirs_refresh()
    
    def trigger_pbirs_manual_refresh(self):
        """Ручной запуск обновления для выбранного отчета PBIRS."""
        return self.ui_operations.trigger_pbirs_manual_refresh()
    
    def add_pbirs_schedule_time(self):
        """Добавление нового времени в расписание PBIRS."""
        return self.ui_operations.add_pbirs_schedule_time()
    
    def remove_pbirs_schedule_time(self):
        """Удаление выбранного времени из расписания PBIRS."""
        return self.ui_operations.remove_pbirs_schedule_time()
    
    def save_pbirs_schedule(self):
        """Сохранение расписания для выбранного отчета PBIRS."""
        return self.ui_operations.save_pbirs_schedule()
    
    def delete_pbirs_schedule(self):
        """Удаление расписания для выбранного отчета PBIRS."""
        return self.ui_operations.delete_pbirs_schedule()

    def execute_pbirs_schedule(self):
        """Немедленный запуск выбранного расписания обновления кэша PBIRS."""
        return self.ui_operations.execute_pbirs_schedule()

    def show_pbirs_refresh_plans_context_menu(self, position):
        """Показывает контекстное меню для таблицы расписаний PBIRS."""
        return self.ui_operations.show_pbirs_refresh_plans_context_menu(position)
    
    def show_report_details_dialog(self, report_data):
        """Открывает диалоговое окно с детальной информацией об отчете."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Детали отчета: {report_data.get('Name', 'Без имени')}")
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        
        layout = QVBoxLayout(dialog)
        
        # Текстовое поле с форматированными деталями
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFontFamily("Courier New")
        text_edit.setFontPointSize(10)
        
        # Форматируем детали отчёта
        formatted_text = format_report_details(report_data)
        text_edit.setPlainText(formatted_text)
        
        layout.addWidget(text_edit)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def on_details_dataset_selected(self, index):
        """Обработчик выбора датасета в комбобоксе на вкладке детали."""
        if index < 0:
            return
        # Получаем выбранный датасет из комбобокса
        dataset = self.details_dataset_combo.itemData(index)
        if dataset:
            self.current_dataset = dataset
            # Пытаемся получить workspace из различных возможных ключей
            self.current_workspace = (
                dataset.get('workspaceId') or
                dataset.get('workspace_id') or
                dataset.get('workspace')
            )
            self.update_dataset_details(dataset)
    
    def update_details_dataset_combo(self, datasets):
        """Обновляет комбобокс выбора датасета на вкладке детали."""
        if not hasattr(self, 'details_dataset_combo'):
            return
        combo = self.details_dataset_combo
        
        # Запоминаем текущий выбранный датасет (если есть)
        current_dataset_id = None
        if self.current_dataset:
            current_dataset_id = self.current_dataset.get('id')
        
        combo.clear()
        found_index = -1
        for idx, ds in enumerate(datasets):
            name = ds.get('name', 'Без имени')
            combo.addItem(name, ds)
            # Если это текущий датасет, запоминаем индекс
            if current_dataset_id and ds.get('id') == current_dataset_id:
                found_index = idx
                # Обновляем current_dataset на актуальный объект
                self.current_dataset = ds
        
        # Добавляем пустой элемент placeholder
        if combo.count() == 0:
            combo.addItem("-- Нет датасетов --", None)
        # Устанавливаем выбранный элемент, если нашли
        elif found_index >= 0:
            combo.setCurrentIndex(found_index)
        # Иначе сбрасываем выбор
        else:
            combo.setCurrentIndex(-1)
    
    def on_dataset_double_clicked(self, item):
        """Обработчик двойного клика по датасета."""
        return self.ui_operations.on_dataset_double_clicked(item)
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы датасетов."""
        return self.ui_operations.show_context_menu(position)
    
    def apply_filters(self):
        """Применяет фильтры к списку датасетов."""
        return self.data_filtering_operations.apply_filters()
    
    def start_monitoring(self):
        """Запускает мониторинг в реальном времени."""
        return self.data_filtering_operations.start_monitoring()

    def stop_monitoring(self):
        """Останавливает мониторинг в реальном времени."""
        return self.data_filtering_operations.stop_monitoring()

    def get_monitor_interval(self) -> int:
        """Возвращает выбранный интервал мониторинга в миллисекундах."""
        if hasattr(self, 'monitor_radio_15') and self.monitor_radio_15.isChecked():
            return 15000
        elif hasattr(self, 'monitor_radio_60') and self.monitor_radio_60.isChecked():
            return 60000
        else:
            return 30000  # 30 сек по умолчанию

    def _update_monitor_group_title(self):
        """Обновляет заголовок группы мониторинга при смене периодичности и статуса."""
        if hasattr(self, 'monitor_group'):
            interval_sec = self.get_monitor_interval() // 1000
            if getattr(self, 'auto_refresh_enabled', False):
                self.monitor_group.setTitle(f"Мониторинг активен (периодичность опроса {interval_sec} сек)")
                self.monitor_group.setStyleSheet("QGroupBox { color: green; font-weight: bold; }")
            else:
                self.monitor_group.setTitle(f"Мониторинг не активен (периодичность опроса {interval_sec} сек)")
                self.monitor_group.setStyleSheet("QGroupBox { color: black; font-weight: normal; }")

        # Если мониторинг активен — перезапускаем таймер с новым интервалом
        if getattr(self, 'auto_refresh_enabled', False) and hasattr(self, 'update_timer'):
            self.update_timer.setInterval(self.get_monitor_interval())
            self.log_message(f"Интервал мониторинга изменён на {self.get_monitor_interval() // 1000} сек")

    def enable_auto_refresh(self):
        """Включает автоматическое обновление для выбранного датасета."""
        return self.refresh_operations.enable_auto_refresh()
    
    def disable_auto_refresh(self):
        """Отключает автоматическое обновление для выбранного датасета."""
        return self.refresh_operations.disable_auto_refresh()
    
    def trigger_manual_refresh(self):
        """Запускает ручное обновление выбранного датасета."""
        return self.refresh_operations.trigger_manual_refresh()

    def enable_auto_refresh_selected(self, datasets):
        """Включает автоматическое обновление для выбранных датасетов."""
        return self.refresh_operations.enable_auto_refresh_selected(datasets)

    def disable_auto_refresh_selected(self, datasets):
        """Отключает автоматическое обновление для выбранных датасетов."""
        return self.refresh_operations.disable_auto_refresh_selected(datasets)

    def trigger_manual_refresh_selected(self, datasets):
        """Запускает ручное обновление для выбранных датасетов."""
        return self.refresh_operations.trigger_manual_refresh_selected(datasets)

    def edit_refresh_schedule(self):
        """Диалог редактирования расписания обновления для выбранного датасета."""
        return self.refresh_operations.edit_refresh_schedule()

    def show_help(self):
        """Показывает справку."""
        return self.ui_operations.show_help()

    def toggle_debug_logging(self, state):
        """
        Включает/выключает сохранение сырых логов в каталог debug/.

        Args:
            state: Состояние чекбокса (0 - выключено, 2 - включено)
        """
        debug_enabled = state == 2  # Qt.Checked == 2
        debug_path = "debug" if debug_enabled else None
        
        # Сохраняем путь в главном окне для использования при создании клиентов
        self.debug_data_path = debug_path
        
        # Если клиент уже создан, обновляем его путь
        if hasattr(self, 'client') and self.client:
            self.client.set_debug_path(debug_path)
        
        self.log_message(f"Сохранение сырых логов {'включено' if debug_enabled else 'выключено'}")
        if debug_enabled:
            self.log_message(f"Сырые логи будут сохраняться в каталог: {debug_path}")

    def toggle_theme(self, state):
        """
        Переключает тему интерфейса между светлой и тёмной.

        Args:
            state: Состояние чекбокса (0 - выключено/светлая, 2 - включено/тёмная)
        """
        dark_enabled = state == 2  # Qt.Checked == 2
        theme_names = list(THEMES.keys())
        # Индексируем: [0] - тёмная (первая), [1] - светлая
        new_theme = theme_names[0] if dark_enabled else theme_names[-1]
        self.current_theme = new_theme
        apply_theme_to_app(new_theme)
        self.log_message(f"Тема изменена на '{new_theme}'")

    def toggle_schedule_group(self):
        """Переключает видимость группы управления расписанием."""
        if hasattr(self, 'schedule_group'):
            self.schedule_group.setVisible(not self.schedule_group.isVisible())

    def add_schedule_time(self):
        """Добавляет время из выпадающих списков часов и минут в список."""
        if not hasattr(self, 'schedule_hours_combo') or not hasattr(self, 'schedule_minutes_combo'):
            return
        hours = self.schedule_hours_combo.currentText()
        minutes = self.schedule_minutes_combo.currentText()
        time_text = f"{hours}:{minutes}"
        self.schedule_times_list.addItem(time_text)

    def remove_schedule_time(self):
        """Удаляет выбранное время из списка."""
        if not hasattr(self, 'schedule_times_list'):
            return
        selected = self.schedule_times_list.currentRow()
        if selected >= 0:
            self.schedule_times_list.takeItem(selected)

    def save_schedule(self):
        """Сохраняет расписание для выбранного датасета."""
        if not self.current_dataset or not self.current_workspace:
            self.log_message("Не выбран датасет или рабочая область")
            return
        # Сбор данных из UI
        days = [api_name for api_name, cb in self.schedule_day_checks.items() if cb.isChecked()]
        times = []
        for i in range(self.schedule_times_list.count()):
            times.append(self.schedule_times_list.item(i).text().strip())
        local_time_zone_id = self.schedule_tz_combo.currentText().strip()
        notify_option = self.schedule_notify_combo.currentData()
        enabled = self.schedule_enabled_cb.isChecked()
        
        payload = {
            "enabled": enabled,
            "days": days,
            "times": times,
            "localTimeZoneId": local_time_zone_id,
            "notifyOption": notify_option,
        }
        
        # Делегируем сохранение в refresh_operations
        try:
            dataset_id = self.current_dataset.get('id')
            dataset_name = self.current_dataset.get('name', dataset_id)
            self.log_message(f"Сохранение расписания для {dataset_name}...")
            self.status_bar.showMessage("Сохранение расписания...")
            self.refresh_operations.update_refresh_schedule(
                self.current_workspace, dataset_id, payload
            )
            self.log_message("✓ Расписание сохранено")
            self.status_bar.showMessage("Расписание сохранено", 3000)
            self.refresh_data()
        except Exception as e:
            self.log_message(f"✗ Ошибка сохранения расписания: {e}")
            self.status_bar.showMessage("Ошибка сохранения расписания", 5000)

    def delete_schedule(self):
        """Удаляет расписание для выбранного датасета."""
        if not self.current_dataset or not self.current_workspace:
            self.log_message("Не выбран датасет или рабочая область")
            return
        try:
            dataset_id = self.current_dataset.get('id')
            dataset_name = self.current_dataset.get('name', dataset_id)
            self.log_message(f"Отключение расписания для {dataset_name}...")
            self.status_bar.showMessage("Удаление расписания...")
            self.refresh_operations.disable_auto_refresh(self.current_workspace, dataset_id)
            self.log_message("✓ Запланированное обновление отключено")
            self.status_bar.showMessage("Расписание отключено", 3000)
            self.refresh_data()
        except Exception as e:
            self.log_message(f"✗ Ошибка удаления расписания: {e}")
            self.status_bar.showMessage("Ошибка удаления расписания", 5000)

    def load_schedule_to_ui(self, schedule_data: dict):
        """
        Загружает данные расписания в элементы управления UI.
        
        Args:
            schedule_data: Словарь с данными расписания (ключи: enabled, days, times, localTimeZoneId, notifyOption)
        """
        if not schedule_data:
            # Если расписание отсутствует, сбрасываем UI
            self._clear_schedule_ui()
            return
        
        # enabled
        if hasattr(self, 'schedule_enabled_cb'):
            self.schedule_enabled_cb.setChecked(schedule_data.get('enabled', False))
        
        # days
        days = schedule_data.get('days', [])
        if hasattr(self, 'schedule_day_checks'):
            for api_name, cb in self.schedule_day_checks.items():
                cb.setChecked(api_name in days)
        
        # times
        times = schedule_data.get('times', [])
        if hasattr(self, 'schedule_times_list'):
            self.schedule_times_list.clear()
            for time_str in times:
                self.schedule_times_list.addItem(time_str)
        
        # localTimeZoneId
        tz_id = schedule_data.get('localTimeZoneId', 'UTC')
        if hasattr(self, 'schedule_tz_combo'):
            index = self.schedule_tz_combo.findText(tz_id)
            if index >= 0:
                self.schedule_tz_combo.setCurrentIndex(index)
            else:
                # Если часовой пояс не найден, добавляем его
                self.schedule_tz_combo.addItem(tz_id)
                self.schedule_tz_combo.setCurrentIndex(self.schedule_tz_combo.count() - 1)
        
        # notifyOption
        notify = schedule_data.get('notifyOption', 'MailOnFailure')
        if hasattr(self, 'schedule_notify_combo'):
            index = self.schedule_notify_combo.findData(notify)
            if index >= 0:
                self.schedule_notify_combo.setCurrentIndex(index)
            else:
                # Если опция не найдена, устанавливаем по умолчанию
                self.schedule_notify_combo.setCurrentIndex(0)

    def _clear_schedule_ui(self):
        """Сбрасывает элементы управления расписанием в состояние по умолчанию."""
        if hasattr(self, 'schedule_enabled_cb'):
            self.schedule_enabled_cb.setChecked(False)
        if hasattr(self, 'schedule_day_checks'):
            for cb in self.schedule_day_checks.values():
                cb.setChecked(False)
        if hasattr(self, 'schedule_times_list'):
            self.schedule_times_list.clear()
        if hasattr(self, 'schedule_tz_combo'):
            self.schedule_tz_combo.setCurrentIndex(0)
        if hasattr(self, 'schedule_notify_combo'):
            self.schedule_notify_combo.setCurrentIndex(0)