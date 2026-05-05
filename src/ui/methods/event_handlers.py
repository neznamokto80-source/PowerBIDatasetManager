#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчики событий пользовательского интерфейса.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QTreeWidgetItem, QMenu, QFormLayout, QGroupBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)


class EventHandlers:
    """Обработчики событий UI."""
    
    def __init__(self, main_window):
        """
        Инициализирует обработчики событий.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def on_workspace_selected(self, index):
        """Обработчик выбора рабочей области."""
        if index < 0 or not self.main_window.workspaces:
            return
        
        workspace_id = self.main_window.workspace_combo.itemData(index)
        if workspace_id:
            self.main_window.current_workspace = workspace_id
            self.main_window.log_message(
                f"Выбрана рабочая область: {self.main_window.workspace_combo.itemText(index)}"
            )
            self.main_window.load_datasets()
    
    def on_dataset_selected(self, item, column):
        """Обработчик выбора датасета."""
        if not item:
            return
        
        # Получаем имя датасета из выбранного элемента
        dataset_name = item.text(0) if isinstance(item, QTreeWidgetItem) else item.text()
        
        # Ищем датасет в списке
        dataset = None
        for ds in self.main_window.datasets:
            if ds.get('name') == dataset_name:
                dataset = ds
                break
        
        if dataset:
            self.main_window.current_dataset = dataset  # сохраняем объект датасета
            self.main_window.update_dataset_details(dataset)
            self.main_window.log_message(f"Выбран датасет: {dataset_name}")
            
            # Включаем кнопки управления
            self.main_window.enable_btn.setEnabled(True)
            self.main_window.disable_btn.setEnabled(True)
            self.main_window.manual_refresh_btn.setEnabled(True)
        else:
            self.main_window.log_message(f"Датасет {dataset_name} не найден в списке")
    
    def on_dataset_double_clicked(self, item):
        """Обработчик двойного клика по датасету."""
        if not item:
            return
        
        # Определяем, является ли элемент ячейкой таблицы или элементом дерева
        dataset = None
        if isinstance(item, QTreeWidgetItem):
            # Элемент дерева
            dataset_name = item.text(0)
            for ds in self.main_window.datasets:
                if ds.get('name') == dataset_name:
                    dataset = ds
                    break
        else:
            # Ячейка таблицы QTableWidgetItem
            table = item.tableWidget()
            row = item.row()
            # Получаем ID датасета из колонки 2
            id_item = table.item(row, 2)
            if id_item:
                dataset_id = id_item.text()
                for ds in self.main_window.datasets:
                    if ds.get('id') == dataset_id:
                        dataset = ds
                        break
        
        if dataset:
            # Получаем имя датасета для заголовка диалога
            dataset_name = dataset.get('name', 'Неизвестно')
            
            # Сохраняем текущий датасет и рабочую область для кнопок
            previous_dataset = self.main_window.current_dataset
            previous_workspace = self.main_window.current_workspace
            self.main_window.current_dataset = dataset
            self.main_window.current_workspace = dataset.get('workspaceId', previous_workspace)
            
            # Создаем диалог
            dialog = QDialog(self.main_window)
            dialog.setWindowTitle(f"Детали датасета: {dataset_name}")
            dialog.setGeometry(200, 200, 600, 500)
            
            main_layout = QVBoxLayout(dialog)
            
            # Группа с информацией
            info_group = QGroupBox("Информация о датасете")
            form_layout = QFormLayout()
            
            # Вычисляем значения полей аналогично update_dataset_details
            name = dataset.get('name', 'Без имени')
            dataset_id = dataset.get('id', 'N/A')
            workspace_id = dataset.get('workspaceId') or dataset.get('workspace_id', '')
            workspace_name = self.main_window.get_workspace_name(workspace_id)
            status = dataset.get('status', 'unknown')
            last_refresh = dataset.get('lastRefreshTime', 'никогда')
            next_refresh = dataset.get('nextRefreshTime', 'не запланировано')
            
            # Получаем информацию о расписании
            refresh_schedule = dataset.get('refresh_schedule', {})
            schedule_text = 'не настроено'
            auto_refresh_status = 'Неизвестно'
            enabled = None
            
            if isinstance(refresh_schedule, dict) and refresh_schedule:
                enabled = refresh_schedule.get('enabled')
                if enabled is True:
                    auto_refresh_status = 'Включено'
                elif enabled is False:
                    auto_refresh_status = 'Выключено'
                else:
                    auto_refresh_status = 'Настроено (статус неизвестен)'
                
                # Формируем текст расписания
                days = refresh_schedule.get('days', [])
                times = refresh_schedule.get('times', [])
                timezone = refresh_schedule.get('localTimeZoneId', '')
                
                if days and times:
                    days_str = ', '.join(days) if isinstance(days, list) else str(days)
                    times_str = ', '.join(times) if isinstance(times, list) else str(times)
                    schedule_text = f'Дни: {days_str}\nВремя: {times_str}'
                    if timezone:
                        schedule_text += f'\nЧасовой пояс: {timezone}'
                    if enabled is not None:
                        schedule_text += f'\nСтатус: {"Включено" if enabled else "Выключено"}'
                    
                    # Конвертируем времена расписания из UTC+6 в UTC+5 (Екатеринбург)
                    # Предполагаем, что timezone = "Central Asia Standard Time" (UTC+6)
                    # Пользовательский часовой пояс: Екатеринбург (UTC+5)
                    from_offset = 6  # UTC+6
                    to_offset = 5    # UTC+5
                    try:
                        schedule_times_local = self.main_window.data_loading_methods._convert_schedule_times(times, from_offset, to_offset)
                        schedule_text += f'\nВремя (Екатеринбург): {", ".join(schedule_times_local)}'
                    except Exception:
                        pass
                else:
                    schedule_text = 'расписание не настроено'
            else:
                auto_refresh_status = 'Не настроено'
            
            # Если автообновление выключено, следующее обновление = N/A
            if enabled is False:
                next_refresh = "N/A"
            elif enabled is True and 'times' in refresh_schedule:
                times = refresh_schedule.get('times', [])
                if times:
                    from_offset = 6
                    to_offset = 5
                    try:
                        schedule_times_local = self.main_window.data_loading_methods._convert_schedule_times(times, from_offset, to_offset)
                        current_time = datetime.now()
                        next_refresh_dt = self.main_window.data_loading_methods._calculate_next_refresh(schedule_times_local, current_time)
                        if next_refresh_dt:
                            next_refresh = self.main_window.data_loading_methods._format_datetime_for_display(next_refresh_dt)
                    except Exception:
                        pass
            
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
            
            # Создаем виджеты с вычисленными значениями
            detail_name = QLabel(name)
            detail_id = QLabel(dataset_id)
            detail_workspace = QLabel(workspace_name)
            detail_refresh_status = QLabel(status)
            detail_last_refresh = QLabel(last_refresh)
            detail_next_refresh = QLabel(next_refresh)
            detail_schedule = QLabel(schedule_text)
            detail_auto_refresh = QLabel(auto_refresh_status)
            detail_last_refresh_details = QLabel(last_refresh_details)
            
            form_layout.addRow("Название:", detail_name)
            form_layout.addRow("ID:", detail_id)
            form_layout.addRow("Рабочая область:", detail_workspace)
            form_layout.addRow("Статус обновления:", detail_refresh_status)
            form_layout.addRow("Последнее обновление:", detail_last_refresh)
            form_layout.addRow("Следующее обновление:", detail_next_refresh)
            form_layout.addRow("Расписание:", detail_schedule)
            form_layout.addRow("Автообновление:", detail_auto_refresh)
            form_layout.addRow("Детали последнего обновления:", detail_last_refresh_details)
            
            info_group.setLayout(form_layout)
            main_layout.addWidget(info_group)
            
            # Кнопки управления
            button_layout = QHBoxLayout()
            
            enable_btn = QPushButton("Включить обновление")
            enable_btn.clicked.connect(self.main_window.enable_auto_refresh)
            # Активна, если автообновление выключено (enabled != True)
            enable_btn.setEnabled(enabled is not True)
            button_layout.addWidget(enable_btn)
            
            disable_btn = QPushButton("Отключить обновление")
            disable_btn.clicked.connect(self.main_window.disable_auto_refresh)
            # Активна, если автообновление включено (enabled == True)
            disable_btn.setEnabled(enabled is True)
            button_layout.addWidget(disable_btn)
            
            manual_refresh_btn = QPushButton("Запустить обновление")
            manual_refresh_btn.clicked.connect(self.main_window.trigger_manual_refresh)
            manual_refresh_btn.setEnabled(dataset.get('isRefreshable', False))
            button_layout.addWidget(manual_refresh_btn)
            
            main_layout.addLayout(button_layout)
            
            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.close)
            main_layout.addWidget(close_btn)
            
            # Восстановление предыдущего состояния после закрытия диалога
            def restore_state():
                self.main_window.current_dataset = previous_dataset
                self.main_window.current_workspace = previous_workspace
            dialog.finished.connect(lambda _: restore_state())
            
            dialog.exec()
            
            self.main_window.log_message(f"Открыты детали датасета: {dataset_name}")
    
    def get_selected_datasets(self, table):
        """
        Возвращает список выбранных датасетов из таблицы.
        
        Args:
            table: QTableWidget (dataset_table)
            
        Returns:
            Список объектов датасетов (словарей)
        """
        selected_datasets = []
        if not table or not hasattr(self.main_window, 'datasets'):
            return selected_datasets
        
        # Получаем выбранные строки
        selected_rows = set()
        for item in table.selectedItems():
            selected_rows.add(item.row())
        
        # Для каждой выбранной строки находим датасет
        for row in selected_rows:
            if row < 0 or row >= table.rowCount():
                continue
            # Получаем ID датасета из колонки 2 (ID датасета)
            id_item = table.item(row, 2)
            if id_item:
                dataset_id = id_item.text()
                # Ищем датасет в общем списке
                for ds in self.main_window.datasets:
                    if ds.get('id') == dataset_id:
                        selected_datasets.append(ds)
                        break
        
        return selected_datasets
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы датасетов."""
        # Определяем, откуда вызвано меню (таблица или дерево)
        sender = self.main_window.sender()
        
        menu = QMenu(self.main_window)
        
        # Общие действия
        refresh_action = QAction("Обновить информацию", self.main_window)
        refresh_action.triggered.connect(self.main_window.refresh_data)
        
        details_action = QAction("Показать детали", self.main_window)
        details_action.triggered.connect(lambda: self.on_dataset_double_clicked(
            sender.currentItem() if hasattr(sender, 'currentItem') else None
        ))
        
        # Определяем выбранные датасеты (для таблицы)
        selected_datasets = []
        if sender == self.main_window.dataset_table:
            selected_datasets = self.get_selected_datasets(sender)
        
        # Если выбрано несколько датасетов
        if len(selected_datasets) > 1:
            count = len(selected_datasets)
            enable_action = QAction(f"Включить автообновление для выбранных ({count})", self.main_window)
            enable_action.triggered.connect(lambda: self.main_window.enable_auto_refresh_selected(selected_datasets))
            
            disable_action = QAction(f"Отключить автообновление для выбранных ({count})", self.main_window)
            disable_action.triggered.connect(lambda: self.main_window.disable_auto_refresh_selected(selected_datasets))
            
            manual_refresh_action = QAction(f"Запустить обновление для выбранных ({count})", self.main_window)
            manual_refresh_action.triggered.connect(lambda: self.main_window.trigger_manual_refresh_selected(selected_datasets))
            
            menu.addAction(refresh_action)
            menu.addSeparator()
            menu.addAction(details_action)
            menu.addSeparator()
            menu.addAction(enable_action)
            menu.addAction(disable_action)
            menu.addAction(manual_refresh_action)
        
        # Одиночный выбор (дерево или таблица с одним выбранным)
        else:
            # Пытаемся определить выбранный датасет
            target_dataset = None
            target_workspace = None
            
            # Если есть selected_datasets с одним элементом
            if len(selected_datasets) == 1:
                target_dataset = selected_datasets[0]
                target_workspace = target_dataset.get('workspaceId', self.main_window.current_workspace)
            elif hasattr(sender, 'currentItem') and sender.currentItem():
                # Получаем датасет из currentItem (для дерева)
                item = sender.currentItem()
                dataset_name = item.text(0) if isinstance(item, QTreeWidgetItem) else item.text()
                for ds in self.main_window.datasets:
                    if ds.get('name') == dataset_name:
                        target_dataset = ds
                        target_workspace = ds.get('workspaceId', self.main_window.current_workspace)
                        break
            
            if target_dataset:
                # Сохраняем текущие значения, чтобы восстановить после действий?
                # Вместо этого временно установим current_dataset и current_workspace
                # через замыкание
                def make_enable_closure(dataset, workspace):
                    def closure():
                        self.main_window.current_dataset = dataset
                        self.main_window.current_workspace = workspace
                        self.main_window.enable_auto_refresh()
                    return closure
                
                def make_disable_closure(dataset, workspace):
                    def closure():
                        self.main_window.current_dataset = dataset
                        self.main_window.current_workspace = workspace
                        self.main_window.disable_auto_refresh()
                    return closure
                
                def make_manual_closure(dataset, workspace):
                    def closure():
                        self.main_window.current_dataset = dataset
                        self.main_window.current_workspace = workspace
                        self.main_window.trigger_manual_refresh()
                    return closure
                
                enable_action = QAction("Включить автообновление", self.main_window)
                enable_action.triggered.connect(make_enable_closure(target_dataset, target_workspace))
                
                disable_action = QAction("Отключить автообновление", self.main_window)
                disable_action.triggered.connect(make_disable_closure(target_dataset, target_workspace))
                
                manual_refresh_action = QAction("Запустить обновление вручную", self.main_window)
                manual_refresh_action.triggered.connect(make_manual_closure(target_dataset, target_workspace))
                
                menu.addAction(refresh_action)
                menu.addSeparator()
                menu.addAction(details_action)
                menu.addSeparator()
                menu.addAction(enable_action)
                menu.addAction(disable_action)
                menu.addAction(manual_refresh_action)
            else:
                # Нет выбранного датасета, показываем только общие действия
                menu.addAction(refresh_action)
                menu.addAction(details_action)
        
        menu.exec(sender.mapToGlobal(position))