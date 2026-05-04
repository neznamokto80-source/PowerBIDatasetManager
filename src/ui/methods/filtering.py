#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы фильтрации датасетов.
"""

import logging
from typing import List, Dict, Any

from PyQt6.QtWidgets import QTreeWidgetItem

logger = logging.getLogger(__name__)


class FilteringMethods:
    """Методы для фильтрации датасетов."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы фильтрации.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def apply_filters(self):
        """Применяет фильтры к списку датасетов."""
        if not self.main_window.datasets:
            return
        
        filtered_datasets = []
        
        for ds in self.main_window.datasets:
            include = True
            
            # Фильтр по включенным обновлениям
            if self.main_window.filter_enabled.isChecked():
                if not ds.get('isRefreshable', False):
                    include = False
            
            # Фильтр по недавним обновлениям (последние 24 часа)
            if self.main_window.filter_recent.isChecked():
                last_refresh = ds.get('lastRefreshTime')
                if not last_refresh or last_refresh == 'никогда':
                    include = False
                # Здесь можно добавить логику проверки времени
            
            # Фильтр по ошибкам
            if self.main_window.filter_errors.isChecked():
                status = ds.get('status', '').lower()
                if 'failed' not in status and 'error' not in status:
                    include = False
            
            # Фильтр "кроме неиспользуемых" (статус not used)
            if self.main_window.filter_except_not_use.isChecked():
                status = ds.get('status', '').lower()
                if 'not used' in status:
                    include = False
            
            # Фильтр по обновляющимся (in progress)
            if self.main_window.filter_in_progress.isChecked():
                status = ds.get('status', '').lower()
                if 'in progress' not in status and 'refreshing' not in status:
                    include = False
            
            if include:
                filtered_datasets.append(ds)
        
        # Обновляем таблицу и дерево отфильтрованными данными
        self.main_window.update_dataset_table(filtered_datasets)
        
        # Обновляем дерево датасетов
        self.main_window.dataset_tree.clear()
        for ds in filtered_datasets:
            name = ds.get('name', 'Без имени')
            status = ds.get('status', 'unknown')
            refresh = ds.get('lastRefreshTime', 'никогда')
            item = QTreeWidgetItem([name, status, refresh])
            self.main_window.dataset_tree.addTopLevelItem(item)
        
        self.main_window.log_message(f"Применены фильтры. Показано датасетов: {len(filtered_datasets)}")