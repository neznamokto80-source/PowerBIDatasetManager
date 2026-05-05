#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы фильтрации датасетов.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtGui import QBrush, QColor

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
    
    def _parse_time(self, time_str: str):
        """
        Парсит строку времени формата HH:MM в кортеж (часы, минуты).
        """
        try:
            if not time_str:
                return (0, 0)
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return (hours, minutes)
        except (ValueError, IndexError):
            return (0, 0)
    
    def _convert_utc_to_local(self, utc_time_str: str, from_offset: int = 0, to_offset: int = 5) -> str:
        """
        Конвертирует время из одного часового пояса в другой.
        """
        try:
            hours, minutes = self._parse_time(utc_time_str)
            diff = to_offset - from_offset
            new_hours = hours + diff
            
            if new_hours < 0:
                new_hours += 24
            elif new_hours >= 24:
                new_hours -= 24
            
            return f"{new_hours:02d}:{minutes:02d}"
        except Exception:
            return utc_time_str
    
    def _convert_schedule_times(self, times: List[str], from_offset: int, to_offset: int) -> List[str]:
        """
        Конвертирует список времен расписания из одного часового пояса в другой.
        """
        converted = []
        for t in times:
            converted.append(self._convert_utc_to_local(t, from_offset, to_offset))
        converted.sort(key=lambda x: self._parse_time(x))
        return converted
    
    def _calculate_next_refresh(self, schedule_times: List[str], current_local_time: datetime):
        """
        Вычисляет следующее время обновления на основе расписания.
        """
        if not schedule_times:
            return None
        
        current_hour = current_local_time.hour
        current_minute = current_local_time.minute
        
        for time_str in schedule_times:
            hours, minutes = self._parse_time(time_str)
            if hours < current_hour or (hours == current_hour and minutes <= current_minute):
                continue
            next_refresh = current_local_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            return next_refresh
        
        first_time = schedule_times[0]
        hours, minutes = self._parse_time(first_time)
        next_refresh = current_local_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        next_refresh += timedelta(days=1)
        return next_refresh
    
    def _format_datetime_for_display(self, dt: datetime) -> str:
        """
        Форматирует datetime для отображения пользователю.
        """
        return dt.strftime("%d.%m.%Y, %H:%M")
    
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
            
            # Цветовое выделение для дерева
            background_color = None
            status_lower = status.lower()
            if status_lower in ('failed', 'error'):
                background_color = QColor(255, 200, 200)  # светло-красный
            else:
                refresh_schedule = ds.get('refresh_schedule', {})
                enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None
                if enabled is False:
                    # Выбор цвета в зависимости от темы
                    if self.main_window.current_theme == "Тёмная":
                        background_color = QColor(60, 60, 60)  # тёмно-серый для тёмной темы
                    else:
                        background_color = QColor(183,134,145)  # очень светло-серый для светлой темы
                else:
                    # Проверяем, есть ли следующее обновление "не запланировано"
                    next_refresh = ds.get('nextRefreshTime', 'не запланировано')
                    if next_refresh == "не запланировано":
                        # Выделение строк, где следующее обновление не запланировано
                        if self.main_window.current_theme == "Тёмная":
                            background_color = QColor(80, 80, 40)  # тёмно-жёлтый для тёмной темы
                        else:
                            background_color = QColor(255, 255, 230)  # очень светло-жёлтый для светлой темы
            
            if background_color:
                brush = QBrush(background_color)
                for col in range(item.columnCount()):
                    item.setBackground(col, brush)
            
            self.main_window.dataset_tree.addTopLevelItem(item)
        
        self.main_window.log_message(f"Применены фильтры. Показано датасетов: {len(filtered_datasets)}")