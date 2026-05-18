#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалог деталей датасета, повторяющий вкладку "Детали" главного окна.
Используется при двойном клике по датасету или выборе из контекстного меню.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QLabel, QPushButton, QCheckBox, QComboBox,
    QListWidget, QFrame, QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

DAY_LABELS_RU = [
    "Воскресенье", "Понедельник", "Вторник", "Среда",
    "Четверг", "Пятница", "Суббота"
]
DAY_NAMES_API = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday"
]
DEFAULT_TIMEZONES = [
    "UTC", "Russian Standard Time", "Central Asia Standard Time",
    "Ekaterinburg Standard Time", "W. Europe Standard Time",
    "Central European Standard Time", "GMT Standard Time",
    "Eastern Standard Time", "Pacific Standard Time"
]


class DatasetDetailsDialog(QDialog):
    """Диалог с детальной информацией о датасете и управлением расписанием."""

    def __init__(
        self,
        parent,
        dataset: Dict[str, Any],
        main_window,
        initial_schedule: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            parent: Родительский виджет
            dataset: Словарь с данными датасета
            main_window: Ссылка на главное окно (для вызова методов)
            initial_schedule: Начальные данные расписания (опционально)
        """
        super().__init__(parent)
        self.dataset = dataset
        self.main = main_window
        self.schedule_data = initial_schedule or {}
        self.setWindowTitle(f"Детали датасета: {dataset.get('name', 'Без имени')}")
        self.resize(900, 600)

        # Создаем layout
        main_layout = QVBoxLayout(self)

        # Блок информации о датасете (два столбца)
        self._create_info_block(main_layout)

        # Блок управления расписанием (дни, время, настройки)
        self._create_schedule_block(main_layout)

        # Кнопки управления датасетом (включить/отключить/обновить)
        self._create_management_buttons(main_layout)

        # Кнопки диалога (Закрыть)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Загружаем данные расписания в UI
        self._load_schedule_to_ui()

    def _create_info_block(self, parent_layout: QVBoxLayout):
        """Создает блок информации о датасете в два столбца."""
        group = QGroupBox("Информация о датасете")
        layout = QHBoxLayout()

        # Левый столбец (основная информация)
        left_form = QFormLayout()
        self.detail_name = QLabel("-")
        left_form.addRow("Название:", self.detail_name)

        self.detail_id = QLabel("-")
        left_form.addRow("ID:", self.detail_id)

        self.detail_workspace = QLabel("-")
        left_form.addRow("Рабочая область:", self.detail_workspace)

        self.detail_refresh_status = QLabel("-")
        left_form.addRow("Статус обновления:", self.detail_refresh_status)

        self.detail_last_refresh = QLabel("-")
        left_form.addRow("Последнее обновление:", self.detail_last_refresh)

        self.detail_next_refresh = QLabel("-")
        left_form.addRow("Следующее обновление:", self.detail_next_refresh)

        # Правый столбец (дополнительная информация)
        right_form = QFormLayout()
        self.detail_schedule = QLabel("-")
        right_form.addRow("Расписание:", self.detail_schedule)

        self.detail_auto_refresh = QLabel("-")
        right_form.addRow("Автообновление:", self.detail_auto_refresh)

        self.detail_last_refresh_details = QLabel("-")
        right_form.addRow("Детали последнего обновления:", self.detail_last_refresh_details)

        # Добавляем формы в горизонтальный layout
        layout.addLayout(left_form)

        # Разделитель в виде вертикальной линии
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setLineWidth(1)
        separator.setMidLineWidth(0)
        separator.setFixedWidth(3)
        layout.addWidget(separator)

        layout.addLayout(right_form)
        # Устанавливаем stretch factors: левый и правый layout растягиваются одинаково, разделитель фиксирован
        layout.setStretch(0, 1)  # left_form
        layout.setStretch(1, 0)  # separator (фиксированная ширина)
        layout.setStretch(2, 1)  # right_form

        group.setLayout(layout)
        parent_layout.addWidget(group)

        # Заполняем данными
        self._update_info_from_dataset()

    def _update_info_from_dataset(self):
        """Заполняет блок информации данными из датасета."""
        dataset = self.dataset
        name = dataset.get('name', 'Без имени')
        dataset_id = dataset.get('id', 'N/A')
        workspace_id = dataset.get('workspaceId') or dataset.get('workspace_id', '')
        workspace_name = self.main.get_workspace_name(workspace_id) if hasattr(self.main, 'get_workspace_name') else workspace_id
        status = dataset.get('status', 'unknown')
        # Преобразуем статус "unknown" в "в процессе обновления" для отображения
        if status.lower() == 'unknown':
            status = 'в процессе обновления'
        last_refresh = dataset.get('lastRefreshTime', 'никогда')
        
        # Получаем информацию о расписании через метод главного окна
        schedule_text, auto_refresh_status, next_refresh, enabled = (
            self.main.data_loading_methods.get_schedule_display_for_dataset(dataset)
        )

        # Получаем информацию о последнем обновлении
        last_refresh_info = dataset.get('last_refresh', {})
        last_refresh_details = 'нет данных'
        if isinstance(last_refresh_info, dict) and last_refresh_info:
            end_time = last_refresh_info.get('endTime', '')
            refresh_status = last_refresh_info.get('status', '')
            refresh_type = last_refresh_info.get('refreshType', '')
            
            details_parts = []
            if end_time:
                try:
                    utc_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    local_dt = utc_dt + timedelta(hours=5)
                    local_dt_rounded = local_dt.replace(second=0, microsecond=0)
                    formatted = local_dt_rounded.strftime('%d.%m.%Y, %H:%M')
                    details_parts.append(f'Время: {formatted} (Екатеринбург)')
                    # Обновляем last_refresh для отображения в основном поле
                    last_refresh = formatted
                except Exception:
                    details_parts.append(f'Время: {end_time}')
            if refresh_status:
                details_parts.append(f'Статус: {refresh_status}')
            if refresh_type:
                details_parts.append(f'Тип: {refresh_type}')
            
            if details_parts:
                last_refresh_details = '; '.join(details_parts)

        self.detail_name.setText(name)
        self.detail_id.setText(dataset_id)
        self.detail_workspace.setText(workspace_name)
        self.detail_refresh_status.setText(status)
        self.detail_last_refresh.setText(last_refresh)
        self.detail_next_refresh.setText(next_refresh)
        self.detail_schedule.setText(schedule_text)
        self.detail_auto_refresh.setText(auto_refresh_status)
        self.detail_last_refresh_details.setText(last_refresh_details)

    def _create_schedule_block(self, parent_layout: QVBoxLayout):
        """Создает блок управления расписанием (дни, время, настройки)."""
        group = QGroupBox("Управление расписанием")
        group.setVisible(True)
        schedule_layout = QHBoxLayout()

        # Дни недели
        days_group = QGroupBox("Дни недели")
        days_layout = QGridLayout()
        self.schedule_day_checks = {}
        # Размещаем в две колонки: 4 в первой, 3 во второй
        for i, (api_name, ru) in enumerate(zip(DAY_NAMES_API, DAY_LABELS_RU)):
            cb = QCheckBox(ru)
            self.schedule_day_checks[api_name] = cb
            row = i % 4  # 4 строки в первой колонке
            col = 0 if i < 4 else 1
            days_layout.addWidget(cb, row, col)
        days_group.setLayout(days_layout)
        schedule_layout.addWidget(days_group)

        # Время срабатывания
        times_group = QGroupBox("Время срабатывания (локальное время выбранного пояса)")
        times_layout = QHBoxLayout()  # Горизонтальный layout: список слева, управление справа
        
        # Список времени в две колонки по 6 строк
        self.schedule_times_list = QListWidget()
        self.schedule_times_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.schedule_times_list.setFlow(QListWidget.Flow.LeftToRight)
        self.schedule_times_list.setWrapping(True)
        self.schedule_times_list.setGridSize(QSize(80, 25))
        self.schedule_times_list.setFixedHeight(180)  # 6 строк * 30 высота
        self.schedule_times_list.setFixedWidth(180)   # 2 колонки * 80 ширина + отступы
        times_layout.addWidget(self.schedule_times_list, 2)  # растягиваем
        
        # Панель управления временем справа
        time_edit_panel = QWidget()
        time_edit_layout = QVBoxLayout(time_edit_panel)
        time_edit_layout.setContentsMargins(5, 5, 5, 5)
        
        # Часы и минуты
        hours_minutes_layout = QHBoxLayout()
        hours_minutes_layout.addWidget(QLabel("Часы:"))
        self.schedule_hours_combo = QComboBox()
        self.schedule_hours_combo.addItems([f"{i:02d}" for i in range(24)])  # 00-23
        hours_minutes_layout.addWidget(self.schedule_hours_combo)
        hours_minutes_layout.addWidget(QLabel("Минуты:"))
        self.schedule_minutes_combo = QComboBox()
        self.schedule_minutes_combo.addItems(["00", "30"])  # только 00 и 30
        hours_minutes_layout.addWidget(self.schedule_minutes_combo)
        time_edit_layout.addLayout(hours_minutes_layout)
        
        # Кнопки
        self.schedule_add_time_btn = QPushButton("Добавить время")
        self.schedule_add_time_btn.clicked.connect(self._add_schedule_time)
        time_edit_layout.addWidget(self.schedule_add_time_btn)
        
        self.schedule_remove_time_btn = QPushButton("Удалить выбранное")
        self.schedule_remove_time_btn.clicked.connect(self._remove_schedule_time)
        time_edit_layout.addWidget(self.schedule_remove_time_btn)
        
        time_edit_layout.addStretch()
        times_layout.addWidget(time_edit_panel, 1)
        
        times_group.setLayout(times_layout)
        schedule_layout.addWidget(times_group)

        # Настройки расписания (часовой пояс, уведомления, кнопки)
        settings_group = QGroupBox("Настройки расписания")
        settings_layout = QVBoxLayout()
        
        # Часовой пояс и уведомления
        form_layout = QFormLayout()
        self.schedule_tz_combo = QComboBox()
        self.schedule_tz_combo.setEditable(True)
        self.schedule_tz_combo.addItems(DEFAULT_TIMEZONES)
        self.schedule_tz_combo.setCurrentText("Central Asia Standard Time")
        form_layout.addRow("Часовой пояс (Windows):", self.schedule_tz_combo)
        
        self.schedule_notify_combo = QComboBox()
        self.schedule_notify_combo.addItem("Без уведомлений", "NoNotification")
        self.schedule_notify_combo.addItem("Почта при ошибке", "MailOnFailure")
        self.schedule_notify_combo.addItem("Почта по завершении", "MailOnCompletion")
        self.schedule_notify_combo.setCurrentIndex(1)  # MailOnFailure по умолчанию
        form_layout.addRow("Уведомления:", self.schedule_notify_combo)
        
        self.schedule_enabled_cb = QCheckBox("Расписание включено")
        self.schedule_enabled_cb.setChecked(True)
        form_layout.addRow(self.schedule_enabled_cb)
        
        settings_layout.addLayout(form_layout)
        settings_layout.addStretch()
        
        # Кнопки сохранения/удаления
        schedule_buttons_layout = QHBoxLayout()
        self.schedule_save_btn = QPushButton("Сохранить расписание")
        self.schedule_save_btn.clicked.connect(self._save_schedule)
        self.schedule_delete_btn = QPushButton("Удалить расписание")
        self.schedule_delete_btn.clicked.connect(self._delete_schedule)
        schedule_buttons_layout.addWidget(self.schedule_save_btn)
        schedule_buttons_layout.addWidget(self.schedule_delete_btn)
        schedule_buttons_layout.addStretch()
        settings_layout.addLayout(schedule_buttons_layout)
        
        settings_group.setLayout(settings_layout)
        schedule_layout.addWidget(settings_group)

        group.setLayout(schedule_layout)
        parent_layout.addWidget(group)

    def _create_management_buttons(self, parent_layout: QVBoxLayout):
        """Создает кнопки управления датасетом (включить/отключить/обновить)."""
        button_layout = QHBoxLayout()
        
        self.enable_btn = QPushButton("Включить обновление")
        self.enable_btn.clicked.connect(self._enable_auto_refresh)
        button_layout.addWidget(self.enable_btn)
        
        self.disable_btn = QPushButton("Отключить обновление")
        self.disable_btn.clicked.connect(self._disable_auto_refresh)
        button_layout.addWidget(self.disable_btn)
        
        self.manual_refresh_btn = QPushButton("Запустить обновление")
        self.manual_refresh_btn.clicked.connect(self._trigger_manual_refresh)
        button_layout.addWidget(self.manual_refresh_btn)
        
        button_layout.addStretch()
        parent_layout.addLayout(button_layout)
        
        # Обновляем состояние кнопок на основе данных датасета
        self._update_management_buttons()

    def _update_management_buttons(self):
        """Обновляет состояние кнопок управления на основе данных датасета."""
        dataset = self.dataset
        schedule_text, auto_refresh_status, next_refresh, enabled = (
            self.main.data_loading_methods.get_schedule_display_for_dataset(dataset)
        )
        self.enable_btn.setEnabled(enabled is not True)
        self.disable_btn.setEnabled(enabled is True)
        self.manual_refresh_btn.setEnabled(dataset.get('isRefreshable', False))

    def _load_schedule_to_ui(self):
        """Загружает данные расписания в UI."""
        # Используем schedule_data, если передан, иначе берем из датасета
        schedule = self.schedule_data
        if not schedule:
            schedule = self.dataset.get('refresh_schedule')
            if not isinstance(schedule, dict):
                schedule = {}
        
        days = schedule.get('days', [])
        for api_name, cb in self.schedule_day_checks.items():
            cb.setChecked(api_name in days)
        
        times = schedule.get('times', [])
        self.schedule_times_list.clear()
        for t in times:
            if isinstance(t, str) and t.strip():
                self.schedule_times_list.addItem(t.strip())
        
        tz = schedule.get('localTimeZoneId', 'Central Asia Standard Time')
        self.schedule_tz_combo.setCurrentText(tz)
        
        notify = schedule.get('notifyOption', 'MailOnFailure')
        idx = self.schedule_notify_combo.findData(notify)
        if idx >= 0:
            self.schedule_notify_combo.setCurrentIndex(idx)
        
        enabled = schedule.get('enabled', True)
        self.schedule_enabled_cb.setChecked(bool(enabled))

    # ========== Обработчики событий ==========

    def _add_schedule_time(self):
        """Добавляет выбранное время в список."""
        hours = self.schedule_hours_combo.currentText()
        minutes = self.schedule_minutes_combo.currentText()
        time_text = f"{hours}:{minutes}"
        # Проверяем, нет ли уже такого времени
        items = [self.schedule_times_list.item(i).text() for i in range(self.schedule_times_list.count())]
        if time_text not in items:
            self.schedule_times_list.addItem(time_text)
        # Сбросить на значения по умолчанию (03:00)
        self.schedule_hours_combo.setCurrentText("03")
        self.schedule_minutes_combo.setCurrentText("00")

    def _remove_schedule_time(self):
        """Удаляет выбранное время из списка."""
        row = self.schedule_times_list.currentRow()
        if row >= 0:
            self.schedule_times_list.takeItem(row)

    def _save_schedule(self):
        """Сохраняет расписание через главное окно."""
        # Собираем данные из UI
        days = [n for n, cb in self.schedule_day_checks.items() if cb.isChecked()]
        times = []
        seen = set()
        for i in range(self.schedule_times_list.count()):
            text = self.schedule_times_list.item(i).text().strip()
            if text and text not in seen:
                seen.add(text)
                times.append(text)
        tz = self.schedule_tz_combo.currentText().strip()
        notify = self.schedule_notify_combo.currentData()
        if notify is None:
            notify = "MailOnFailure"
        enabled = self.schedule_enabled_cb.isChecked()
        
        schedule_payload = {
            "enabled": enabled,
            "days": days,
            "times": times,
            "localTimeZoneId": tz,
            "notifyOption": notify,
        }
        
        # Вызываем метод сохранения через refresh_operations
        workspace_id = self.dataset.get('workspaceId') or self.dataset.get('workspace_id') or self.dataset.get('workspace', '')
        dataset_id = self.dataset.get('id', '')
        if not workspace_id or not dataset_id:
            self.main.log_message(f"Ошибка: не удалось определить workspace или dataset. workspace_id={workspace_id}, dataset_id={dataset_id}, keys={list(self.dataset.keys())}")
            return
        
        try:
            self.main.log_message(f"Сохранение расписания для датасета {self.dataset.get('name', dataset_id)}...")
            self.main.refresh_operations.update_refresh_schedule(workspace_id, dataset_id, schedule_payload)
            self.main.log_message("✓ Расписание сохранено")
            # Обновляем информацию о датасете
            self._update_info_from_dataset()
            self._update_management_buttons()
        except Exception as e:
            self.main.log_message(f"✗ Ошибка сохранения расписания: {e}")

    def _delete_schedule(self):
        """Удаляет расписание через refresh_operations."""
        workspace_id = self.dataset.get('workspaceId') or self.dataset.get('workspace_id') or self.dataset.get('workspace', '')
        dataset_id = self.dataset.get('id', '')
        if not workspace_id or not dataset_id:
            self.main.log_message(f"Ошибка: не удалось определить workspace или dataset. workspace_id={workspace_id}, dataset_id={dataset_id}, keys={list(self.dataset.keys())}")
            return
        
        try:
            self.main.log_message(f"Отключение расписания для датасета {self.dataset.get('name', dataset_id)}...")
            self.main.refresh_operations.disable_auto_refresh(workspace_id, dataset_id)
            self.main.log_message("✓ Расписание отключено")
            # Обновляем информацию о датасете
            self._update_info_from_dataset()
            self._update_management_buttons()
        except Exception as e:
            self.main.log_message(f"✗ Ошибка отключения расписания: {e}")

    def _enable_auto_refresh(self):
        """Включает автообновление через refresh_operations."""
        workspace_id = self.dataset.get('workspaceId') or self.dataset.get('workspace_id') or self.dataset.get('workspace', '')
        dataset_id = self.dataset.get('id', '')
        if not workspace_id or not dataset_id:
            self.main.log_message(f"Ошибка: не удалось определить workspace или dataset. workspace_id={workspace_id}, dataset_id={dataset_id}, keys={list(self.dataset.keys())}")
            return
        
        try:
            self.main.log_message(f"Включение автообновления для датасета {self.dataset.get('name', dataset_id)}...")
            self.main.refresh_operations.enable_auto_refresh(workspace_id, dataset_id)
            self.main.log_message("✓ Автообновление включено")
            self._update_info_from_dataset()
            self._update_management_buttons()
        except Exception as e:
            self.main.log_message(f"✗ Ошибка включения автообновления: {e}")

    def _disable_auto_refresh(self):
        """Отключает автообновление через refresh_operations."""
        workspace_id = self.dataset.get('workspaceId') or self.dataset.get('workspace_id') or self.dataset.get('workspace', '')
        dataset_id = self.dataset.get('id', '')
        if not workspace_id or not dataset_id:
            self.main.log_message(f"Ошибка: не удалось определить workspace или dataset. workspace_id={workspace_id}, dataset_id={dataset_id}, keys={list(self.dataset.keys())}")
            return
        
        try:
            self.main.log_message(f"Отключение автообновления для датасета {self.dataset.get('name', dataset_id)}...")
            self.main.refresh_operations.disable_auto_refresh(workspace_id, dataset_id)
            self.main.log_message("✓ Автообновление отключено")
            self._update_info_from_dataset()
            self._update_management_buttons()
        except Exception as e:
            self.main.log_message(f"✗ Ошибка отключения автообновления: {e}")

    def _trigger_manual_refresh(self):
        """Запускает ручное обновление через refresh_operations."""
        workspace_id = self.dataset.get('workspaceId') or self.dataset.get('workspace_id') or self.dataset.get('workspace', '')
        dataset_id = self.dataset.get('id', '')
        if not workspace_id or not dataset_id:
            self.main.log_message(f"Ошибка: не удалось определить workspace или dataset. workspace_id={workspace_id}, dataset_id={dataset_id}, keys={list(self.dataset.keys())}")
            return
        
        try:
            self.main.log_message(f"Запуск ручного обновления для датасета {self.dataset.get('name', dataset_id)}...")
            self.main.refresh_operations.trigger_manual_refresh(workspace_id, dataset_id)
            self.main.log_message("✓ Ручное обновление запущено")
            self._update_info_from_dataset()
            self._update_management_buttons()
        except Exception as e:
            self.main.log_message(f"✗ Ошибка запуска ручного обновления: {e}")