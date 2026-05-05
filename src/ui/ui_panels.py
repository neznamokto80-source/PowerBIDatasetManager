#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль панелей пользовательского интерфейса.
Содержит методы создания левой, центральной панелей и вкладок.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QTabWidget,
    QTextEdit, QFormLayout, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class UIPanels:
    """Класс для создания панелей интерфейса."""
    
    def __init__(self, main_window):
        """
        Инициализация с ссылкой на главное окно.
        
        Args:
            main_window: Экземпляр PowerBIMonitorUI
        """
        self.main = main_window
    
    def create_left_panel(self):
        """Создает левую панель навигации."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Кнопка подключения
        connect_btn = QPushButton("Подключить")
        connect_btn.clicked.connect(self.main.connect_to_powerbi)
        layout.addWidget(connect_btn)
        
        # Группа "Рабочие области"
        workspace_group = QGroupBox("Рабочие области")
        workspace_layout = QVBoxLayout()
        
        self.main.workspace_combo = QComboBox()
        self.main.workspace_combo.currentIndexChanged.connect(self.main.on_workspace_selected)
        workspace_layout.addWidget(self.main.workspace_combo)
        
        refresh_workspaces_btn = QPushButton("Обновить список")
        refresh_workspaces_btn.clicked.connect(self.main.load_workspaces)
        workspace_layout.addWidget(refresh_workspaces_btn)
        
        workspace_group.setLayout(workspace_layout)
        layout.addWidget(workspace_group)
        
        # Группа "Датасеты"
        dataset_group = QGroupBox("Датасеты")
        dataset_layout = QVBoxLayout()
        
        self.main.dataset_tree = QTreeWidget()
        self.main.dataset_tree.setHeaderLabels(["Name", "Status", "Refresh"])
        self.main.dataset_tree.itemClicked.connect(self.main.on_dataset_selected)
        dataset_layout.addWidget(self.main.dataset_tree)
        
        refresh_datasets_btn = QPushButton("Обновить статусы")
        refresh_datasets_btn.clicked.connect(self.main.load_datasets)
        dataset_layout.addWidget(refresh_datasets_btn)
        
        dataset_group.setLayout(dataset_layout)
        layout.addWidget(dataset_group)
        
        # Группа "Фильтры"
        filter_group = QGroupBox("Фильтры")
        filter_layout = QVBoxLayout()
        
        self.main.filter_enabled = QCheckBox("Только с включенным обновлением")
        self.main.filter_enabled.stateChanged.connect(self.main.apply_filters)
        filter_layout.addWidget(self.main.filter_enabled)
        
        self.main.filter_recent = QCheckBox("Только с выключенным обновлением")
        self.main.filter_recent.stateChanged.connect(self.main.apply_filters)
        filter_layout.addWidget(self.main.filter_recent)
        
        # Новые фильтры
        self.main.filter_errors = QCheckBox("с ошибками")
        self.main.filter_errors.stateChanged.connect(self.main.apply_filters)
        filter_layout.addWidget(self.main.filter_errors)
        
        self.main.filter_except_not_use = QCheckBox("Все кроме not_use")
        self.main.filter_except_not_use.stateChanged.connect(self.main.apply_filters)
        filter_layout.addWidget(self.main.filter_except_not_use)
        
        self.main.filter_in_progress = QCheckBox("В процессе обновления")
        self.main.filter_in_progress.stateChanged.connect(self.main.apply_filters)
        filter_layout.addWidget(self.main.filter_in_progress)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Группа "Мониторинг"
        monitor_group = QGroupBox("Мониторинг в реальном времени")
        monitor_layout = QVBoxLayout()

        self.main.monitor_status = QLabel("Мониторинг не активен")
        monitor_layout.addWidget(self.main.monitor_status)

        self.main.start_monitor_btn = QPushButton("Запустить мониторинг")
        self.main.start_monitor_btn.clicked.connect(self.main.start_monitoring)
        monitor_layout.addWidget(self.main.start_monitor_btn)

        self.main.stop_monitor_btn = QPushButton("Остановить мониторинг")
        self.main.stop_monitor_btn.clicked.connect(self.main.stop_monitoring)
        self.main.stop_monitor_btn.setEnabled(False)
        monitor_layout.addWidget(self.main.stop_monitor_btn)

        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        layout.addStretch()
        return panel
        
    def create_center_panel(self):
        """Создает центральную панель с информацией."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Вкладки
        self.main.tab_widget = QTabWidget()
        
        # Вкладка "Обзор"
        overview_tab = self.create_overview_tab()
        self.main.tab_widget.addTab(overview_tab, "Обзор")
        
        # Вкладка "Детали"
        details_tab = self.create_details_tab()
        self.main.tab_widget.addTab(details_tab, "Детали")
        
        # Вкладка "История обновлений" удалена по требованию
        # history_tab = self.create_history_tab()
        # self.main.tab_widget.addTab(history_tab, "История")
        
        # Вкладка "Логи"
        logs_tab = self.create_logs_tab()
        self.main.tab_widget.addTab(logs_tab, "Логи")
        
        layout.addWidget(self.main.tab_widget)
        return panel
        
    def create_overview_tab(self):
        """Создает вкладку обзора."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Статистика
        stats_group = QGroupBox("Статистика")
        stats_layout = QHBoxLayout()
        
        self.main.total_datasets_label = QLabel("Всего датасетов: 0")
        stats_layout.addWidget(self.main.total_datasets_label)
        
        self.main.enabled_refresh_label = QLabel("С обновлением: 0")
        stats_layout.addWidget(self.main.enabled_refresh_label)
        
        self.main.failed_refresh_label = QLabel("С ошибками: 0")
        stats_layout.addWidget(self.main.failed_refresh_label)
        
        self.main.last_update_label = QLabel("Последнее обновление: -")
        stats_layout.addWidget(self.main.last_update_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Таблица датасетов
        self.main.dataset_table = QTableWidget()
        self.main.dataset_table.setColumnCount(7)
        self.main.dataset_table.setHorizontalHeaderLabels([
            "Название", "Рабочая область", "ID датасета", "Status",
            "Последнее обновление", "Следующее", "Автообновление"
        ])
        # Настройка ширины колонок: колонка статуса уже
        self.main.dataset_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.main.dataset_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.main.dataset_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.main.dataset_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.main.dataset_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.main.dataset_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.main.dataset_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.main.dataset_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.main.dataset_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.main.dataset_table.itemDoubleClicked.connect(self.main.on_dataset_double_clicked)
        # Контекстное меню
        self.main.dataset_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main.dataset_table.customContextMenuRequested.connect(self.main.show_context_menu)
        
        layout.addWidget(self.main.dataset_table)
        
        # Прогресс-бар для обновлений
        self.main.progress_bar = QProgressBar()
        self.main.progress_bar.setVisible(False)
        layout.addWidget(self.main.progress_bar)
        
        return tab
        
    def create_details_tab(self):
        """Создает вкладку детальной информации."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Информация о выбранном датасете
        self.main.details_group = QGroupBox("Информация о датасете")
        details_layout = QFormLayout()
        
        self.main.detail_name = QLabel("-")
        details_layout.addRow("Название:", self.main.detail_name)
        
        self.main.detail_id = QLabel("-")
        details_layout.addRow("ID:", self.main.detail_id)
        
        self.main.detail_workspace = QLabel("-")
        details_layout.addRow("Рабочая область:", self.main.detail_workspace)
        
        self.main.detail_refresh_status = QLabel("-")
        details_layout.addRow("Статус обновления:", self.main.detail_refresh_status)
        
        self.main.detail_last_refresh = QLabel("-")
        details_layout.addRow("Последнее обновление:", self.main.detail_last_refresh)
        
        self.main.detail_next_refresh = QLabel("-")
        details_layout.addRow("Следующее обновление:", self.main.detail_next_refresh)
        
        self.main.detail_schedule = QLabel("-")
        details_layout.addRow("Расписание:", self.main.detail_schedule)
        
        # Добавляем поле для статуса автоматического обновления
        self.main.detail_auto_refresh = QLabel("-")
        details_layout.addRow("Автообновление:", self.main.detail_auto_refresh)
        
        # Добавляем поле для деталей последнего обновления
        self.main.detail_last_refresh_details = QLabel("-")
        details_layout.addRow("Детали последнего обновления:", self.main.detail_last_refresh_details)
        
        self.main.details_group.setLayout(details_layout)
        layout.addWidget(self.main.details_group)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.main.enable_btn = QPushButton("Включить обновление")
        self.main.enable_btn.clicked.connect(self.main.enable_auto_refresh)
        self.main.enable_btn.setEnabled(False)
        button_layout.addWidget(self.main.enable_btn)
        
        self.main.disable_btn = QPushButton("Отключить обновление")
        self.main.disable_btn.clicked.connect(self.main.disable_auto_refresh)
        self.main.disable_btn.setEnabled(False)
        button_layout.addWidget(self.main.disable_btn)
        
        self.main.manual_refresh_btn = QPushButton("Запустить обновление")
        self.main.manual_refresh_btn.clicked.connect(self.main.trigger_manual_refresh)
        self.main.manual_refresh_btn.setEnabled(False)
        button_layout.addWidget(self.main.manual_refresh_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        return tab
    
    def create_history_tab(self):
        """Создает вкладку истории обновлений."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.main.history_table = QTableWidget()
        self.main.history_table.setColumnCount(5)
        self.main.history_table.setHorizontalHeaderLabels([
            "Время начала", "Время окончания", "Статус", "Тип", "Длительность"
        ])
        self.main.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.main.history_table)
        return tab
    
    def create_logs_tab(self):
        """Создает вкладку логов."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.main.logs_text = QTextEdit()
        self.main.logs_text.setReadOnly(True)
        self.main.logs_text.setFont(QFont("Courier", 10))
        
        layout.addWidget(self.main.logs_text)
        return tab