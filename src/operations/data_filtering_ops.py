#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Операции фильтрации и мониторинга датасетов.
Объединяет функционал из filtering.py и monitoring.py.
"""

import logging

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtGui import QBrush

from src.ui.theme_colors import ThemeColors
from src.operations.base_operations import BaseOperations

logger = logging.getLogger(__name__)


class DataFilteringOperations(BaseOperations):
    """Операции для фильтрации и мониторинга датасетов."""
    
    def __init__(self, main_window):
        """
        Инициализирует операции фильтрации и мониторинга.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        super().__init__(main_window)
    
    # ========== Методы фильтрации ==========
    
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
                if 'in progress' not in status and 'refreshing' not in status and 'unknown' not in status:
                    include = False
            
            # Фильтр по названию датасета (текстовый фильтр)
            if hasattr(self.main_window, 'dataset_name_filter') and self.main_window.dataset_name_filter:
                filter_text = self.main_window.dataset_name_filter.text().strip().lower()
                if filter_text:
                    dataset_name = ds.get('name', '').lower()
                    if filter_text not in dataset_name:
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
            # Преобразуем статус "unknown" в "в процессе обновления" для отображения
            if status.lower() == 'unknown':
                status = 'в процессе обновления'
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
    
    # ========== Методы мониторинга ==========
    
    def start_monitoring(self):
        """Запускает мониторинг в реальном времени."""
        if self.main_window.auto_refresh_enabled:
            self.main_window.log_message("Мониторинг уже запущен")
            return
        
        try:
            # Запускаем таймер с интервалом 60 секунд (можно настроить)
            interval = 60000  # 60 секунд в миллисекундах
            self.main_window.update_timer.start(interval)
            self.main_window.auto_refresh_enabled = True
            
            # Обновляем UI
            self.main_window.start_monitor_btn.setEnabled(False)
            self.main_window.stop_monitor_btn.setEnabled(True)
            self.main_window.status_bar.showMessage("Мониторинг запущен", 3000)
            self.main_window.log_message(f"✓ Мониторинг запущен (интервал: {interval//1000} сек)")
            
            # Сразу обновляем данные
            self.main_window.refresh_data()
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка запуска мониторинга: {e}")
            self.main_window.status_bar.showMessage("Ошибка запуска мониторинга", 5000)
    
    def stop_monitoring(self):
        """Останавливает мониторинг в реальном времени."""
        if not self.main_window.auto_refresh_enabled:
            self.main_window.log_message("Мониторинг не запущен")
            return
        
        try:
            self.main_window.update_timer.stop()
            self.main_window.auto_refresh_enabled = False
            
            # Обновляем UI
            self.main_window.start_monitor_btn.setEnabled(True)
            self.main_window.stop_monitor_btn.setEnabled(False)
            self.main_window.status_bar.showMessage("Мониторинг остановлен", 3000)
            self.main_window.log_message("✓ Мониторинг остановлен")
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка остановки мониторинга: {e}")
            self.main_window.status_bar.showMessage("Ошибка остановки мониторинга", 5000)