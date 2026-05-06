#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Базовые методы, общие для всех классов методов UI.
Содержит вспомогательные функции работы со временем, логирование и общие утилиты.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class BaseMethods:
    """Базовый класс для всех классов методов UI."""
    
    def __init__(self, main_window):
        """
        Инициализирует базовые методы.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    # ========== Вспомогательные функции для работы со временем ==========
    
    def _parse_time(self, time_str: str) -> Tuple[int, int]:
        """
        Парсит строку времени формата HH:MM в кортеж (часы, минуты).
        
        Args:
            time_str: Строка времени (например, "14:30")
            
        Returns:
            Кортеж (часы, минуты)
        """
        try:
            if not time_str:
                return (0, 0)
            # Убираем возможные секунды
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return (hours, minutes)
        except (ValueError, IndexError):
            return (0, 0)
    
    def _convert_utc_to_local(self, utc_time_str: str, from_offset: int = 0, to_offset: int = 5) -> str:
        """
        Конвертирует время из одного часового пояса в другой.
        
        Args:
            utc_time_str: Время в формате HH:MM (в часовом поясе from_offset)
            from_offset: Смещение исходного времени относительно UTC (часы)
            to_offset: Смещение целевого времени относительно UTC (часы)
            
        Returns:
            Время в формате HH:MM в целевом поясе
        """
        try:
            hours, minutes = self._parse_time(utc_time_str)
            # Применяем разницу смещений
            diff = to_offset - from_offset
            new_hours = hours + diff
            
            # Обработка перехода через сутки
            if new_hours < 0:
                new_hours += 24
                # Флаг предыдущего дня (для расписания)
            elif new_hours >= 24:
                new_hours -= 24
                # Флаг следующего дня
            
            return f"{new_hours:02d}:{minutes:02d}"
        except Exception:
            return utc_time_str
    
    def _convert_schedule_times(self, times: List[str], from_offset: int, to_offset: int) -> List[str]:
        """
        Конвертирует список времен расписания из одного часового пояса в другой.
        
        Args:
            times: Список строк времени в формате HH:MM
            from_offset: Смещение исходного времени относительно UTC
            to_offset: Смещение целевого времени относительно UTC
            
        Returns:
            Отсортированный список времен в целевом поясе
        """
        converted = []
        for t in times:
            converted.append(self._convert_utc_to_local(t, from_offset, to_offset))
        # Сортируем по времени
        converted.sort(key=lambda x: self._parse_time(x))
        return converted
    
    def _calculate_next_refresh(self, schedule_times: List[str], current_local_time: datetime) -> Optional[datetime]:
        """
        Вычисляет следующее время обновления на основе расписания.
        
        Args:
            schedule_times: Список времен расписания в локальном часовом поясе (формат HH:MM)
            current_local_time: Текущее время в том же часовом поясе
            
        Returns:
            datetime следующего обновления или None, если обновлений больше не будет сегодня
        """
        if not schedule_times:
            return None
        
        current_hour = current_local_time.hour
        current_minute = current_local_time.minute
        
        # Ищем ближайшее время сегодня
        for time_str in schedule_times:
            hours, minutes = self._parse_time(time_str)
            # Если время сегодня уже прошло, пропускаем
            if hours < current_hour or (hours == current_hour and minutes <= current_minute):
                continue
            # Нашли ближайшее будущее время сегодня
            next_refresh = current_local_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            return next_refresh
        
        # Если сегодня больше нет обновлений, берем первое время завтра
        first_time = schedule_times[0]
        hours, minutes = self._parse_time(first_time)
        next_refresh = current_local_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        next_refresh += timedelta(days=1)
        return next_refresh
    
    def _format_datetime_for_display(self, dt: datetime) -> str:
        """
        Форматирует datetime для отображения пользователю.
        
        Args:
            dt: Объект datetime
            
        Returns:
            Строка в формате "дд.мм.гггг, HH:MM"
        """
        return dt.strftime("%d.%m.%Y, %H:%M")
    
    # ========== Общие утилиты ==========
    
    def log_message(self, message: str, level: str = "info"):
        """
        Логирует сообщение через главное окно.
        
        Args:
            message: Текст сообщения
            level: Уровень логирования ('info', 'warning', 'error')
        """
        if hasattr(self.main_window, 'log_message'):
            self.main_window.log_message(message, level)
        else:
            getattr(logger, level)(message)
    
    def update_ui_state(self, connected: bool):
        """
        Обновляет состояние UI в зависимости от подключения.
        
        Args:
            connected: True если подключено к Power BI
        """
        if connected:
            if hasattr(self.main_window, 'update_ui_for_connected_state'):
                self.main_window.update_ui_for_connected_state()
        else:
            if hasattr(self.main_window, 'update_ui_for_disconnected_state'):
                self.main_window.update_ui_for_disconnected_state()