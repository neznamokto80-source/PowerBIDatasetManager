#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы фильтрации датасетов.
"""

import logging

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtGui import QBrush

from src.ui.theme_colors import ThemeColors
from .base_methods import BaseMethods

logger = logging.getLogger(__name__)


class FilteringMethods(BaseMethods):
    """Методы для фильтрации датасетов."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы фильтрации.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        super().__init__(main_window)
    
    # Вспомогательные функции для работы со временем унаследованы от BaseMethods
    
    def apply_filters(self):
        """Применяет фильтры к списку датасетов."""
        if not self.main_window.datasets:
            return
        
        filtered_datasets = []
        
        for ds in self.main_window.datasets:
            include = True
            
            # Фильтр по включенным обновлениям (автообновление включено)
            if self.main_window.filter_enabled.isChecked():
                refresh_schedule = ds.get('refresh_schedule', {})
                enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None
                if enabled is not True:
                    include = False
            
            # Фильтр по выключенному автообновлению
            if self.main_window.filter_recent.isChecked():
                refresh_schedule = ds.get('refresh_schedule', {})
                enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None
                if enabled is not False:
                    include = False
            
            # Фильтр по ошибкам
            if self.main_window.filter_errors.isChecked():
                status = ds.get('status', '').lower()
                if 'failed' not in status and 'error' not in status:
                    include = False
            
            # Фильтр "Все кроме not_use" (проверка названия)
            if self.main_window.filter_except_not_use.isChecked():
                name = ds.get('name', '').lower()
                if 'not_use' in name:
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
            
            # Цветовое выделение для дерева - используем общую логику определения цвета
            background_color = ThemeColors.get_dataset_background_color(ds, self.main_window.current_theme)
            
            if background_color:
                brush = QBrush(background_color)
                for col in range(item.columnCount()):
                    item.setBackground(col, brush)
            
            self.main_window.dataset_tree.addTopLevelItem(item)
        
        self.main_window.log_message(f"Применены фильтры. Показано датасетов: {len(filtered_datasets)}")