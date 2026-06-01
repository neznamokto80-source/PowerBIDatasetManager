#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль панелей пользовательского интерфейса.
Содержит методы создания левой, центральной панелей и вкладок.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QGroupBox, QTreeWidget, QCheckBox, QRadioButton, QTableWidget, QHeaderView,
    QAbstractItemView, QTabWidget, QTextEdit, QFormLayout,
    QProgressBar, QLineEdit, QListWidget, QGridLayout, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor


from .widgets import (
    create_group_box,
    create_button,
    create_table_widget,
    create_tree_widget,
    create_label,
    create_progress_bar,
    create_text_edit,
    create_combo_box,
    create_check_box,
    create_tab_widget
)


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
        
        # Кнопка подключения теперь в верхней панели
        
        # Группа "Рабочие области"
        workspace_layout = QVBoxLayout()
        
        self.main.workspace_combo = create_combo_box()
        self.main.workspace_combo.currentIndexChanged.connect(self.main.on_workspace_selected)
        workspace_layout.addWidget(self.main.workspace_combo)
        
        refresh_workspaces_btn = create_button("Обновить список", callback=self.main.load_workspaces)
        workspace_layout.addWidget(refresh_workspaces_btn)
        
        workspace_group = create_group_box("Рабочие области", workspace_layout)
        self.main.workspace_group = workspace_group  # сохраняем для изменения заголовка
        layout.addWidget(workspace_group)
        
        # Группа "Датасеты" удалена по требованию
        # (выбор датасета теперь только через таблицу в центральной панели)
        # Создаем дерево датасетов как заглушку (не отображается) для совместимости кода
        self.main.dataset_tree = QTreeWidget()
        self.main.dataset_tree.setHeaderLabels(["Название", "Статус", "Обновление"])
        
        # Группа "Фильтры"
        filter_layout = QVBoxLayout()
        
        # === Фильтры для Power BI Service (облако) ===
        self.main.filter_enabled = create_check_box("Только с включенным обновлением")
        self.main.filter_enabled.stateChanged.connect(lambda state, cb=self.main.filter_enabled: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_enabled)
        
        self.main.filter_recent = create_check_box("Только с выключенным обновлением")
        self.main.filter_recent.stateChanged.connect(lambda state, cb=self.main.filter_recent: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_recent)
        
        # Новые фильтры
        self.main.filter_errors = create_check_box("С ошибками при обновлении")
        self.main.filter_errors.stateChanged.connect(lambda state, cb=self.main.filter_errors: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_errors)
        
        self.main.filter_except_not_use = create_check_box("Все кроме not_use")
        self.main.filter_except_not_use.stateChanged.connect(lambda state, cb=self.main.filter_except_not_use: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_except_not_use)
        
        self.main.filter_in_progress = create_check_box("В процессе обновления")
        self.main.filter_in_progress.stateChanged.connect(lambda state, cb=self.main.filter_in_progress: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_in_progress)
        
        # === Фильтры для PBIRS (сервер) ===
        self.main.filter_pbirs_no_schedule = create_check_box("Без расписаний")
        self.main.filter_pbirs_no_schedule.stateChanged.connect(lambda state, cb=self.main.filter_pbirs_no_schedule: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_pbirs_no_schedule)
        
        self.main.filter_pbirs_no_auth = create_check_box("Без аутентификации")
        self.main.filter_pbirs_no_auth.stateChanged.connect(lambda state, cb=self.main.filter_pbirs_no_auth: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_pbirs_no_auth)
        
        self.main.filter_pbirs_success = create_check_box("Успешно обновлённые")
        self.main.filter_pbirs_success.stateChanged.connect(lambda state, cb=self.main.filter_pbirs_success: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_pbirs_success)
        
        self.main.filter_pbirs_errors = create_check_box("С ошибками последнего обновления")
        self.main.filter_pbirs_errors.stateChanged.connect(lambda state, cb=self.main.filter_pbirs_errors: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_pbirs_errors)
        
        self.main.filter_pbirs_in_progress = create_check_box("В процессе обновления")
        self.main.filter_pbirs_in_progress.stateChanged.connect(lambda state, cb=self.main.filter_pbirs_in_progress: self.main.apply_filters())
        filter_layout.addWidget(self.main.filter_pbirs_in_progress)
        
        filter_group = create_group_box("Фильтры", filter_layout)
        layout.addWidget(filter_group)
        
        # По умолчанию скрываем PBIRS-фильтры (показываются только в режиме server)
        self._set_pbirs_filters_visible(False)

        # Группа "Мониторинг"
        monitor_layout = QVBoxLayout()

        self.main.monitor_status = create_label("Мониторинг не активен")
        monitor_layout.addWidget(self.main.monitor_status)

        # RadioButton для выбора периодичности (единичный выбор)
        period_layout = QHBoxLayout()
        period_layout.setSpacing(5)

        self.main.monitor_radio_15 = QRadioButton("15 сек")
        self.main.monitor_radio_30 = QRadioButton("30 сек")
        self.main.monitor_radio_60 = QRadioButton("60 сек")

        # По умолчанию выбран 30 сек
        self.main.monitor_radio_30.setChecked(True)

        # При клике на radio button обновляем заголовок группы и интервал
        self.main.monitor_radio_15.clicked.connect(self.main._update_monitor_group_title)
        self.main.monitor_radio_30.clicked.connect(self.main._update_monitor_group_title)
        self.main.monitor_radio_60.clicked.connect(self.main._update_monitor_group_title)

        period_layout.addWidget(self.main.monitor_radio_15)
        period_layout.addWidget(self.main.monitor_radio_30)
        period_layout.addWidget(self.main.monitor_radio_60)
        monitor_layout.addLayout(period_layout)

        self.main.start_monitor_btn = create_button("Запустить мониторинг", callback=self.main.start_monitoring)
        monitor_layout.addWidget(self.main.start_monitor_btn)

        self.main.stop_monitor_btn = create_button("Остановить мониторинг", callback=self.main.stop_monitoring)
        self.main.stop_monitor_btn.setEnabled(False)
        monitor_layout.addWidget(self.main.stop_monitor_btn)

        self.main.monitor_group = create_group_box("Мониторинг (периодичность опроса 30 сек)", monitor_layout)
        layout.addWidget(self.main.monitor_group)

        # Группа "Настройки"
        settings_layout = QVBoxLayout()
        
        # Чекбокс темы
        self.main.theme_checkbox = create_check_box("Тёмная тема")
        self.main.theme_checkbox.stateChanged.connect(self.main.toggle_theme)
        settings_layout.addWidget(self.main.theme_checkbox)
        
        # Чекбокс сырых логов
        self.main.debug_checkbox = create_check_box("Сохранять сырые логи (debug)")
        self.main.debug_checkbox.stateChanged.connect(self.main.toggle_debug_logging)
        settings_layout.addWidget(self.main.debug_checkbox)
        
        settings_group = create_group_box("Настройки", settings_layout)
        layout.addWidget(settings_group)

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
        
        # Вкладка "Отчёты PBIRS" (скрыта по умолчанию, показывается только в режиме server)
        pbirs_reports_tab = self.create_pbirs_reports_tab()
        self.main.tab_widget.addTab(pbirs_reports_tab, "Отчёты PBIRS")
        
        # Вкладка "Источники PBIRS" (скрыта по умолчанию, показывается только в режиме server)
        pbirs_sources_tab = self.create_pbirs_sources_tab()
        self.main.tab_widget.addTab(pbirs_sources_tab, "Источники PBIRS")
        
        # Вкладка "Детали PBIRS" (скрыта по умолчанию, показывается только в режиме server)
        pbirs_details_tab = self.create_pbirs_details_tab()
        self.main.tab_widget.addTab(pbirs_details_tab, "Детали PBIRS")
        
        # Вкладка "История обновлений" удалена по требованию
        # history_tab = self.create_history_tab()
        # self.main.tab_widget.addTab(history_tab, "История")
        
        # Вкладка "Логи" удалена - логи теперь в нижнем блоке
        # logs_tab = self.create_logs_tab()
        # self.main.tab_widget.addTab(logs_tab, "Логи")
        
        # Блок статистики PBIRS (справа от заголовков вкладок, только для режима server)
        self.main.pbirs_stats_widget = QWidget()
        stats_layout = QHBoxLayout(self.main.pbirs_stats_widget)
        stats_layout.setContentsMargins(5, 0, 5, 0)
        stats_layout.setSpacing(10)
        
        self.main.pbirs_stats_total = QLabel("Всего: 0")
        self.main.pbirs_stats_errors = QLabel("С ошибками: 0")
        self.main.pbirs_stats_size = QLabel("Общий размер: 0 МБ")
        
        for label in [self.main.pbirs_stats_total, self.main.pbirs_stats_errors, self.main.pbirs_stats_size]:
            label.setStyleSheet("font-weight: bold; padding: 2px 8px;")
            stats_layout.addWidget(label)
        
        self.main.tab_widget.setCornerWidget(self.main.pbirs_stats_widget, Qt.Corner.TopRightCorner)
        self.main.pbirs_stats_widget.setVisible(False)  # По умолчанию скрыт
        
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
        
        # Фильтр по названию датасета
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Фильтр по названию:")
        self.main.dataset_name_filter = QLineEdit()
        self.main.dataset_name_filter.setPlaceholderText("Введите часть названия...")
        self.main.dataset_name_filter.textChanged.connect(self.main.apply_filters)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.main.dataset_name_filter)
        layout.addLayout(filter_layout)
        
        # Таблица датасетов
        self.main.dataset_table = QTableWidget()
        self.main.dataset_table.setColumnCount(7)
        self.main.dataset_table.setHorizontalHeaderLabels([
            "Название", "Рабочая область", "ID датасета", "Status",
            "Последнее обновление", "Следующее", "Автообновление"
        ])
        # Скрыть столбец ID датасета
        self.main.dataset_table.setColumnHidden(2, True)
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
        
        # Прогресс-бар для обновлений (как в примере powerbi_monitor_ui.py)
        self.main.progress_bar = QProgressBar()
        self.main.progress_bar.setVisible(True)  # Видим по умолчанию
        self.main.progress_bar.setMinimumHeight(20)
        # Убрано ограничение по ширине - растягивается по ширине окна
        # Формат: только процент выполнения
        self.main.progress_bar.setFormat("%p%")
        self.main.progress_bar.setRange(0, 100)
        self.main.progress_bar.setValue(0)
        layout.addWidget(self.main.progress_bar)
        
        return tab
        
    def create_details_tab(self):
        """Создает вкладку детальной информации."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Фильтр выбора датасета с кнопками управления
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Выберите датасет:")
        self.main.details_dataset_combo = QComboBox()
        self.main.details_dataset_combo.setPlaceholderText("-- Выберите датасет --")
        self.main.details_dataset_combo.currentIndexChanged.connect(self.main.on_details_dataset_selected)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.main.details_dataset_combo)
        
        # Кнопки управления
        self.main.enable_btn = QPushButton("Включить обновление")
        self.main.enable_btn.clicked.connect(self.main.enable_auto_refresh)
        self.main.enable_btn.setEnabled(False)
        filter_layout.addWidget(self.main.enable_btn)
        
        self.main.disable_btn = QPushButton("Отключить обновление")
        self.main.disable_btn.clicked.connect(self.main.disable_auto_refresh)
        self.main.disable_btn.setEnabled(False)
        filter_layout.addWidget(self.main.disable_btn)
        
        self.main.manual_refresh_btn = QPushButton("Запустить обновление")
        self.main.manual_refresh_btn.clicked.connect(self.main.trigger_manual_refresh)
        self.main.manual_refresh_btn.setEnabled(False)
        filter_layout.addWidget(self.main.manual_refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Информация о выбранном датасете (два столбца)
        self.main.details_group = QGroupBox("Информация о датасете")
        details_layout = QHBoxLayout()
        
        # Левый столбец (основная информация)
        left_form = QFormLayout()
        self.main.detail_name = QLabel("-")
        left_form.addRow("Название:", self.main.detail_name)
        
        self.main.detail_id = QLabel("-")
        left_form.addRow("ID:", self.main.detail_id)
        
        self.main.detail_workspace = QLabel("-")
        left_form.addRow("Рабочая область:", self.main.detail_workspace)
        
        self.main.detail_refresh_status = QLabel("-")
        left_form.addRow("Статус обновления:", self.main.detail_refresh_status)
        
        self.main.detail_last_refresh = QLabel("-")
        left_form.addRow("Последнее обновление:", self.main.detail_last_refresh)
        
        self.main.detail_next_refresh = QLabel("-")
        left_form.addRow("Следующее обновление:", self.main.detail_next_refresh)
        
        # Правый столбец (дополнительная информация)
        right_form = QFormLayout()
        self.main.detail_schedule = QLabel("-")
        right_form.addRow("Расписание:", self.main.detail_schedule)
        
        self.main.detail_auto_refresh = QLabel("-")
        right_form.addRow("Автообновление:", self.main.detail_auto_refresh)
        
        self.main.detail_last_refresh_details = QLabel("-")
        right_form.addRow("Детали последнего обновления:", self.main.detail_last_refresh_details)
        
        # Добавляем формы в горизонтальный layout
        details_layout.addLayout(left_form)
        
        # Разделитель в виде вертикальной линии
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)
        separator.setMidLineWidth(0)
        separator.setFixedWidth(3)
        details_layout.addWidget(separator)
        
        details_layout.addLayout(right_form)
        # Удален addStretch, чтобы столбцы были одинаковой ширины
        # Устанавливаем stretch factors: левый и правый layout растягиваются одинаково, разделитель фиксирован
        details_layout.setStretch(0, 1)  # left_form
        details_layout.setStretch(1, 0)  # separator (фиксированная ширина)
        details_layout.setStretch(2, 1)  # right_form
        
        self.main.details_group.setLayout(details_layout)
        layout.addWidget(self.main.details_group)
        
        
        # Группа управления расписанием (теперь постоянно видима)
        self.main.schedule_group = QGroupBox("Управление расписанием")
        self.main.schedule_group.setVisible(True)
        schedule_layout = QHBoxLayout()
        
        # Дни недели
        days_group = QGroupBox("Дни недели")
        days_layout = QGridLayout()
        self.main.schedule_day_checks = {}
        DAY_LABELS_RU = [
            "Воскресенье", "Понедельник", "Вторник", "Среда",
            "Четверг", "Пятница", "Суббота"
        ]
        DAY_NAMES_API = [
            "Sunday", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday"
        ]
        # Размещаем в две колонки: 4 в первой, 3 во второй
        for i, (api_name, ru) in enumerate(zip(DAY_NAMES_API, DAY_LABELS_RU)):
            cb = QCheckBox(ru)
            self.main.schedule_day_checks[api_name] = cb
            row = i % 4  # 4 строки в первой колонке
            col = 0 if i < 4 else 1
            days_layout.addWidget(cb, row, col)
        days_group.setLayout(days_layout)
        schedule_layout.addWidget(days_group)
        
        # Время срабатывания
        times_group = QGroupBox("Время срабатывания (локальное время выбранного пояса)")
        times_layout = QHBoxLayout()  # Горизонтальный layout: список слева, управление справа
        
        # Список времени в две колонки
        self.main.schedule_times_list = QListWidget()
        self.main.schedule_times_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.main.schedule_times_list.setFlow(QListWidget.Flow.LeftToRight)
        self.main.schedule_times_list.setWrapping(True)
        self.main.schedule_times_list.setGridSize(QSize(80, 25))
        self.main.schedule_times_list.setFixedHeight(180)  # 6 строк * 30 высота
        times_layout.addWidget(self.main.schedule_times_list, 2)  # растягиваем
        
        # Панель управления временем справа
        time_edit_panel = QWidget()
        time_edit_layout = QVBoxLayout(time_edit_panel)
        time_edit_layout.setContentsMargins(5, 5, 5, 5)
        
        # Часы и минуты
        hours_minutes_layout = QHBoxLayout()
        hours_minutes_layout.addWidget(QLabel("Часы:"))
        self.main.schedule_hours_combo = QComboBox()
        self.main.schedule_hours_combo.addItems([f"{i:02d}" for i in range(24)])  # 00-23
        hours_minutes_layout.addWidget(self.main.schedule_hours_combo)
        hours_minutes_layout.addWidget(QLabel("Минуты:"))
        self.main.schedule_minutes_combo = QComboBox()
        self.main.schedule_minutes_combo.addItems(["00", "30"])  # только 00 и 30
        hours_minutes_layout.addWidget(self.main.schedule_minutes_combo)
        time_edit_layout.addLayout(hours_minutes_layout)
        
        # Кнопки
        self.main.schedule_add_time_btn = QPushButton("Добавить время")
        self.main.schedule_add_time_btn.clicked.connect(self.main.add_schedule_time)
        time_edit_layout.addWidget(self.main.schedule_add_time_btn)
        
        self.main.schedule_remove_time_btn = QPushButton("Удалить выбранное")
        self.main.schedule_remove_time_btn.clicked.connect(self.main.remove_schedule_time)
        time_edit_layout.addWidget(self.main.schedule_remove_time_btn)
        
        time_edit_layout.addStretch()
        times_layout.addWidget(time_edit_panel, 1)
        
        times_group.setLayout(times_layout)
        schedule_layout.addWidget(times_group)
        
        # Настройки расписания (часовой пояс, уведомления, кнопки)
        settings_group = QGroupBox("Настройки расписания")
        settings_layout = QVBoxLayout()
        
        # Часовой пояс и уведомления
        form_layout = QFormLayout()
        self.main.schedule_tz_combo = QComboBox()
        self.main.schedule_tz_combo.setEditable(True)
        DEFAULT_TIMEZONES = [
            "UTC", "Russian Standard Time", "Central Asia Standard Time",
            "Ekaterinburg Standard Time", "W. Europe Standard Time",
            "Central European Standard Time", "GMT Standard Time",
            "Eastern Standard Time", "Pacific Standard Time"
        ]
        self.main.schedule_tz_combo.addItems(DEFAULT_TIMEZONES)
        self.main.schedule_tz_combo.setCurrentText("Central Asia Standard Time")
        form_layout.addRow("Часовой пояс (Windows):", self.main.schedule_tz_combo)
        
        self.main.schedule_notify_combo = QComboBox()
        self.main.schedule_notify_combo.addItem("Без уведомлений", "NoNotification")
        self.main.schedule_notify_combo.addItem("Почта при ошибке", "MailOnFailure")
        self.main.schedule_notify_combo.addItem("Почта по завершении", "MailOnCompletion")
        self.main.schedule_notify_combo.setCurrentIndex(1)  # MailOnFailure по умолчанию
        form_layout.addRow("Уведомления:", self.main.schedule_notify_combo)
        
        self.main.schedule_enabled_cb = QCheckBox("Расписание включено")
        self.main.schedule_enabled_cb.setChecked(True)
        form_layout.addRow(self.main.schedule_enabled_cb)
        
        settings_layout.addLayout(form_layout)
        settings_layout.addStretch()
        
        # Кнопки сохранения/удаления
        schedule_buttons_layout = QHBoxLayout()
        self.main.schedule_save_btn = QPushButton("Сохранить расписание")
        self.main.schedule_save_btn.clicked.connect(self.main.save_schedule)
        self.main.schedule_delete_btn = QPushButton("Удалить расписание")
        self.main.schedule_delete_btn.clicked.connect(self.main.delete_schedule)
        schedule_buttons_layout.addWidget(self.main.schedule_save_btn)
        schedule_buttons_layout.addWidget(self.main.schedule_delete_btn)
        schedule_buttons_layout.addStretch()
        settings_layout.addLayout(schedule_buttons_layout)
        
        settings_group.setLayout(settings_layout)
        schedule_layout.addWidget(settings_group)
        
        self.main.schedule_group.setLayout(schedule_layout)
        layout.addWidget(self.main.schedule_group)
        
        layout.addStretch()
        return tab
    
    def create_pbirs_reports_tab(self):
        """Создает вкладку для отображения отчетов Power BI Report Server."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Фильтр по папке (уже есть в левой панели) - здесь можно добавить поиск
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Фильтр по названию:")
        self.main.pbirs_report_name_filter = QLineEdit()
        self.main.pbirs_report_name_filter.setPlaceholderText("Введите часть названия отчета...")
        # Подключаем фильтр
        if hasattr(self.main, 'on_pbirs_name_filter_changed'):
            self.main.pbirs_report_name_filter.textChanged.connect(self.main.on_pbirs_name_filter_changed)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.main.pbirs_report_name_filter)
        layout.addLayout(filter_layout)
        
        # Таблица отчетов
        self.main.pbirs_reports_table = QTableWidget()
        self.main.pbirs_reports_table.setColumnCount(8)
        self.main.pbirs_reports_table.setHorizontalHeaderLabels([
            "Папка", "Название отчета", "Размер (МБ)", "Тип отчета", "Источники данных",
            "Последний статус", "Последнее обновление", "Следующее обновление"
        ])
        # Настройка ширины колонок
        header = self.main.pbirs_reports_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Папка
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Название отчета
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)    # Размер (МБ)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)    # Тип отчета
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Источники данных
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Последний статус
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)    # Последнее обновление
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)    # Следующее обновление
        header.setStretchLastSection(False)
        
        self.main.pbirs_reports_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.main.pbirs_reports_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # Подключаем обработчик двойного клика
        self.main.pbirs_reports_table.doubleClicked.connect(self.main.on_pbirs_report_double_clicked)
        # Подключаем сортировку по двойному клику на заголовок колонки
        self.main.pbirs_reports_table.horizontalHeader().sectionDoubleClicked.connect(
            lambda col: self.main.sort_pbirs_table('reports', col)
        )
        
        layout.addWidget(self.main.pbirs_reports_table)
        
        return tab
    
    def create_pbirs_sources_tab(self):
        """Создает вкладку для отображения источников данных Power BI Report Server."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Панель фильтров
        filter_layout = QHBoxLayout()
        
        # Фильтр по названию отчета
        report_filter_label = QLabel("Название отчета:")
        self.main.pbirs_sources_report_filter = QLineEdit()
        self.main.pbirs_sources_report_filter.setPlaceholderText("Введите часть названия отчета...")
        # Подключаем фильтрацию по мере ввода
        self.main.pbirs_sources_report_filter.textChanged.connect(self.main.on_pbirs_sources_filter_changed)
        filter_layout.addWidget(report_filter_label)
        filter_layout.addWidget(self.main.pbirs_sources_report_filter)
        
        # Фильтр по источникам данных (ConnectionString)
        source_filter_label = QLabel("Источники:")
        self.main.pbirs_sources_source_filter = QComboBox()
        self.main.pbirs_sources_source_filter.setEditable(True)
        self.main.pbirs_sources_source_filter.setPlaceholderText("введите часть строки подключения...")
        # Подключаем фильтрацию по мере ввода
        self.main.pbirs_sources_source_filter.currentIndexChanged.connect(self.main.on_pbirs_sources_filter_changed)
        self.main.pbirs_sources_source_filter.editTextChanged.connect(self.main.on_pbirs_sources_filter_changed)
        filter_layout.addWidget(source_filter_label)
        filter_layout.addWidget(self.main.pbirs_sources_source_filter)
        
        # Фильтр по типу (Kind) с редактируемым полем и строгим соответствием
        kind_filter_label = QLabel("Тип:")
        self.main.pbirs_sources_kind_filter = QComboBox()
        self.main.pbirs_sources_kind_filter.setEditable(True)
        self.main.pbirs_sources_kind_filter.setPlaceholderText("введите тип...")
        # Подключаем фильтрацию по мере ввода
        self.main.pbirs_sources_kind_filter.currentIndexChanged.connect(self.main.on_pbirs_sources_filter_changed)
        self.main.pbirs_sources_kind_filter.editTextChanged.connect(self.main.on_pbirs_sources_filter_changed)
        filter_layout.addWidget(kind_filter_label)
        filter_layout.addWidget(self.main.pbirs_sources_kind_filter)
        
        # Фильтр по пользователю (Username)
        user_filter_label = QLabel("Пользователь:")
        self.main.pbirs_sources_user_filter = QComboBox()
        self.main.pbirs_sources_user_filter.setEditable(True)
        self.main.pbirs_sources_user_filter.setPlaceholderText("введите имя пользователя...")
        # Подключаем фильтрацию по мере ввода
        self.main.pbirs_sources_user_filter.currentIndexChanged.connect(self.main.on_pbirs_sources_filter_changed)
        self.main.pbirs_sources_user_filter.editTextChanged.connect(self.main.on_pbirs_sources_filter_changed)
        filter_layout.addWidget(user_filter_label)
        filter_layout.addWidget(self.main.pbirs_sources_user_filter)
        
        # Настраиваем пропорциональное распределение ширины
        filter_layout.setStretch(0, 1)  # Метка "Название отчета"
        filter_layout.setStretch(1, 2)  # Поле ввода названия отчета
        filter_layout.setStretch(2, 1)  # Метка "Источники"
        filter_layout.setStretch(3, 2)  # Комбобокс ConnectionString
        filter_layout.setStretch(4, 1)  # Метка "Тип"
        filter_layout.setStretch(5, 2)  # Комбобокс Тип
        filter_layout.setStretch(6, 1)  # Метка "Пользователь"
        filter_layout.setStretch(7, 2)  # Комбобокс Пользователь
        
        layout.addLayout(filter_layout)
        
        # Таблица источников данных
        self.main.pbirs_sources_table = QTableWidget()
        self.main.pbirs_sources_table.setColumnCount(6)
        self.main.pbirs_sources_table.setHorizontalHeaderLabels([
            "Папка", "Название отчета", "Источник", "Тип", "Дата изменения", "Пользователь"
        ])
        # Настройка ширины колонок
        header = self.main.pbirs_sources_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Папка
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Название отчета
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # ConnectionString
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Тип (Kind)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Дата изменения
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Пользователь
        
        self.main.pbirs_sources_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.main.pbirs_sources_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # Подключаем сортировку по двойному клику на заголовок колонки
        self.main.pbirs_sources_table.horizontalHeader().sectionDoubleClicked.connect(
            lambda col: self.main.sort_pbirs_table('sources', col)
        )
        
        layout.addWidget(self.main.pbirs_sources_table)
        
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
    def create_pbirs_details_tab(self):
        """Создает вкладку детальной информации для отчетов PBIRS с таблицей расписаний."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Верхняя панель выбора отчета
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        report_label = QLabel("Выберите Отчет:")
        self.main.pbirs_details_report_combo = QComboBox()
        self.main.pbirs_details_report_combo.setPlaceholderText("-- Выберите отчет --")
        self.main.pbirs_details_report_combo.currentIndexChanged.connect(
            self.main.on_pbirs_details_report_selected
        )
        top_layout.addWidget(report_label)
        top_layout.addWidget(self.main.pbirs_details_report_combo, 2)
        top_layout.addStretch()
        layout.addWidget(top_panel)

        # Блок информации об отчете (две колонки)
        info_group = QGroupBox("Информация об Отчете")
        info_layout = QHBoxLayout()

        # Левая колонка
        left_form = QFormLayout()
        self.main.pbirs_detail_name = QLabel("-")
        self.main.pbirs_detail_name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_form.addRow("Название:", self.main.pbirs_detail_name)
        self.main.pbirs_detail_id = QLabel("-")
        self.main.pbirs_detail_id.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_form.addRow("PowerBIReport ID:", self.main.pbirs_detail_id)
        self.main.pbirs_detail_folder = QLabel("-")
        self.main.pbirs_detail_folder.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_form.addRow("Расположение отчета:", self.main.pbirs_detail_folder)
        self.main.pbirs_detail_creator = QLabel("-")
        self.main.pbirs_detail_creator.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_form.addRow("Создатель:", self.main.pbirs_detail_creator)
        # Новые поля
        self.main.pbirs_detail_created_date = QLabel("-")
        self.main.pbirs_detail_created_date.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_form.addRow("Дата создания:", self.main.pbirs_detail_created_date)
        self.main.pbirs_detail_modified_by = QLabel("-")
        self.main.pbirs_detail_modified_by.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_form.addRow("Кем изменён:", self.main.pbirs_detail_modified_by)
        self.main.pbirs_detail_modified_date = QLabel("-")
        self.main.pbirs_detail_modified_date.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_form.addRow("Дата изменения:", self.main.pbirs_detail_modified_date)
        # Правая колонка
        right_form = QFormLayout()
        #self.main.pbirs_detail_sources = QLabel("-")
        #self.main.pbirs_detail_sources.setWordWrap(True)
        self.main.pbirs_detail_sources = QLabel("-")
        self.main.pbirs_detail_sources.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.main.pbirs_detail_sources.setWordWrap(True)
        self.main.pbirs_detail_sources.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_form.addRow("Источники данных:", self.main.pbirs_detail_sources)
        #right_form.addRow("Источники данных:", self.main.pbirs_detail_sources)
        self.main.pbirs_detail_refresh_status = QLabel("-")
        self.main.pbirs_detail_refresh_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.main.pbirs_detail_refresh_status.setWordWrap(True)  # Перенос текста для длинных статусов
        right_form.addRow("Статус обновления:", self.main.pbirs_detail_refresh_status)
        self.main.pbirs_detail_last_refresh = QLabel("-")
        self.main.pbirs_detail_last_refresh.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        right_form.addRow("Последнее обновление:", self.main.pbirs_detail_last_refresh)
        self.main.pbirs_detail_next_refresh = QLabel("-")
        self.main.pbirs_detail_next_refresh.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        right_form.addRow("Следующее обновление:", self.main.pbirs_detail_next_refresh)
        


        info_layout.addLayout(left_form)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        info_layout.addWidget(sep)
        info_layout.addLayout(right_form)
        # Устанавливаем stretch-факторы для равномерного распределения колонок
        info_layout.setStretch(0, 1)  # Левая колонка
        info_layout.setStretch(1, 0)  # Разделитель (фиксированная ширина)
        info_layout.setStretch(2, 1)  # Правая колонка
        info_group.setLayout(info_layout)
        layout.addWidget(info_group, 4)

        # Блок расписаний обновления
        plans_group = QGroupBox("Расписания обновления (Cache Refresh Plans)")
        plans_layout = QVBoxLayout()
        
        self.main.pbirs_refresh_plans_table = QTableWidget()
        self.main.pbirs_refresh_plans_table.setColumnCount(5)
        self.main.pbirs_refresh_plans_table.setHorizontalHeaderLabels([
            "Название", "Расписание", "Последний запуск", "Статус", "Следующий запуск"
        ])
        header = self.main.pbirs_refresh_plans_table.horizontalHeader()
        # Колонки 0, 1, 3 — растягиваются; колонки 2, 4 — фиксированная ширина
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        self.main.pbirs_refresh_plans_table.verticalHeader().setVisible(False)
        self.main.pbirs_refresh_plans_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.main.pbirs_refresh_plans_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Включаем контекстное меню
        self.main.pbirs_refresh_plans_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main.pbirs_refresh_plans_table.customContextMenuRequested.connect(
            self.main.show_pbirs_refresh_plans_context_menu
        )
        
        plans_layout.addWidget(self.main.pbirs_refresh_plans_table)
        plans_group.setLayout(plans_layout)
        layout.addWidget(plans_group, 4)

        # Информационное сообщение о создании/удалении расписания
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_label = QLabel("Для создания/удаления расписания используйте контекстное меню")
        info_label.setStyleSheet("color: #888; font-style: italic;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        layout.addWidget(info_widget, 1)

        return tab

    def create_logs_panel(self):
        """Создает панель логов для правой стороны."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Текстовое поле для логов (то же самое, что и во вкладке)
        # Если logs_text уже создан, используем его, иначе создаём новый
        if not hasattr(self.main, 'logs_text'):
            self.main.logs_text = QTextEdit()
            self.main.logs_text.setReadOnly(True)
            self.main.logs_text.setFont(QFont("Courier", 10))
        
        layout.addWidget(self.main.logs_text)
        
        # Кнопка очистки логов (опционально)
        clear_btn = QPushButton("Очистить логи")
        clear_btn.clicked.connect(lambda: self.main.logs_text.clear())
        layout.addWidget(clear_btn)
        
        return panel
    
    def _set_pbirs_filters_visible(self, visible: bool):
        """
        Переключает видимость PBIRS-фильтров и Service-фильтров.
        
        Args:
            visible: True - показать PBIRS-фильтры (режим server),
                     False - показать Service-фильтры (режим service)
        """
        # Фильтры для Power BI Service
        if hasattr(self.main, 'filter_enabled'):
            self.main.filter_enabled.setVisible(not visible)
        if hasattr(self.main, 'filter_recent'):
            self.main.filter_recent.setVisible(not visible)
        if hasattr(self.main, 'filter_errors'):
            self.main.filter_errors.setVisible(not visible)
        if hasattr(self.main, 'filter_except_not_use'):
            self.main.filter_except_not_use.setVisible(not visible)
        if hasattr(self.main, 'filter_in_progress'):
            self.main.filter_in_progress.setVisible(not visible)
        
        # Фильтры для PBIRS
        if hasattr(self.main, 'filter_pbirs_no_schedule'):
            self.main.filter_pbirs_no_schedule.setVisible(visible)
        if hasattr(self.main, 'filter_pbirs_no_auth'):
            self.main.filter_pbirs_no_auth.setVisible(visible)
        if hasattr(self.main, 'filter_pbirs_success'):
            self.main.filter_pbirs_success.setVisible(visible)
        if hasattr(self.main, 'filter_pbirs_errors'):
            self.main.filter_pbirs_errors.setVisible(visible)
        if hasattr(self.main, 'filter_pbirs_in_progress'):
            self.main.filter_pbirs_in_progress.setVisible(visible)
        
        # Блокируем сигналы на время сброса чекбоксов, чтобы избежать лишних вызовов apply_filters()
        if visible:
            # Сбрасываем Service-фильтры
            if hasattr(self.main, 'filter_enabled'):
                self.main.filter_enabled.blockSignals(True)
                self.main.filter_enabled.setChecked(False)
                self.main.filter_enabled.blockSignals(False)
            if hasattr(self.main, 'filter_recent'):
                self.main.filter_recent.blockSignals(True)
                self.main.filter_recent.setChecked(False)
                self.main.filter_recent.blockSignals(False)
            if hasattr(self.main, 'filter_errors'):
                self.main.filter_errors.blockSignals(True)
                self.main.filter_errors.setChecked(False)
                self.main.filter_errors.blockSignals(False)
            if hasattr(self.main, 'filter_except_not_use'):
                self.main.filter_except_not_use.blockSignals(True)
                self.main.filter_except_not_use.setChecked(False)
                self.main.filter_except_not_use.blockSignals(False)
            if hasattr(self.main, 'filter_in_progress'):
                self.main.filter_in_progress.blockSignals(True)
                self.main.filter_in_progress.setChecked(False)
                self.main.filter_in_progress.blockSignals(False)
        else:
            # Сбрасываем PBIRS-фильтры
            if hasattr(self.main, 'filter_pbirs_no_schedule'):
                self.main.filter_pbirs_no_schedule.blockSignals(True)
                self.main.filter_pbirs_no_schedule.setChecked(False)
                self.main.filter_pbirs_no_schedule.blockSignals(False)
            if hasattr(self.main, 'filter_pbirs_no_auth'):
                self.main.filter_pbirs_no_auth.blockSignals(True)
                self.main.filter_pbirs_no_auth.setChecked(False)
                self.main.filter_pbirs_no_auth.blockSignals(False)
            if hasattr(self.main, 'filter_pbirs_success'):
                self.main.filter_pbirs_success.blockSignals(True)
                self.main.filter_pbirs_success.setChecked(False)
                self.main.filter_pbirs_success.blockSignals(False)
            if hasattr(self.main, 'filter_pbirs_errors'):
                self.main.filter_pbirs_errors.blockSignals(True)
                self.main.filter_pbirs_errors.setChecked(False)
                self.main.filter_pbirs_errors.blockSignals(False)
            if hasattr(self.main, 'filter_pbirs_in_progress'):
                self.main.filter_pbirs_in_progress.blockSignals(True)
                self.main.filter_pbirs_in_progress.setChecked(False)
                self.main.filter_pbirs_in_progress.blockSignals(False)