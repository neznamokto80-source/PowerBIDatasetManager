#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Операции пользовательского интерфейса: управление состоянием, обработчики событий, справка.
Объединяет функционал из ui_state.py, event_handlers.py и help_methods.py.
"""

import logging
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidgetItem,
    QMenu, QFormLayout, QGroupBox, QTextEdit, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from ..ui.dataset_details_dialog import DatasetDetailsDialog

logger = logging.getLogger(__name__)


class UIOperations:
    """Операции пользовательского интерфейса."""
    
    def __init__(self, main_window):
        """
        Инициализирует операции UI.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    # ========== Методы управления состоянием UI (из UIStateMethods) ==========
    
    def update_ui_for_disconnected_state(self):
        """Обновляет UI для состояния 'не подключено'."""
        # Очищаем все данные
        self.main_window.workspace_combo.clear()
        
        # В зависимости от режима настраиваем комбобокс
        if self.main_window.current_mode == 'server':
            # В режиме server добавляем опцию "Все папки" и включаем комбобокс
            self.main_window.workspace_combo.addItem("Все папки")
            self.main_window.workspace_combo.setEnabled(True)
        else:
            # В режиме service показываем "Не подключено" и выключаем
            self.main_window.workspace_combo.addItem("-- Не подключено --")
            self.main_window.workspace_combo.setEnabled(False)
        
        self.main_window.dataset_tree.clear()
        self.main_window.dataset_tree.setHeaderLabels(["Название", "Статус", "Обновление"])
        
        # Очищаем таблицу
        self.main_window.dataset_table.setRowCount(0)
        
        # Обновляем статистику
        self.main_window.total_datasets_label.setText("Всего датасетов: --")
        self.main_window.enabled_refresh_label.setText("С обновлением: --")
        self.main_window.failed_refresh_label.setText("С ошибками: --")
        self.main_window.last_update_label.setText("Последнее обновление: --")
        
        # Обновляем детали
        self.main_window.detail_name.setText("-")
        self.main_window.detail_id.setText("-")
        self.main_window.detail_workspace.setText("-")
        self.main_window.detail_refresh_status.setText("-")
        self.main_window.detail_last_refresh.setText("-")
        self.main_window.detail_next_refresh.setText("-")
        self.main_window.detail_schedule.setText("-")
        
        # Отключаем кнопки управления
        self.main_window.enable_btn.setEnabled(False)
        self.main_window.disable_btn.setEnabled(False)
        self.main_window.manual_refresh_btn.setEnabled(False)
        if hasattr(self.main_window, 'edit_schedule_btn'):
            self.main_window.edit_schedule_btn.setEnabled(False)
        
        # Отключаем фильтры
        self.main_window.filter_enabled.setEnabled(False)
        self.main_window.filter_recent.setEnabled(False)
        self.main_window.filter_errors.setEnabled(False)
        self.main_window.filter_except_not_use.setEnabled(False)
        self.main_window.filter_in_progress.setEnabled(False)
        
        # Отключаем мониторинг
        self.main_window.start_monitor_btn.setEnabled(False)
        self.main_window.stop_monitor_btn.setEnabled(False)
        
        # Обновляем кнопку подключения
        if hasattr(self.main_window, 'connect_btn'):
            self.main_window.connect_btn.setText("Подключить")
            self.main_window.connect_btn.setEnabled(True)
    
    def update_ui_for_connected_state(self):
        """Обновляет UI для состояния 'подключено'."""
        # Включаем комбобокс рабочих областей
        self.main_window.workspace_combo.setEnabled(True)
        self.main_window.workspace_combo.clear()
        
        if self.main_window.current_mode == 'server':
            # В режиме server добавляем "Все папки"
            self.main_window.workspace_combo.addItem("Все папки")
            # Если папки уже загружены, добавляем их
            if hasattr(self.main_window, 'pbirs_folders') and self.main_window.pbirs_folders:
                for folder in self.main_window.pbirs_folders:
                    self.main_window.workspace_combo.addItem(folder)
        else:
            # Режим service
            if self.main_window.workspaces:
                for ws in self.main_window.workspaces:
                    name = ws.get('name', 'Без имени')
                    self.main_window.workspace_combo.addItem(name, ws.get('id'))
            else:
                self.main_window.workspace_combo.addItem("Нет рабочих областей")
        
        # Включаем фильтры
        self.main_window.filter_enabled.setEnabled(True)
        self.main_window.filter_recent.setEnabled(True)
        self.main_window.filter_errors.setEnabled(True)
        self.main_window.filter_except_not_use.setEnabled(True)
        self.main_window.filter_in_progress.setEnabled(True)
        
        # Включаем кнопки управления (позже, когда выбран датасет)
        self.main_window.enable_btn.setEnabled(False)
        self.main_window.disable_btn.setEnabled(False)
        self.main_window.manual_refresh_btn.setEnabled(False)
        if hasattr(self.main_window, 'edit_schedule_btn'):
            self.main_window.edit_schedule_btn.setEnabled(False)
        self.main_window.start_monitor_btn.setEnabled(True)
        self.main_window.stop_monitor_btn.setEnabled(False)
        
        # Обновляем статус
        self.main_window.status_bar.showMessage("Подключено", 3000)
        self.main_window.log_message("UI обновлен для состояния 'подключено'")
    
    def log_message(self, message: str):
        """Добавляет сообщение в лог через стандартный логгер."""
        # Логируем через стандартный логгер - обработчик QTextEditLogHandler
        # сам добавит запись в UI с правильным форматом
        logger.info(message)
    
    # ========== Обработчики событий (из EventHandlers) ==========
    
    def on_workspace_selected(self, index):
        """Обработчик выбора рабочей области (для service) или папки (для server)."""
        if index < 0:
            return
        
        if self.main_window.current_mode == 'server':
            # Режим PBIRS: выбор папки
            folder_path = self.main_window.workspace_combo.itemText(index)
            self.main_window.log_message(f"Выбрана папка: {folder_path}")
            
            # Получаем фильтр по названию отчета
            name_filter = None
            if hasattr(self.main_window, 'pbirs_report_name_filter'):
                name_filter = self.main_window.pbirs_report_name_filter.text().strip()
                if name_filter:
                    self.main_window.log_message(f"Фильтр по названию: '{name_filter}'")
            
            # Фильтруем отчеты по папке и названию
            if hasattr(self.main_window, 'pbirs_reports'):
                reports = self.main_window.pbirs_reports
                # Обновляем таблицу с фильтрацией
                if hasattr(self.main_window, 'update_pbirs_reports_table'):
                    self.main_window.update_pbirs_reports_table(reports, folder_path, name_filter)
                    self.main_window.log_message(f"Таблица отфильтрована по папке: {folder_path}, фильтр названия: {name_filter or 'нет'}")
                else:
                    # Резервная логика фильтрации
                    filtered = []
                    for report in reports:
                        path = report.get('Path', '')
                        name = report.get('Name', '')
                        # Проверяем фильтр по папке
                        folder_match = (folder_path == "Все папки" or folder_path == '/' or
                                       path.startswith(folder_path + '/') or path == folder_path)
                        # Проверяем фильтр по названию
                        name_match = True
                        if name_filter:
                            name_match = name_filter.lower() in name.lower()
                        
                        if folder_match and name_match:
                            filtered.append(report)
                    self.main_window.log_message(f"Найдено отчетов в папке: {len(filtered)}")
                    for i, report in enumerate(filtered[:5]):
                        self.main_window.log_message(f"  {i+1}. {report.get('Name', 'Без имени')}")
            else:
                self.main_window.log_message("Отчеты PBIRS не загружены.")
        else:
            # Режим Power BI Service
            if not self.main_window.workspaces:
                return
            workspace_id = self.main_window.workspace_combo.itemData(index)
            if workspace_id:
                self.main_window.current_workspace = workspace_id
                self.main_window.log_message(
                    f"Выбрана рабочая область: {self.main_window.workspace_combo.itemText(index)}"
                )
                self.main_window.load_datasets()
    
    def on_pbirs_name_filter_changed(self):
        """Обработчик изменения текста в поле фильтра по названию отчета PBIRS."""
        if self.main_window.current_mode != 'server':
            return
        
        # Получаем текущий фильтр
        name_filter = None
        if hasattr(self.main_window, 'pbirs_report_name_filter'):
            name_filter = self.main_window.pbirs_report_name_filter.text().strip()
            if not name_filter:
                name_filter = None
        
        # Получаем выбранную папку
        selected_folder = None
        if hasattr(self.main_window, 'workspace_combo'):
            index = self.main_window.workspace_combo.currentIndex()
            if index >= 0:
                selected_folder = self.main_window.workspace_combo.itemText(index)
        
        # Применяем фильтрацию
        if hasattr(self.main_window, 'pbirs_reports'):
            reports = self.main_window.pbirs_reports
            if hasattr(self.main_window, 'update_pbirs_reports_table'):
                self.main_window.update_pbirs_reports_table(reports, selected_folder, name_filter)
                self.main_window.log_message(f"Фильтр по названию обновлен: '{name_filter or 'нет'}'")
            else:
                # Резервная логика фильтрации
                filtered = []
                for report in reports:
                    path = report.get('Path', '')
                    name = report.get('Name', '')
                    
                    # Проверяем фильтр по папке
                    folder_match = True
                    if selected_folder and selected_folder != "Все папки" and selected_folder != '/':
                        folder_match = path.startswith(selected_folder + '/') or path == selected_folder
                    
                    # Проверяем фильтр по названию
                    name_match = True
                    if name_filter:
                        name_match = name_filter.lower() in name.lower()
                    
                    if folder_match and name_match:
                        filtered.append(report)
                
                self.main_window.log_message(f"Отфильтровано отчетов: {len(filtered)} (фильтр: '{name_filter or 'нет'}')")

    def on_pbirs_sources_filter_changed(self):
        """Обработчик изменения фильтров на вкладке источников данных PBIRS."""
        if self.main_window.current_mode != 'server':
            return
        
        # Получаем фильтр по названию отчета
        report_filter = None
        if hasattr(self.main_window, 'pbirs_sources_report_filter'):
            text = self.main_window.pbirs_sources_report_filter.text().strip()
            if text:
                report_filter = text
        
        # Получаем фильтр по ConnectionString
        source_filter = None
        if hasattr(self.main_window, 'pbirs_sources_source_filter'):
            combo = self.main_window.pbirs_sources_source_filter
            index = combo.currentIndex()
            if index >= 0:
                # Пытаемся получить полный ConnectionString из userData
                full_connection = combo.itemData(index, Qt.ItemDataRole.UserRole)
                if full_connection and isinstance(full_connection, str):
                    source_filter = full_connection.strip()
                else:
                    source_filter = combo.currentText().strip()
                
                if not source_filter or source_filter == "Все источники":
                    source_filter = None
        
        # Получаем фильтр по типу (Kind) — строгое соответствие
        kind_filter = None
        if hasattr(self.main_window, 'pbirs_sources_kind_filter'):
            combo = self.main_window.pbirs_sources_kind_filter
            text = combo.currentText().strip()
            if text and text != "Все типы":
                kind_filter = text
        
        # Получаем фильтр по пользователю — строгое соответствие
        user_filter = None
        if hasattr(self.main_window, 'pbirs_sources_user_filter'):
            combo = self.main_window.pbirs_sources_user_filter
            text = combo.currentText().strip()
            if text and text != "Все пользователи":
                user_filter = text
        
        # Применяем фильтрацию к таблице источников
        if hasattr(self.main_window, 'pbirs_sources_data'):
            sources_data = self.main_window.pbirs_sources_data
            if hasattr(self.main_window, 'update_pbirs_sources_table'):
                self.main_window.update_pbirs_sources_table(sources_data, report_filter, source_filter, kind_filter, user_filter)
                self.main_window.log_message(
                    f"Фильтр источников обновлен: отчет='{report_filter or 'нет'}', "
                    f"ConnectionString='{source_filter or 'нет'}', "
                    f"тип='{kind_filter or 'нет'}', "
                    f"пользователь='{user_filter or 'нет'}'"
                )
            else:
                # Резервная логика фильтрации
                filtered = []
                for source_item in sources_data:
                    folder = source_item.get('Folder', '')
                    report_name = source_item.get('ReportName', '')
                    connection_string = source_item.get('ConnectionString', '')
                    kind = source_item.get('Kind', '')
                    username = source_item.get('Username', '')
                    
                    # Проверяем фильтр по названию отчета
                    report_match = True
                    if report_filter:
                        report_match = report_filter.lower() in report_name.lower()
                    
                    # Проверяем фильтр по ConnectionString
                    source_match = True
                    if source_filter:
                        filter_lower = source_filter.lower()
                        connection_string_lower = connection_string.lower()
                        source_match = filter_lower in connection_string_lower
                    
                    # Проверяем фильтр по типу (Kind) — строгое соответствие
                    kind_match = True
                    if kind_filter:
                        kind_match = kind.lower() == kind_filter.lower()
                    
                    # Проверяем фильтр по пользователю — строгое соответствие
                    user_match = True
                    if user_filter:
                        user_match = username.lower() == user_filter.lower()
                    
                    if report_match and source_match and kind_match and user_match:
                        filtered.append(source_item)
                
                self.main_window.log_message(
                    f"Отфильтровано источников: {len(filtered)} "
                    f"(отчет: '{report_filter or 'нет'}', "
                    f"ConnectionString: '{source_filter or 'нет'}', "
                    f"тип: '{kind_filter or 'нет'}', "
                    f"пользователь: '{user_filter or 'нет'}')"
                )

    def on_pbirs_details_filter_changed(self):
        """Обработчик изменения фильтра на вкладке детальной информации PBIRS."""
        if self.main_window.current_mode != 'server':
            return
        
        # Получаем фильтр по названию отчета
        name_filter = None
        if hasattr(self.main_window, 'pbirs_details_name_filter'):
            text = self.main_window.pbirs_details_name_filter.text().strip()
            if text:
                name_filter = text
        
        # Применяем фильтрацию к таблице деталей
        if hasattr(self.main_window, 'pbirs_details_data'):
            details_data = self.main_window.pbirs_details_data
            if hasattr(self.main_window, 'update_pbirs_details_table'):
                self.main_window.update_pbirs_details_table(details_data, name_filter)
                self.main_window.log_message(
                    f"Фильтр деталей обновлен: название='{name_filter or 'нет'}'"
                )
            else:
                # Резервная логика фильтрации
                filtered = []
                for report in details_data:
                    report_name = report.get('Name', '')
                    
                    # Проверяем фильтр по названию отчета
                    name_match = True
                    if name_filter:
                        name_match = name_filter.lower() in report_name.lower()
                    
                    if name_match:
                        filtered.append(report)
                
                self.main_window.log_message(
                    f"Отфильтровано отчетов: {len(filtered)} "
                    f"(название: '{name_filter or 'нет'}')"
                )

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
            if hasattr(self.main_window, 'edit_schedule_btn'):
                self.main_window.edit_schedule_btn.setEnabled(True)
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
            # Сохраняем текущий датасет и рабочую область для кнопок
            previous_dataset = self.main_window.current_dataset
            previous_workspace = self.main_window.current_workspace
            self.main_window.current_dataset = dataset
            self.main_window.current_workspace = dataset.get('workspaceId', previous_workspace)
            
            # Получаем данные расписания из датасета (поле refresh_schedule)
            schedule_data = dataset.get('refresh_schedule')
            if not isinstance(schedule_data, dict):
                schedule_data = None
            
            # Создаем диалог
            dialog = DatasetDetailsDialog(
                parent=self.main_window,
                dataset=dataset,
                main_window=self.main_window,
                initial_schedule=schedule_data
            )
            
            # Восстановление предыдущего состояния после закрытия диалога
            def restore_state():
                self.main_window.current_dataset = previous_dataset
                self.main_window.current_workspace = previous_workspace
            dialog.finished.connect(lambda _: restore_state())
            
            dialog.exec()
            
            self.main_window.log_message(f"Открыты детали датасета: {dataset.get('name', 'Неизвестно')}")
    
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
    
    # ========== Методы справки ==========
    
    def show_help(self):
        """Показывает диалог справки с подробным описанием."""
        from src.utils.help_text import get_help_text
        help_text = get_help_text()

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Справка - Power BI Dataset Monitor & Manager")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(help_text)
        text_edit.setStyleSheet("QTextEdit { font-family: 'Segoe UI', 'Arial'; font-size: 10pt; }")

        layout.addWidget(text_edit)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()
    
    # ========== Методы для вкладки "Детали PBIRS" ==========
    
    def on_pbirs_details_report_selected(self):
        """Обработчик выбора отчета в выпадающем списке на вкладке Детали PBIRS."""
        combo = self.main_window.pbirs_details_report_combo
        index = combo.currentIndex()
        
        if index <= 0:  # Первый элемент "-- Выберите отчет --" или нет выбора
            # Очищаем поля информации
            self._clear_pbirs_details_fields()
            # Отключаем кнопки управления
            self._set_pbirs_buttons_enabled(False)
            # Очищаем таблицу расписаний
            if hasattr(self.main_window, 'pbirs_refresh_plans_table'):
                self.main_window.pbirs_refresh_plans_table.setRowCount(0)
            return
        
        # Получаем данные отчета из userData комбобокса
        report_data = combo.itemData(index)
        if not report_data:
            self.main_window.log_message("Ошибка: данные отчета не найдены")
            return
        
        # Обновляем поля информации об отчете
        self._update_pbirs_details_fields(report_data)
        # Включаем кнопки управления
        self._set_pbirs_buttons_enabled(True)
        # Заполняем таблицу расписаний
        self.populate_pbirs_refresh_plans_table(report_data)
        self.main_window.log_message(f"Выбран отчет: {report_data.get('Name', 'Без имени')}")

    def populate_pbirs_refresh_plans_table(self, report_data):
        """
        Заполняет таблицу расписаний на вкладке Детали PBIRS.
        Использует реальные поля LastRunTime и вычисляет следующий запуск.
        """
        from src.utils.pbirs_formatter import compute_next_run
        import dateutil.parser

        if not hasattr(self.main_window, 'pbirs_refresh_plans_table'):
            return

        table = self.main_window.pbirs_refresh_plans_table
        table.setRowCount(0)

        refresh_plans = report_data.get('RefreshPlansList', [])
        if not refresh_plans:
            self.main_window.log_message("Нет расписаний обновления для этого отчета.")
            return

        table.setRowCount(len(refresh_plans))
        for row, plan in enumerate(refresh_plans):
            # 1. Название
            plan_name = plan.get('Description') or plan.get('Name', 'Без названия')
            table.setItem(row, 0, QTableWidgetItem(plan_name))

            # 2. Расписание (читаемое описание)
            schedule_desc = plan.get('ScheduleDescription', 'Не задано')
            schedule_item = QTableWidgetItem(schedule_desc)
            schedule_item.setToolTip(f"{schedule_desc}")            
            table.setItem(row, 1, QTableWidgetItem(schedule_item))

            # 3. Последний запуск (из LastRunTime)
            last_run_raw = plan.get('LastRunTime')
            if last_run_raw:
                try:
                    dt = dateutil.parser.parse(last_run_raw)
                    last_run_str = dt.strftime("%d.%m.%Y в %H:%M")
                except Exception:
                    last_run_str = last_run_raw
            else:
                last_run_str = 'Никогда'
            table.setItem(row, 2, QTableWidgetItem(last_run_str))

            # 4. Статус + tooltip с полным текстом
            last_status = plan.get('LastStatus', 'Не запускался')
            status_item = QTableWidgetItem(last_status)
            status_item.setToolTip(f"{last_status}")
            table.setItem(row, 3, status_item)

            # 5. Следующий запуск (вычисляем из расписания)
            schedule_obj = plan.get('Schedule')
            start_dt = None
            end_dt = None
            recurrence = None
            if schedule_obj and isinstance(schedule_obj, dict):
                definition = schedule_obj.get('Definition', {})
                start_dt = definition.get('StartDateTime')
                end_dt = definition.get('EndDate')
                recurrence = definition.get('Recurrence')
            if recurrence and start_dt:
                next_run_str = compute_next_run(recurrence, start_dt, end_dt)
            else:
                next_run_str = "Не запланировано"
            table.setItem(row, 4, QTableWidgetItem(next_run_str))

            # Сохраняем объект плана в userData первой ячейки
            table.item(row, 0).setData(Qt.ItemDataRole.UserRole, plan)

        # Размеры колонок заданы в ui_panels.py при создании таблицы
        self.main_window.log_message(f"Загружено расписаний: {len(refresh_plans)}")
    
   
    def _clear_pbirs_details_fields(self):
        """Очищает поля информации об отчете на вкладке Детали PBIRS."""
        if hasattr(self.main_window, 'pbirs_detail_name'):
            self.main_window.pbirs_detail_name.setText("-")
        if hasattr(self.main_window, 'pbirs_detail_id'):
            self.main_window.pbirs_detail_id.setText("-")
        if hasattr(self.main_window, 'pbirs_detail_folder'):
            self.main_window.pbirs_detail_folder.setText("-")
        if hasattr(self.main_window, 'pbirs_detail_creator'):
            self.main_window.pbirs_detail_creator.setText("-")
        if hasattr(self.main_window, 'pbirs_detail_sources'):
            self.main_window.pbirs_detail_sources.setText("-")
        if hasattr(self.main_window, 'pbirs_detail_refresh_status'):
            self.main_window.pbirs_detail_refresh_status.setText("-")
        if hasattr(self.main_window, 'pbirs_detail_last_refresh'):
            self.main_window.pbirs_detail_last_refresh.setText("-")
        if hasattr(self.main_window, 'pbirs_detail_next_refresh'):
            self.main_window.pbirs_detail_next_refresh.setText("-")
    
    def _update_pbirs_details_fields(self, report_data):
        """Обновляет поля информации об отчете на вкладке Детали PBIRS."""
        import dateutil.parser

        if hasattr(self.main_window, 'pbirs_detail_name'):
            self.main_window.pbirs_detail_name.setText(report_data.get('Name', '-'))
        if hasattr(self.main_window, 'pbirs_detail_id'):
            self.main_window.pbirs_detail_id.setText(report_data.get('Id', '-'))
        if hasattr(self.main_window, 'pbirs_detail_folder'):
            self.main_window.pbirs_detail_folder.setText(report_data.get('Path', '-'))
        if hasattr(self.main_window, 'pbirs_detail_creator'):
            self.main_window.pbirs_detail_creator.setText(report_data.get('CreatedBy', '-'))

        # Источники данных (полные, каждый с новой строки, с типом, строкой подключения и пользователем)
        if hasattr(self.main_window, 'pbirs_detail_sources'):
            sources_list = report_data.get('DataSourcesList', [])
            if sources_list:
                lines = []
                for ds in sources_list:
                    if ds is None:
                        continue
                    conn_str = ds.get('ConnectionString', '')
                    kind = ds.get('Kind', '')
                    username = ds.get('Username', '')
                    if kind:
                        lines.append(f"  тип: {kind}")
                    if conn_str:
                        lines.append(f"  ConnectionString: {conn_str}")
                    else:
                        lines.append("  ConnectionString: (нет строки подключения)")
                    if username:
                        lines.append(f"  Пользователь: {username}")
                    lines.append("")  # пустая строка между источниками
                sources_text = "\n".join(lines).rstrip("\n") if lines else "Нет источников"
            else:
                sources_text = "Нет источников"
            self.main_window.pbirs_detail_sources.setText(sources_text)

        # Статус обновления (полный текст — в блоке информации об отчете показываем без обрезания)
        if hasattr(self.main_window, 'pbirs_detail_refresh_status'):
            last_status = report_data.get('LastStatus', 'Не запускался')
            self.main_window.pbirs_detail_refresh_status.setText(last_status)

        # Последнее обновление
        if hasattr(self.main_window, 'pbirs_detail_last_refresh'):
            last_run = report_data.get('LastRunDisplayFull', report_data.get('LastRunDisplay', 'Никогда'))
            self.main_window.pbirs_detail_last_refresh.setText(last_run)

        # Следующее обновление
        if hasattr(self.main_window, 'pbirs_detail_next_refresh'):
            next_run = report_data.get('NextRunDisplayDetailed', report_data.get('NextRunDisplay', 'Не запланировано'))
            self.main_window.pbirs_detail_next_refresh.setText(next_run)

        # Дата создания
        if hasattr(self.main_window, 'pbirs_detail_created_date'):
            created_date = report_data.get('CreatedDate', '')
            if created_date:
                try:
                    dt = dateutil.parser.parse(created_date)
                    created_date_fmt = dt.strftime("%d.%m.%Y %H:%M:%S")
                except:
                    created_date_fmt = created_date
            else:
                created_date_fmt = '-'
            self.main_window.pbirs_detail_created_date.setText(created_date_fmt)

        # Кем изменён
        if hasattr(self.main_window, 'pbirs_detail_modified_by'):
            self.main_window.pbirs_detail_modified_by.setText(report_data.get('ModifiedBy', '-'))

        # Дата изменения
        if hasattr(self.main_window, 'pbirs_detail_modified_date'):
            modified_date = report_data.get('ModifiedDate', '')
            if modified_date:
                try:
                    dt = dateutil.parser.parse(modified_date)
                    modified_date_fmt = dt.strftime("%d.%m.%Y %H:%M:%S")
                except:
                    modified_date_fmt = modified_date
            else:
                modified_date_fmt = '-'
            self.main_window.pbirs_detail_modified_date.setText(modified_date_fmt)
    
    def _set_pbirs_buttons_enabled(self, enabled):
        """Включает или отключает кнопки управления на вкладке Детали PBIRS."""
        if hasattr(self.main_window, 'pbirs_enable_btn'):
            self.main_window.pbirs_enable_btn.setEnabled(enabled)
        if hasattr(self.main_window, 'pbirs_disable_btn'):
            self.main_window.pbirs_disable_btn.setEnabled(enabled)
        if hasattr(self.main_window, 'pbirs_manual_refresh_btn'):
            self.main_window.pbirs_manual_refresh_btn.setEnabled(enabled)
    
    def enable_pbirs_refresh(self):
        """Включение автоматического обновления для выбранного отчета PBIRS."""
        self.main_window.log_message("Включение обновления PBIRS (заглушка)")
    
    def disable_pbirs_refresh(self):
        """Отключение автоматического обновления для выбранного отчета PBIRS."""
        self.main_window.log_message("Отключение обновления PBIRS (заглушка)")
    
    def trigger_pbirs_manual_refresh(self):
        """Ручной запуск обновления для выбранного отчета PBIRS."""
        self.main_window.log_message("Ручной запуск обновления PBIRS (заглушка)")
    
    def add_pbirs_schedule_time(self):
        """Добавление нового времени в расписание PBIRS."""
        self.main_window.log_message("Добавление времени в расписание PBIRS (заглушка)")
    
    def remove_pbirs_schedule_time(self):
        """Удаление выбранного времени из расписания PBIRS."""
        self.main_window.log_message("Удаление времени из расписания PBIRS (заглушка)")
    
    def save_pbirs_schedule(self):
        """Создание расписания для выбранного отчета PBIRS через диалог."""
        # Получаем данные выбранного отчёта из комбобокса
        combo = self.main_window.pbirs_details_report_combo
        index = combo.currentIndex()
        
        if index <= 0:
            self.main_window.log_message("✗ Не выбран отчёт для создания расписания")
            QMessageBox.warning(self.main_window, "Создание расписания", "Сначала выберите отчёт.")
            return
        
        report_data = combo.itemData(index)
        if not report_data:
            self.main_window.log_message("✗ Данные отчёта не найдены")
            return
        
        report_id = report_data.get('Id')
        report_name = report_data.get('Name', 'Без имени')
        report_path = report_data.get('Path', '')
        
        if not report_id:
            self.main_window.log_message("✗ Не найден ID отчёта")
            return
        
        if not report_path:
            self.main_window.log_message("✗ Не найден путь к отчёту (Path)")
            return
        
        # Проверяем, назначен ли пользователь для всех источников данных отчёта
        data_sources = report_data.get('DataSourcesList', [])
        sources_without_user = []
        for ds in data_sources:
            if ds is None:
                continue
            username = ds.get('Username', '') or ''
            if not username.strip():
                # Формируем название датасета: Kind - ConnectionString
                data_model = ds.get('DataModelDataSource', {}) or {}
                ds_kind = data_model.get('Kind', '') if isinstance(data_model, dict) else ''
                conn_str = ds.get('ConnectionString', '')
                if conn_str and ';' in conn_str:
                    conn_str = conn_str.split(';')[0]
                if ds_kind and conn_str:
                    ds_label = f"{ds_kind} - {conn_str}"
                elif conn_str:
                    ds_label = conn_str
                else:
                    ds_label = ds.get('Name', 'Без имени')
                sources_without_user.append(ds_label)
        
        if sources_without_user:
            sources_str = "\n".join(f"  • {name}" for name in sources_without_user)
            
            # Формируем ссылку на страницу настройки источников данных в веб-интерфейсе
            report_name_for_url = report_data.get('Name', '')
            client = self.main_window.client
            if client and hasattr(client, 'base_url'):
                server_base = client.base_url.replace('/api/v2.0', '')
            else:
                server_base = 'http://localhost/Reports'
            datasource_url = f"{server_base}/manage/catalogitem/datasources/{report_name_for_url}"
            
            msg = (
                f"Для следующих датасетов отчёта '{report_name}' "
                f"не назначен пользователь и пароль:\n\n{sources_str}\n\n"
                f"Расписание может не работать без учётных данных."
            )
            
            # Создаём кастомный диалог с кнопками "Закрыть" и "Перейти к заполнению"
            from PyQt6.QtWidgets import QDialogButtonBox
            dialog = QMessageBox(self.main_window)
            dialog.setWindowTitle("Внимание: отсутствуют учётные данные")
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setText(msg)
            
            close_btn = dialog.addButton("Закрыть", QMessageBox.ButtonRole.RejectRole)
            go_btn = dialog.addButton("Перейти к заполнению", QMessageBox.ButtonRole.ActionRole)
            
            dialog.exec()
            
            if dialog.clickedButton() == go_btn:
                import webbrowser
                webbrowser.open(datasource_url)
                self.main_window.log_message(
                    f"Открыт веб-интерфейс для настройки источников: {datasource_url}"
                )
            
            self.main_window.log_message(
                f"Создание расписания отменено: для датасетов {', '.join(sources_without_user)} "
                f"не назначен пользователь"
            )
            return
        
        # Открываем диалог создания расписания
        from src.ui.pbirs_schedule_dialog import PBIRSScheduleDialog
        
        dialog = PBIRSScheduleDialog(self.main_window, report_name)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.main_window.log_message("Создание расписания отменено")
            return
        
        result = dialog.get_result()
        if not result:
            return
        
        schedule_name = result["name"]
        period_type = result["period_type"]
        selected_days = result["days"]
        hour = result["hour"]
        minute = result["minute"]
        
        # Формируем дату старта — завтра в указанное время (часовой пояс UTC+5)
        from datetime import datetime, timedelta, timezone
        local_tz = timezone(timedelta(hours=5))
        tomorrow = datetime.now(local_tz) + timedelta(days=1)
        start_datetime = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        start_datetime_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S+05:00")
        
        # Формируем Recurrence в зависимости от выбранного типа периодичности
        # API PBIRS требует, чтобы неиспользуемые типы были null
        recurrence = {
            "MinuteRecurrence": None,
            "DailyRecurrence": None,
            "WeeklyRecurrence": None,
            "MonthlyRecurrence": None,
            "MonthlyDOWRecurrence": None,
        }
        
        period_label = ""  # для лога
        
        if period_type == "daily":
            recurrence["DailyRecurrence"] = {
                "DaysInterval": 1
            }
            period_label = "Ежедневно"
            
        elif period_type == "weekly":
            recurrence["WeeklyRecurrence"] = {
                "WeeksInterval": 1,
                "WeeksIntervalSpecified": True,
                "DaysOfWeek": {
                    "Sunday": "Sunday" in selected_days,
                    "Monday": "Monday" in selected_days,
                    "Tuesday": "Tuesday" in selected_days,
                    "Wednesday": "Wednesday" in selected_days,
                    "Thursday": "Thursday" in selected_days,
                    "Friday": "Friday" in selected_days,
                    "Saturday": "Saturday" in selected_days,
                }
            }
            day_names_ru = {
                "Monday": "Пн", "Tuesday": "Вт", "Wednesday": "Ср",
                "Thursday": "Чт", "Friday": "Пт", "Saturday": "Сб", "Sunday": "Вс"
            }
            days_str = ", ".join(day_names_ru[d] for d in selected_days)
            period_label = f"[{days_str}]"
        
        # Формируем тело запроса
        plan_data = {
            "CatalogItemPath": report_path,
            "EventType": "DataModelRefresh",
            "Description": schedule_name,
            "Schedule": {
                "Definition": {
                    "StartDateTime": start_datetime_str,
                    "EndDate": "0001-01-01T00:00:00Z",
                    "EndDateSpecified": False,
                    "Recurrence": recurrence,
                }
            },
            "ParameterValues": []
        }
        
        try:
            client = self.main_window.client
            if not client or not hasattr(client, 'create_cache_refresh_plan'):
                self.main_window.log_message("✗ Клиент PBIRS не инициализирован")
                return
            
            client.create_cache_refresh_plan(plan_data)
            
            self.main_window.log_message(
                f"✓ Расписание '{schedule_name}' создано для '{report_name}': "
                f"{period_label} в {hour:02d}:{minute:02d}"
            )
            
            # Обновляем данные через 1 секунду
            QTimer.singleShot(1000, self.main_window.load_pbirs_reports)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка при создании расписания: {e}")

    def delete_pbirs_schedule(self):
        """Удаление выбранного расписания для отчета PBIRS через API."""
        table = self.main_window.pbirs_refresh_plans_table
        current_row = table.currentRow()
        
        if current_row < 0:
            self.main_window.log_message("✗ Не выбрано расписание для удаления")
            return
        
        # Получаем объект плана из userData первой ячейки
        plan_item = table.item(current_row, 0)
        if not plan_item:
            self.main_window.log_message("✗ Не удалось получить данные расписания")
            return
        
        plan = plan_item.data(Qt.ItemDataRole.UserRole)
        if not plan:
            self.main_window.log_message("✗ Не удалось получить данные расписания")
            return
        
        plan_id = plan.get('Id') or plan.get('PlanId')
        plan_name = plan.get('Description') or plan.get('Name', 'Без названия')
        
        if not plan_id:
            self.main_window.log_message(f"✗ Не найден ID расписания для '{plan_name}'")
            return
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self.main_window,
            "Подтверждение удаления",
            f"Вы точно хотите удалить расписание '{plan_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            self.main_window.log_message("Удаление отменено")
            return
        
        try:
            client = self.main_window.client
            if not client or not hasattr(client, 'delete_cache_refresh_plan'):
                self.main_window.log_message("✗ Клиент PBIRS не инициализирован")
                return
            
            client.delete_cache_refresh_plan(plan_id)
            self.main_window.log_message(f"✓ Расписание '{plan_name}' успешно удалено")
            
            # Обновляем данные через 1 секунду после удаления
            QTimer.singleShot(1000, self.main_window.load_pbirs_reports)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка при удалении расписания: {e}")

    def execute_pbirs_schedule(self):
        """Немедленный запуск выбранного расписания обновления кэша PBIRS."""
        table = self.main_window.pbirs_refresh_plans_table
        current_row = table.currentRow()

        if current_row < 0:
            self.main_window.log_message("✗ Не выбрано расписание для запуска")
            return

        # Получаем объект плана из userData первой ячейки
        plan_item = table.item(current_row, 0)
        if not plan_item:
            self.main_window.log_message("✗ Не удалось получить данные расписания")
            return

        plan = plan_item.data(Qt.ItemDataRole.UserRole)
        if not plan:
            self.main_window.log_message("✗ Не удалось получить данные расписания")
            return

        plan_id = plan.get('Id') or plan.get('PlanId')
        plan_name = plan.get('Description') or plan.get('Name', 'Без названия')

        if not plan_id:
            self.main_window.log_message(f"✗ Не найден ID расписания для '{plan_name}'")
            return

        # Подтверждение запуска
        reply = QMessageBox.question(
            self.main_window,
            "Подтверждение запуска",
            f"Запустить обновление '{plan_name}' сейчас?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            self.main_window.log_message("Запуск отменён")
            return

        try:
            client = self.main_window.client
            if not client or not hasattr(client, 'execute_cache_refresh_plan'):
                self.main_window.log_message("✗ Клиент PBIRS не инициализирован")
                return

            client.execute_cache_refresh_plan(plan_id)
            self.main_window.log_message(f"✓ Расписание '{plan_name}' запущено на выполнение")

            # Обновляем данные через 1 секунду
            QTimer.singleShot(1000, self.main_window.load_pbirs_reports)

        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка при запуске расписания: {e}")

    def show_pbirs_refresh_plans_context_menu(self, position):
        """Показывает контекстное меню для таблицы расписаний PBIRS."""
        table = self.main_window.pbirs_refresh_plans_table
        
        menu = QMenu(self.main_window)
        
        # Создать расписание — доступно всегда
        create_action = QAction("Создать расписание", self.main_window)
        create_action.triggered.connect(self.main_window.save_pbirs_schedule)
        menu.addAction(create_action)
        
        # Удалить расписание — только если есть выбранная строка с расписанием
        current_row = table.currentRow()
        has_selected_plan = current_row >= 0 and table.item(current_row, 0) is not None
        
        if has_selected_plan:
            # Разделитель перед действиями над выбранным расписанием
            menu.addSeparator()

            execute_action = QAction("Обновить сейчас", self.main_window)
            execute_action.triggered.connect(self.main_window.execute_pbirs_schedule)
            menu.addAction(execute_action)

            delete_action = QAction("Удалить расписание", self.main_window)
            delete_action.triggered.connect(self.main_window.delete_pbirs_schedule)
            menu.addAction(delete_action)

        menu.exec(table.viewport().mapToGlobal(position))