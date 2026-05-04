#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно приложения мониторинга Power BI.
Содержит основной интерфейс и управление состоянием приложения.
"""

import logging
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QGroupBox, QTextEdit,
    QTabWidget, QMessageBox, QProgressBar, QSplitter, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QToolBar, QStatusBar, QDialog,
    QFormLayout, QLineEdit, QTimeEdit, QCheckBox, QSpinBox,
    QDialogButtonBox, QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction, QPalette, QColor

from src.core.dependencies import DependencyManager
from src.core.powerbi_client import PowerBIClient, parse_utc_to_local
from src.core.refresh_manager import RefreshManager, create_default_schedule
from src.ui.ui_components import UIComponents
from src.integration.ui_integration import UIIntegration, UIDataProvider

# Импорт классов методов
from src.ui.methods.connection import ConnectionMethods
from src.ui.methods.data_loading import DataLoadingMethods
from src.ui.methods.ui_state import UIStateMethods
from src.ui.methods.event_handlers import EventHandlers
from src.ui.methods.filtering import FilteringMethods
from src.ui.methods.monitoring import MonitoringMethods
from src.ui.methods.refresh_management import RefreshManagementMethods

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
        
        # Инициализация компонентов UI
        self.ui_components = UIComponents(self)
        
        # Инициализация классов методов
        self._init_method_classes()
        
        self.init_ui()
        self.initialize_backend()
    
    def _init_method_classes(self):
        """Инициализирует классы методов."""
        self.connection_methods = ConnectionMethods(self)
        self.data_loading_methods = DataLoadingMethods(self)
        self.ui_state_methods = UIStateMethods(self)
        self.event_handlers = EventHandlers(self)
        self.filtering_methods = FilteringMethods(self)
        self.monitoring_methods = MonitoringMethods(self)
        self.refresh_management_methods = RefreshManagementMethods(self)
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        self.setWindowTitle("Power BI Dataset Monitor & Manager")
        self.setGeometry(100, 100, 1400, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        
        # Панель инструментов удалена по требованию
        # self.ui_components.create_toolbar()
        
        # Разделитель для основной области
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель (навигация)
        left_panel = self.ui_components.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Центральная панель (контент)
        center_panel = self.ui_components.create_center_panel()
        splitter.addWidget(center_panel)
        
        # Правая панель удалена по требованию
        # right_panel = self.ui_components.create_right_panel()
        # splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 1000])
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        
        # Таймер для обновления данных (не запускается автоматически)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        # Таймер не запускается - будет запускаться только при включении мониторинга
    
    # Делегирование методов классам методов
    
    def initialize_backend(self):
        """Инициализация бэкенда приложения (без автоматического подключения)."""
        return self.connection_methods.initialize_backend()
    
    def connect_to_powerbi(self):
        """Подключение к Power BI."""
        return self.connection_methods.connect_to_powerbi()
    
    def refresh_data(self):
        """Обновление данных."""
        return self.data_loading_methods.refresh_data()
    
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
        return self.ui_state_methods.update_ui_for_disconnected_state()
    
    def update_ui_for_connected_state(self):
        """Обновляет UI для состояния 'подключено'."""
        return self.ui_state_methods.update_ui_for_connected_state()
    
    def log_message(self, message: str):
        """Добавляет сообщение в лог."""
        return self.ui_state_methods.log_message(message)
    
    def on_workspace_selected(self, index):
        """Обработчик выбора рабочей области."""
        return self.event_handlers.on_workspace_selected(index)
    
    def on_dataset_selected(self, item, column):
        """Обработчик выбора датасета."""
        return self.event_handlers.on_dataset_selected(item, column)
    
    def on_dataset_double_clicked(self, item):
        """Обработчик двойного клика по датасету."""
        return self.event_handlers.on_dataset_double_clicked(item)
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы датасетов."""
        return self.event_handlers.show_context_menu(position)
    
    def apply_filters(self):
        """Применяет фильтры к списку датасетов."""
        return self.filtering_methods.apply_filters()
    
    def start_monitoring(self):
        """Запускает мониторинг в реальном времени."""
        return self.monitoring_methods.start_monitoring()
    
    def stop_monitoring(self):
        """Останавливает мониторинг в реальном времени."""
        return self.monitoring_methods.stop_monitoring()
    
    def enable_auto_refresh(self):
        """Включает автоматическое обновление для выбранного датасета."""
        return self.refresh_management_methods.enable_auto_refresh()
    
    def disable_auto_refresh(self):
        """Отключает автоматическое обновление для выбранного датасета."""
        return self.refresh_management_methods.disable_auto_refresh()
    
    def trigger_manual_refresh(self):
        """Запускает ручное обновление выбранного датасета."""
        return self.refresh_management_methods.trigger_manual_refresh()