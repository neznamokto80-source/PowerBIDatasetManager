#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно приложения мониторинга Power BI.
Содержит основной интерфейс и управление состоянием приложения.
"""

import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from src.ui.ui_components import UIComponents
from src.ui.theme_colors import apply_theme_to_app

# Импорт классов операций (после рефакторинга)
from src.core.connection import ConnectionMethods
from src.operations.data_loading_ops import DataLoadingMethods
from src.operations.ui_operations import UIOperations
from src.operations.data_filtering_ops import DataFilteringOperations
from src.operations.refresh_operations import RefreshOperations, ProgressManager
from src.utils.log_handler import QTextEditLogHandler

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
        self.current_theme = "Светлая"  # Текущая тема интерфейса
        
        # Инициализация компонентов UI
        self.ui_components = UIComponents(self)
        
        # Инициализация классов методов
        self._init_method_classes()
        
        self.init_ui()
        self.initialize_backend()
    
    def _init_method_classes(self):
        """Инициализирует классы операций (после рефакторинга)."""
        self.connection_methods = ConnectionMethods(self)
        self.data_loading_methods = DataLoadingMethods(self)
        self.ui_operations = UIOperations(self)
        self.data_filtering_operations = DataFilteringOperations(self)
        self.refresh_operations = RefreshOperations(self)
        self.progress_manager = ProgressManager(self)
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        self.setWindowTitle("Power BI Dataset Monitor & Manager")
        self.setGeometry(100, 100, 1400, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        
        # Панель с отдельными кнопками (вместо панели инструментов)
        button_panel = self.ui_components.create_button_panel()
        main_layout.addWidget(button_panel)
        
        # Вертикальный разделитель для основной области и логов
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Горизонтальный разделитель для левой и центральной панели
        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        
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
        return self.connection_methods.connect_to_powerbi()
    
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
    
    def enable_auto_refresh(self):
        """Включает автоматическое обновление для выбранного датасета."""
        return self.refresh_operations.enable_auto_refresh()
    
    def disable_auto_refresh(self):
        """Отключает автоматическое обновление для выбранного датасета."""
        return self.refresh_operations.disable_auto_refresh()
    
    def trigger_manual_refresh(self):
        """Запускает ручное обновление выбранного датасета."""
        return self.refresh_operations.trigger_manual_refresh()

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
        if hasattr(self, 'client') and self.client:
            self.client.set_debug_path(debug_path)
        self.log_message(f"Сохранение сырых логов {'включено' if debug_enabled else 'выключено'}")

    def toggle_theme(self, state):
        """
        Переключает тему интерфейса между светлой и тёмной.

        Args:
            state: Состояние чекбокса (0 - выключено/светлая, 2 - включено/тёмная)
        """
        dark_enabled = state == 2  # Qt.Checked == 2
        new_theme = "Тёмная" if dark_enabled else "Светлая"
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