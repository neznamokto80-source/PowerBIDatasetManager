#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно приложения мониторинга Power BI.
Содержит основной интерфейс и управление состоянием приложения.
"""

import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from src.ui.ui_components import UIComponents
from src.ui.theme_colors import apply_theme_to_app

# Импорт классов методов
from src.ui.methods.connection import ConnectionMethods
from src.ui.methods.data_loading import DataLoadingMethods


class QTextEditLogHandler(logging.Handler):
    """Обработчик логов, который записывает сообщения в QTextEdit."""
    
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        # Устанавливаем формат, соответствующий настройкам basicConfig
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        """Записывает запись лога в QTextEdit."""
        try:
            msg = self.format(record)
            # Используем invokeMethod для потокобезопасного обновления UI
            from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QThread
            from PyQt6.QtWidgets import QApplication
            # Проверяем, что text_edit существует
            if self.text_edit is None:
                return
            app = QApplication.instance()
            if app is None:
                # Если приложение не существует, просто добавляем напрямую (редкий случай)
                self.text_edit.append(msg)
                return
            # Если мы в главном потоке, можно вызывать напрямую
            if QThread.currentThread() == app.thread():
                self.text_edit.append(msg)
            else:
                QMetaObject.invokeMethod(self.text_edit, "append", Qt.ConnectionType.QueuedConnection, Q_ARG(str, msg))
        except Exception as e:
            # Логируем ошибку в консоль, чтобы не потерять
            import sys, traceback
            print(f"Ошибка в QTextEditLogHandler: {e}", file=sys.stderr)
            traceback.print_exc()
            self.handleError(record)
from src.ui.methods.ui_state import UIStateMethods
from src.ui.methods.event_handlers import EventHandlers
from src.ui.methods.filtering import FilteringMethods
from src.ui.methods.monitoring import MonitoringMethods
from src.ui.methods.refresh_management import RefreshManagementMethods
from src.ui.methods.help_methods import HelpMethods

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
        self.current_theme = "Светлая"  # Текущая тема по умолчанию
        
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
        self.help_methods = HelpMethods(self)
    
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
        
        # Панель с кнопкой подключения, переключателем темы и справкой (справа вверху)
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        
        # Кнопка подключения (слева)
        self.connect_btn = QPushButton("Подключить")
        self.connect_btn.clicked.connect(self.connect_to_powerbi)
        top_layout.addWidget(self.connect_btn)
        
        # Кнопка тестовых данных
        self.test_data_btn = QPushButton("Тестовые данные")
        self.test_data_btn.clicked.connect(self.data_loading_methods.load_test_data)
        top_layout.addWidget(self.test_data_btn)
        
        top_layout.addStretch()
        
        # Кнопка переключения темы
        self.theme_btn = QPushButton("Светлая/Тёмная")
        self.theme_btn.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.theme_btn)
        
        # Кнопка справки
        self.help_btn = QPushButton("Справка")
        self.help_btn.clicked.connect(self.help_methods.show_help)
        top_layout.addWidget(self.help_btn)
        
        main_layout.addWidget(top_panel)
        
        # Основной вертикальный разделитель: сверху - контент, снизу - логи
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Горизонтальный разделитель для левой и центральной панели
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель (навигация)
        left_panel = self.ui_components.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Центральная панель (контент)
        center_panel = self.ui_components.create_center_panel()
        content_splitter.addWidget(center_panel)
        
        content_splitter.setSizes([300, 800])
        main_splitter.addWidget(content_splitter)
        
        # Панель логов (внизу)
        logs_panel = self.ui_components.create_logs_panel()
        main_splitter.addWidget(logs_panel)
        
        # Добавляем обработчик логов в QTextEdit
        if hasattr(self, 'logs_text'):
            log_handler = QTextEditLogHandler(self.logs_text)
            log_handler.setLevel(logging.INFO)
            logging.getLogger().addHandler(log_handler)
            # Убираем дублирование сообщений (если уже есть другие обработчики)
            # Но оставляем FileHandler и StreamHandler
            # Можно также установить уровень для корневого логгера, но он уже настроен
        else:
            logging.warning("logs_text не найден, обработчик логов не добавлен")
        
        main_splitter.setSizes([600, 200])
        main_layout.addWidget(main_splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        
        # Прогресс-бар теперь находится во вкладке "Обзор" (см. ui_panels.create_overview_tab)
        # self.progress_bar создаётся там
        
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
    
    def enable_auto_refresh_selected(self, datasets):
        """Включает автоматическое обновление для выбранных датасетов."""
        return self.refresh_management_methods.enable_auto_refresh_selected(datasets)
    
    def disable_auto_refresh_selected(self, datasets):
        """Отключает автоматическое обновление для выбранных датасетов."""
        return self.refresh_management_methods.disable_auto_refresh_selected(datasets)
    
    def trigger_manual_refresh_selected(self, datasets):
        """Запускает ручное обновление для выбранных датасетов."""
        return self.refresh_management_methods.trigger_manual_refresh_selected(datasets)

    def edit_refresh_schedule(self):
        """Диалог редактирования расписания обновления для выбранного датасета."""
        return self.refresh_management_methods.edit_refresh_schedule()

    def change_theme(self, theme_name):
        """Изменяет тему интерфейса."""
        # Сохраняем текущую тему
        self.current_theme = theme_name
        
        # Применяем тему через модуль theme_colors
        apply_theme_to_app(theme_name)
        
        # Обновляем статус бар для отображения текущей темы
        self.status_bar.showMessage(f"Тема изменена на: {theme_name}", 3000)
    
    def toggle_theme(self):
        """Переключает тему между светлой и тёмной."""
        if self.current_theme == "Светлая":
            new_theme = "Тёмная"
        else:
            new_theme = "Светлая"
        self.change_theme(new_theme)
    