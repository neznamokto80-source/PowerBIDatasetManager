#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для разбора расписаний Power BI Report Server.
Адаптировано из предоставленного скрипта.
"""

import json
from typing import Optional, Dict, Any, List


def parse_recurrence(recurrence: Dict[str, Any]) -> Dict[str, Any]:
    """Разбирает Recurrence и возвращает словарь с читаемым описанием и сырыми полями."""
    if not recurrence:
        return {"type": None, "description": "Не указано", "raw": None}
    
    result = {"raw": recurrence}
    
    # MinuteRecurrence (например, {"MinutesInterval": 30})
    minute = recurrence.get("MinuteRecurrence")
    if minute:
        interval = minute.get("MinutesInterval")
        result["type"] = "Minute"
        result["description"] = f"Каждые {interval} минут(ы)"
        result["minutes_interval"] = interval
        return result
    
    # DailyRecurrence (например, {"DaysInterval": 1})
    daily = recurrence.get("DailyRecurrence")
    if daily:
        interval = daily.get("DaysInterval")
        result["type"] = "Daily"
        result["description"] = f"Каждые {interval} день(дней)"
        result["days_interval"] = interval
        return result
    
    # WeeklyRecurrence (например, {"WeeksInterval": 1, "DaysOfWeek": "Monday,Wednesday"})
    weekly = recurrence.get("WeeklyRecurrence")
    if weekly:
        interval = weekly.get("WeeksInterval")
        days = weekly.get("DaysOfWeek")
        # Преобразуем английские названия дней на русские
        days_map = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота",
            "Sunday": "Воскресенье"
        }
        if days:
            # Убедимся, что days - строка
            if not isinstance(days, str):
                days = str(days)
            days_list = [d.strip() for d in days.split(',')]
            days_ru = [days_map.get(day, day) for day in days_list]
            days_str = ', '.join(days_ru)
        else:
            days_str = "не указаны"
        result["type"] = "Weekly"
        result["description"] = f"Каждые {interval} неделю(и) в {days_str}"
        result["weeks_interval"] = interval
        result["days_of_week"] = days
        return result
    
    # MonthlyRecurrence (например, {"MonthsInterval": 1, "DaysOfMonth": "15"})
    monthly = recurrence.get("MonthlyRecurrence")
    if monthly:
        interval = monthly.get("MonthsInterval")
        days = monthly.get("DaysOfMonth")
        # Убедимся, что days - строка
        if days is not None and not isinstance(days, str):
            days = str(days)
        result["type"] = "Monthly"
        result["description"] = f"Каждые {interval} месяц(ев) в день(дни) {days}"
        result["months_interval"] = interval
        result["days_of_month"] = days
        return result
    
    # MonthlyDOWRecurrence (например, {"MonthsInterval": 1, "WeeksOfMonth": "First", "DaysOfWeek": "Monday", "WhichWeekSpecified": true})
    monthly_dow = recurrence.get("MonthlyDOWRecurrence")
    if monthly_dow:
        interval = monthly_dow.get("MonthsInterval")
        week = monthly_dow.get("WeeksOfMonth")
        days = monthly_dow.get("DaysOfWeek")
        # Преобразуем английские названия
        week_map = {
            "First": "первый",
            "Second": "второй",
            "Third": "третий",
            "Fourth": "четвертый",
            "Last": "последний"
        }
        days_map = {
            "Monday": "понедельник",
            "Tuesday": "вторник",
            "Wednesday": "среду",
            "Thursday": "четверг",
            "Friday": "пятницу",
            "Saturday": "субботу",
            "Sunday": "воскресенье"
        }
        # Убедимся, что week и days - строки
        if week is not None and not isinstance(week, str):
            week = str(week)
        if days is not None and not isinstance(days, str):
            days = str(days)
        week_ru = week_map.get(week, week)
        days_ru = days_map.get(days, days)
        result["type"] = "MonthlyDOW"
        result["description"] = f"Каждые {interval} месяц(ев) в {week_ru} {days_ru}"
        result["months_interval"] = interval
        result["week_of_month"] = week
        result["days_of_week"] = days
        return result
    
    result["type"] = "Unknown"
    result["description"] = "Неподдерживаемый тип периодичности"
    return result


def extract_schedule_details(schedule_obj: Optional[Dict]) -> Dict[str, Any]:
    """
    Извлекает из объекта Schedule (если есть) все поля:
    - ScheduleID
    - Definition.StartDateTime
    - Definition.EndDate
    - Definition.Recurrence (разобранный)
    Возвращает словарь с плоскими полями.
    """
    if not schedule_obj or not isinstance(schedule_obj, dict):
        return {
            "ScheduleID": None,
            "StartDateTime": None,
            "EndDate": None,
            "RecurrenceType": None,
            "RecurrenceDescription": None,
            "RecurrenceRaw": None
        }
    
    schedule_id = schedule_obj.get("ScheduleID")
    definition = schedule_obj.get("Definition") or {}
    start_dt = definition.get("StartDateTime")
    end_date = definition.get("EndDate")
    recurrence = definition.get("Recurrence") or {}
    
    parsed = parse_recurrence(recurrence)
    
    return {
        "ScheduleID": schedule_id,
        "StartDateTime": start_dt,
        "EndDate": end_date,
        "RecurrenceType": parsed.get("type"),
        "RecurrenceDescription": parsed.get("description"),
        "RecurrenceRaw": json.dumps(recurrence, ensure_ascii=False) if recurrence else None
    }


def format_schedule_for_display(schedule_details: Dict[str, Any]) -> str:
    """Форматирует детали расписания для отображения в UI."""
    lines = []
    
    if schedule_details.get("RecurrenceDescription"):
        lines.append(f"📅 {schedule_details['RecurrenceDescription']}")
    
    if schedule_details.get("StartDateTime"):
        lines.append(f"📅 Начало: {schedule_details['StartDateTime']}")
    
    if schedule_details.get("EndDate"):
        lines.append(f"📅 Окончание: {schedule_details['EndDate']}")
    
    if schedule_details.get("ScheduleID"):
        lines.append(f"🆔 ID расписания: {schedule_details['ScheduleID']}")
    
    return "\n".join(lines) if lines else "Расписание не настроено"


def extract_refresh_plan_details(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Извлекает и форматирует детали плана обновления кэша."""
    if not plan:
        return {}
    
    # Базовые поля
    result = {
        "Id": plan.get("Id"),
        "Name": plan.get("Name", "Без имени"),
        "Description": plan.get("Description"),
        "LastRunTime": plan.get("LastRunTime"),
        "LastStatus": plan.get("LastStatus"),
    }
    
    # Детали расписания
    schedule_obj = plan.get("Schedule")
    if schedule_obj:
        schedule_details = extract_schedule_details(schedule_obj)
        result.update({
            "ScheduleID": schedule_details["ScheduleID"],
            "StartDateTime": schedule_details["StartDateTime"],
            "EndDate": schedule_details["EndDate"],
            "RecurrenceType": schedule_details["RecurrenceType"],
            "RecurrenceDescription": schedule_details["RecurrenceDescription"],
            "RecurrenceRaw": schedule_details["RecurrenceRaw"],
        })
    
    # История
    history = plan.get("History", [])
    if history and isinstance(history, list):
        # Берем последние 5 записей
        recent_history = history[:5]
        result["RecentHistory"] = recent_history
        result["HistoryCount"] = len(history)
    else:
        result["RecentHistory"] = []
        result["HistoryCount"] = 0
    
    return result