#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для вычисления следующего запуска расписания.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dateutil import parser as date_parser


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Парсит строку даты-времени в объект datetime."""
    if not dt_str:
        return None
    try:
        # Пробуем разные форматы
        return date_parser.parse(dt_str)
    except (ValueError, TypeError):
        return None


def calculate_next_run(
    start_dt: Optional[str],
    end_date: Optional[str],
    recurrence_type: Optional[str],
    recurrence_raw: Optional[str],
    last_run_time: Optional[str] = None
) -> Optional[datetime]:
    """
    Вычисляет следующую дату/время запуска на основе расписания.
    
    Args:
        start_dt: Дата начала расписания (строка)
        end_date: Дата окончания расписания (строка)
        recurrence_type: Тип периодичности (Minute, Daily, Weekly, Monthly, MonthlyDOW)
        recurrence_raw: Сырые данные периодичности (JSON строка)
        last_run_time: Время последнего запуска (строка)
    
    Returns:
        datetime или None если невозможно вычислить
    """
    # Если нет расписания
    if not start_dt or not recurrence_type:
        return None
    
    start_datetime = parse_datetime(start_dt)
    if not start_datetime:
        return None
    
    # Проверяем, не истекло ли расписание
    if end_date:
        end_datetime = parse_datetime(end_date)
        if end_datetime:
            # Приводим aware datetime к наивному для сравнения с datetime.now()
            if end_datetime.tzinfo is not None:
                end_datetime_naive = end_datetime.replace(tzinfo=None)
            else:
                end_datetime_naive = end_datetime
            if datetime.now() > end_datetime_naive:
                return None
    
    # Берем базовую дату для расчета
    base_datetime = parse_datetime(last_run_time) if last_run_time else datetime.now()
    # Если base_datetime aware, преобразуем в наивный
    if base_datetime and base_datetime.tzinfo is not None:
        base_datetime = base_datetime.replace(tzinfo=None)
    
    # Если последний запуск был после начала расписания, используем его как базовую дату
    if last_run_time:
        last_run_datetime = parse_datetime(last_run_time)
        if last_run_datetime:
            # Приводим к наивному для сравнения
            if last_run_datetime.tzinfo is not None:
                last_run_datetime_naive = last_run_datetime.replace(tzinfo=None)
            else:
                last_run_datetime_naive = last_run_datetime
            if start_datetime.tzinfo is not None:
                start_datetime_naive = start_datetime.replace(tzinfo=None)
            else:
                start_datetime_naive = start_datetime
            if last_run_datetime_naive > start_datetime_naive:
                base_datetime = last_run_datetime_naive
    
    # Вычисляем следующее выполнение в зависимости от типа периодичности
    try:
        if recurrence_type == "Minute":
            # Парсим интервал в минутах
            if recurrence_raw:
                import json
                recurrence_data = json.loads(recurrence_raw)
                minute_recurrence = recurrence_data.get("MinuteRecurrence", {})
                interval = minute_recurrence.get("MinutesInterval", 60)
            else:
                interval = 60  # по умолчанию каждый час
            
            # Вычисляем следующее выполнение
            next_run = base_datetime + timedelta(minutes=interval)
            # Убедимся, что next_run наивный
            if next_run.tzinfo is not None:
                next_run = next_run.replace(tzinfo=None)
            
            # Если следующее выполнение раньше текущего времени, добавляем еще интервал
            while next_run <= datetime.now():
                next_run += timedelta(minutes=interval)
                if next_run.tzinfo is not None:
                    next_run = next_run.replace(tzinfo=None)
            
            return next_run
            
        elif recurrence_type == "Daily":
            # Парсим интервал в днях
            if recurrence_raw:
                import json
                recurrence_data = json.loads(recurrence_raw)
                daily_recurrence = recurrence_data.get("DailyRecurrence", {})
                interval = daily_recurrence.get("DaysInterval", 1)
            else:
                interval = 1
            
            # Вычисляем следующее выполнение
            next_run = base_datetime + timedelta(days=interval)
            
            # Если следующее выполнение раньше текущего времени, добавляем еще интервал
            while next_run <= datetime.now():
                next_run += timedelta(days=interval)
            
            return next_run
            
        elif recurrence_type == "Weekly":
            # Для Weekly нужен более сложный расчет с учетом дней недели
            # Пока возвращаем упрощенный вариант
            if recurrence_raw:
                import json
                recurrence_data = json.loads(recurrence_raw)
                weekly_recurrence = recurrence_data.get("WeeklyRecurrence", {})
                interval = weekly_recurrence.get("WeeksInterval", 1)
            else:
                interval = 1
            
            next_run = base_datetime + timedelta(weeks=interval)
            while next_run <= datetime.now():
                next_run += timedelta(weeks=interval)
            
            return next_run
            
        elif recurrence_type in ["Monthly", "MonthlyDOW"]:
            # Для Monthly также упрощенный вариант
            if recurrence_raw:
                import json
                recurrence_data = json.loads(recurrence_raw)
                monthly_recurrence = recurrence_data.get("MonthlyRecurrence") or recurrence_data.get("MonthlyDOWRecurrence", {})
                interval = monthly_recurrence.get("MonthsInterval", 1)
            else:
                interval = 1
            
            # Просто добавляем месяцы (упрощенно)
            from dateutil.relativedelta import relativedelta
            next_run = base_datetime + relativedelta(months=interval)
            while next_run <= datetime.now():
                next_run += relativedelta(months=interval)
            
            return next_run
            
    except Exception:
        # В случае ошибки возвращаем None
        return None
    
    return None


def format_next_run_display(next_run: Optional[datetime]) -> str:
    """
    Форматирует следующее обновление для отображения в UI.
    Формат как в облачном варианте.
    """
    if not next_run:
        return "Не запланировано"
    
    now = datetime.now()
    delta = next_run - now
    
    # Если следующее обновление в прошлом
    if delta.total_seconds() < 0:
        return "Просрочено"
    
    # Если сегодня
    if next_run.date() == now.date():
        return f"Сегодня, {next_run.strftime('%H:%M')}"
    
    # Если завтра
    if next_run.date() == now.date() + timedelta(days=1):
        return f"Завтра, {next_run.strftime('%H:%M')}"
    
    # Если послезавтра
    if next_run.date() == now.date() + timedelta(days=2):
        return f"Послезавтра, {next_run.strftime('%H:%M')}"
    
    # Если в течение недели
    if delta.days < 7:
        days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        day_name = days_ru[next_run.weekday()]
        return f"{day_name}, {next_run.strftime('%H:%M')}"
    
    # Если дальше чем через неделю
    return f"{next_run.strftime('%d.%m.%Y, %H:%M')}"


def get_next_run_display_string(
    start_dt: Optional[str],
    end_date: Optional[str],
    recurrence_type: Optional[str],
    recurrence_raw: Optional[str],
    last_run_time: Optional[str] = None
) -> str:
    """Вычисляет и форматирует следующее обновление в одну строку."""
    next_run = calculate_next_run(start_dt, end_date, recurrence_type, recurrence_raw, last_run_time)
    return format_next_run_display(next_run)