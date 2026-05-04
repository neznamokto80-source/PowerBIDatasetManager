#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы загрузки данных из Power BI (рабочие области, датасеты, обновление).
"""

import logging
from typing import List, Dict, Any

from PyQt6.QtWidgets import QTableWidgetItem, QTreeWidgetItem
from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)


class DataLoadingMethods:
    """Методы для загрузки данных из Power BI."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы загрузки данных.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def refresh_data(self):
        """Обновление данных."""
        if not self.main_window.client or not self.main_window.current_workspace:
            self.main_window.log_message("Не подключено к Power BI или не выбрана рабочая область")
            return
        
        try:
            self.main_window.log_message("Обновление данных...")
            self.main_window.status_bar.showMessage("Обновление данных...")
            
            # Обновляем список датасетов
            self.main_window.load_datasets()
            
            # Если есть выбранный датасет, обновляем его детали
            if self.main_window.current_dataset:
                self.main_window.update_dataset_details(self.main_window.current_dataset)
            
            self.main_window.status_bar.showMessage("Данные обновлены", 3000)
            self.main_window.log_message("✓ Данные обновлены")
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка при обновлении данных: {e}")
            self.main_window.status_bar.showMessage("Ошибка обновления", 5000)
    
    def load_workspaces(self):
        """Загружает список рабочих областей из Power BI."""
        try:
            self.main_window.log_message("Обновление списка рабочих областей...")
            self.main_window.workspaces = self.main_window.client.get_workspaces()
            self.main_window.log_message(f"✓ Загружено рабочих областей: {len(self.main_window.workspaces)}")
            
            # Обновление комбобокса
            self.main_window.workspace_combo.clear()
            if self.main_window.workspaces:
                for ws in self.main_window.workspaces:
                    name = ws.get('name', 'Без имени')
                    self.main_window.workspace_combo.addItem(name, ws.get('id'))
            else:
                self.main_window.workspace_combo.addItem("Нет рабочих областей")
            
            # Если есть рабочие области, выбираем первую
            if self.main_window.workspaces:
                self.main_window.current_workspace = self.main_window.workspaces[0].get('id')
                self.main_window.workspace_combo.setCurrentIndex(0)
                self.main_window.load_datasets()
            
            self.main_window.status_bar.showMessage("Рабочие области обновлены", 3000)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка загрузки рабочих областей: {e}")
            self.main_window.status_bar.showMessage("Ошибка загрузки", 5000)
    
    def load_datasets(self):
        """Загружает датасеты из выбранной рабочей области."""
        if not self.main_window.current_workspace:
            self.main_window.log_message("Не выбрана рабочая область")
            return
        
        try:
            self.main_window.log_message(
                f"Загрузка датасетов из рабочей области {self.main_window.current_workspace}..."
            )
            datasets = self.main_window.client.get_datasets_in_workspace(self.main_window.current_workspace)
            self.main_window.datasets = datasets
            self.main_window.log_message(f"✓ Загружено датасетов: {len(datasets)}")
            
            # Обновление дерева датасетов
            self.main_window.dataset_tree.clear()
            for ds in datasets:
                name = ds.get('name', 'Без имени')
                status = ds.get('status', 'unknown')
                refresh = ds.get('lastRefreshTime', 'никогда')
                item = QTreeWidgetItem([name, status, refresh])
                self.main_window.dataset_tree.addTopLevelItem(item)
            
            # Обновление таблицы датасетов
            self.update_dataset_table(datasets)
            
            # Обновление статистики
            self.update_stats(datasets)
            
            self.main_window.status_bar.showMessage("Датасеты загружены", 3000)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка загрузки датасетов: {e}")
            self.main_window.status_bar.showMessage("Ошибка загрузки", 5000)
    
    def update_dataset_table(self, datasets):
        """Обновляет таблицу датасетов."""
        self.main_window.dataset_table.setRowCount(len(datasets))
        for row, ds in enumerate(datasets):
            name = ds.get('name', 'Без имени')
            workspace = self.main_window.get_workspace_name(ds.get('workspaceId', ''))
            status = ds.get('status', 'unknown')
            last_refresh = ds.get('lastRefreshTime', 'никогда')
            next_refresh = ds.get('nextRefreshTime', 'не запланировано')
            
            self.main_window.dataset_table.setItem(row, 0, QTableWidgetItem(name))
            self.main_window.dataset_table.setItem(row, 1, QTableWidgetItem(workspace))
            self.main_window.dataset_table.setItem(row, 2, QTableWidgetItem(status))
            self.main_window.dataset_table.setItem(row, 3, QTableWidgetItem(last_refresh))
            self.main_window.dataset_table.setItem(row, 4, QTableWidgetItem(next_refresh))
    
    def update_stats(self, datasets):
        """Обновляет статистику."""
        total = len(datasets)
        enabled = sum(1 for ds in datasets if ds.get('isRefreshable', False))
        failed = sum(1 for ds in datasets if ds.get('status', '').lower() == 'failed')
        last_update = max(
            (ds.get('lastRefreshTime') for ds in datasets if ds.get('lastRefreshTime')), 
            default='никогда'
        )
        
        self.main_window.total_datasets_label.setText(f"Всего датасетов: {total}")
        self.main_window.enabled_refresh_label.setText(f"С обновлением: {enabled}")
        self.main_window.failed_refresh_label.setText(f"С ошибками: {failed}")
        self.main_window.last_update_label.setText(f"Последнее обновление: {last_update}")
    
    def get_workspace_name(self, workspace_id):
        """Возвращает имя рабочей области по ID."""
        for ws in self.main_window.workspaces:
            if ws.get('id') == workspace_id:
                return ws.get('name', 'Без имени')
        return workspace_id
    
    def update_dataset_details(self, dataset):
        """Обновляет детальную информацию о выбранном датасете."""
        if not dataset:
            return
        
        name = dataset.get('name', 'Без имени')
        dataset_id = dataset.get('id', 'N/A')
        workspace_id = dataset.get('workspaceId', '')
        workspace_name = self.main_window.get_workspace_name(workspace_id)
        status = dataset.get('status', 'unknown')
        last_refresh = dataset.get('lastRefreshTime', 'никогда')
        next_refresh = dataset.get('nextRefreshTime', 'не запланировано')
        schedule = dataset.get('refreshSchedule', {}).get('frequency', 'не настроено')
        is_refreshable = dataset.get('isRefreshable', False)
        
        # Обновляем поля деталей
        self.main_window.detail_name.setText(name)
        self.main_window.detail_id.setText(dataset_id)
        self.main_window.detail_workspace.setText(workspace_name)
        self.main_window.detail_refresh_status.setText(status)
        self.main_window.detail_last_refresh.setText(last_refresh)
        self.main_window.detail_next_refresh.setText(next_refresh)
        self.main_window.detail_schedule.setText(schedule)
        
        # Обновляем статус кнопок в зависимости от возможности обновления
        self.main_window.enable_btn.setEnabled(not is_refreshable)
        self.main_window.disable_btn.setEnabled(is_refreshable)