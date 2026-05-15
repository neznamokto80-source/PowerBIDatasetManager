#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Базовый класс для всех операций UI.
Содержит общие утилиты и делегирует функции времени модулю utils.time_utils.
"""

import logging
from datetime import datetime
from typing import List, Optional

from src.utils import time_utils

logger = logging.getLogger(__name__)


class BaseOperations:
    """Базовый класс для всех классов операций UI."""
    
    def __init__(self, main_window):
        """
        Инициализирует базовые операции.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    # ========== Вспомогательные функции для работы со временем ==========
    # Делегируем функции модулю time_utils
    
    def _parse_time(self, time_str: str):
        """Парсит строку времени формата HH:MM в кортеж (часы, минуты)."""
        return time_utils.parse_time(time_str)
    
    def _convert_utc_to_local(self, utc_time_str: str, from_offset: int = 0, to_offset: int = 5) -> str:
        """Конвертирует время из одного часового пояса в другой."""
        return time_utils.convert_utc_to_local(utc_time_str, from_offset, to_offset)
    
    def _convert_schedule_times(self, times: List[str], from_offset: int, to_offset: int) -> List[str]:
        """Конвертирует список времен расписания из одного часового пояса в другой."""
        return time_utils.convert_schedule_times(times, from_offset, to_offset)
    
    def _calculate_next_refresh(self, schedule_times: List[str], current_local_time: datetime) -> Optional[datetime]:
        """Вычисляет следующее время обновления на основе расписания."""
        return time_utils.calculate_next_refresh(schedule_times, current_local_time)
    
    def _format_datetime_for_display(self, dt: datetime) -> str:
        """Форматирует datetime для отображения пользователю."""
        return time_utils.format_datetime_for_display(dt)
    
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