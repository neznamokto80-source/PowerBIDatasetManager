#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для форматирования данных PBIRS в соответствии с предоставленным скриптом.
Содержит функции для форматирования дат, описания расписаний и вычисления следующего запуска.
"""

import json
from datetime import datetime, timedelta
import calendar
from typing import Dict, Any, List, Optional


def format_datetime(dt_str: Optional[str]) -> str:
    """ДД.ММ.ГГГГ ЧЧ:ММ:СС"""
    if not dt_str or not isinstance(dt_str, str):
        return ""
    try:
        # Обработка формата ISO с Z или без
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    except:
        return dt_str


def format_date_only(dt_str: Optional[str]) -> str:
    if not dt_str or not isinstance(dt_str, str):
        return ""
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y")
    except:
        return dt_str


def format_time_from_datetime(dt_str: Optional[str]) -> str:
    if not dt_str or not isinstance(dt_str, str):
        return ""
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%H:%M")
    except:
        return ""


def format_datetime_full(dt_str: Optional[str]) -> str:
    """27 мая 2026 г. 9:35:55"""
    if not dt_str or not isinstance(dt_str, str):
        return ""
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        return f"{dt.day} {months[dt.month-1]} {dt.year} г. {dt.hour}:{dt.minute:02d}:{dt.second:02d}"
    except:
        return dt_str


# --------------------- Парсинг рекурренции и описание ---------------------
def get_days_of_week_from_obj(days_obj: Optional[Dict]) -> List[str]:
    if not days_obj or not isinstance(days_obj, dict):
        return []
    mapping = {"Sunday": "Вс", "Monday": "Пн", "Tuesday": "Вт", "Wednesday": "Ср",
               "Thursday": "Чт", "Friday": "Пт", "Saturday": "Сб"}
    return [ru for eng, ru in mapping.items() if days_obj.get(eng) is True]


def get_months_from_obj(months_obj: Optional[Dict]) -> List[str]:
    if not months_obj or not isinstance(months_obj, dict):
        return []
    mapping = {"January": "Январь", "February": "Февраль", "March": "Март", "April": "Апрель",
               "May": "Май", "June": "Июнь", "July": "Июль", "August": "Август",
               "September": "Сентябрь", "October": "Октябрь", "November": "Ноябрь", "December": "Декабрь"}
    return [ru for eng, ru in mapping.items() if months_obj.get(eng) is True]


def translate_which_week(week_str: str) -> str:
    mapping = {"FirstWeek": "первую", "SecondWeek": "вторую", "ThirdWeek": "третью",
               "FourthWeek": "четвертую", "LastWeek": "последнюю"}
    return mapping.get(week_str, week_str)


def parse_recurrence_to_description(recurrence: Optional[Dict], start_time_str: Optional[str]) -> str:
    if not recurrence or not isinstance(recurrence, dict):
        return "Расписание не задано"
    time_part = f"в {format_time_from_datetime(start_time_str)}" if start_time_str else ""

    # Daily
    daily = recurrence.get("DailyRecurrence")
    if daily and isinstance(daily, dict):
        interval = daily.get("DaysInterval", 1)
        freq = "Ежедневно" if interval == 1 else f"Каждые {interval} дней"
        return f"{freq} {time_part}".strip()
    # Weekly
    weekly = recurrence.get("WeeklyRecurrence")
    if weekly and isinstance(weekly, dict):
        interval = weekly.get("WeeksInterval", 1)
        days_list = get_days_of_week_from_obj(weekly.get("DaysOfWeek"))
        days_str = "; ".join(days_list) if days_list else "не указаны"
        if interval == 1:
            freq = f"каждый {days_str} каждой недели"
        else:
            freq = f"каждый {days_str} каждые {interval} недель"
        return f"На {time_part} {freq}".strip()
    # MonthlyDOW
    monthly_dow = recurrence.get("MonthlyDOWRecurrence")
    if monthly_dow and isinstance(monthly_dow, dict):
        week_ru = translate_which_week(monthly_dow.get("WhichWeek", ""))
        days_list = get_days_of_week_from_obj(monthly_dow.get("DaysOfWeek"))
        days_str = "; ".join(days_list) if days_list else "не указаны"
        months_list = get_months_from_obj(monthly_dow.get("MonthsOfYear"))
        months_str = ", ".join(months_list) if months_list else ""
        if months_str:
            freq = f"в {week_ru} {days_str} из {months_str}"
        else:
            freq = f"в {week_ru} {days_str}"
        return f"На {time_part} {freq}".strip()
    # Monthly (по числам)
    monthly = recurrence.get("MonthlyRecurrence")
    if monthly and isinstance(monthly, dict):
        interval = monthly.get("MonthsInterval", 1)
        days_of_month = monthly.get("DaysOfMonth", "")
        if interval == 1:
            freq = f"ежемесячно {days_of_month}-го числа"
        else:
            freq = f"каждые {interval} месяцев, {days_of_month}-го числа"
        return f"{freq} {time_part}".strip()
    # Minute
    minute = recurrence.get("MinuteRecurrence")
    if minute and isinstance(minute, dict):
        interval = minute.get("MinutesInterval", 1)
        freq = "Каждую минуту" if interval == 1 else f"Каждые {interval} минут"
        return f"{freq} {time_part}".strip()
    return "Нестандартное расписание"


# --------------------- Расчёт следующего запуска ---------------------
def parse_iso_to_naive(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        if '+' in dt_str:
            dt_str = dt_str.split('+')[0]
        elif dt_str.endswith('Z'):
            dt_str = dt_str[:-1]
        return datetime.fromisoformat(dt_str)
    except:
        return None


def get_next_weekday(base_date: datetime, target_weekday: int) -> datetime:
    days_ahead = target_weekday - base_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return base_date + timedelta(days=days_ahead)


def get_date_for_weekday_in_month(year: int, month: int, week_num: int, weekdays: List[int]):
    """
    week_num: 1..5 (5 = последняя неделя)
    weekdays: список int (0=пн..6=вс)
    Возвращает date
    """
    first_day = datetime(year, month, 1)
    first_weekday = first_day.weekday()
    if week_num == 5:  # последняя неделя
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])
        last_weekday = last_day.weekday()
        candidates = []
        for wd in weekdays:
            diff = (wd - last_weekday) % 7
            candidate = last_day - timedelta(days=7 - diff) if diff != 0 else last_day
            if candidate.month == month:
                candidates.append(candidate)
        return min(candidates).date() if candidates else None
    else:
        first_monday = first_day + timedelta(days=(7 - first_weekday) % 7)
        week_start = first_monday + timedelta(days=7 * (week_num - 1))
        candidates = []
        for wd in weekdays:
            candidate = week_start + timedelta(days=wd)
            if candidate.month == month:
                candidates.append(candidate)
        return min(candidates).date() if candidates else None


def compute_next_run(recurrence: Optional[Dict], start_dt_str: Optional[str], end_dt_str: Optional[str]) -> str:
    if not recurrence or not start_dt_str:
        return "не запланирован"
    start = parse_iso_to_naive(start_dt_str)
    if start is None:
        return "ошибка в дате начала"
    end = parse_iso_to_naive(end_dt_str) if end_dt_str and end_dt_str != "0001-01-01T00:00:00Z" else None
    current_dt = datetime.now()
    if start > current_dt:
        return start.strftime("%d.%m.%Y в %H:%M")
    run_hour, run_minute = start.hour, start.minute

    # 1. DailyRecurrence
    daily = recurrence.get("DailyRecurrence")
    if daily and isinstance(daily, dict):
        interval = daily.get("DaysInterval", 1)
        current_date = current_dt.date()
        start_date = start.date()
        delta = (current_date - start_date).days
        if delta < 0:
            days_to_add = 0
        else:
            remainder = delta % interval
            if remainder == 0 and current_dt.time() <= datetime.min.time().replace(hour=run_hour, minute=run_minute):
                days_to_add = 0
            else:
                days_to_add = interval - remainder
        next_date = start_date + timedelta(days=delta + days_to_add)
        if end and next_date > end.date():
            return "завершено (после даты окончания)"
        next_dt = datetime.combine(next_date, datetime.min.time().replace(hour=run_hour, minute=run_minute))
        if next_dt < current_dt:
            next_dt += timedelta(days=interval)
        return next_dt.strftime("%d.%m.%Y в %H:%M")

    # 2. WeeklyRecurrence
    weekly = recurrence.get("WeeklyRecurrence")
    if weekly and isinstance(weekly, dict):
        interval = weekly.get("WeeksInterval", 1)
        days_obj = weekly.get("DaysOfWeek")
        day_mapping = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                       "Friday": 4, "Saturday": 5, "Sunday": 6}
        weekdays = [idx for eng, idx in day_mapping.items() if days_obj.get(eng) is True]
        if not weekdays:
            return "не заданы дни недели"
        current_date = current_dt.date()
        start_date = start.date()
        # Поиск следующего запуска
        for _ in range(200):
            for wd in sorted(weekdays):
                next_date = get_next_weekday(datetime.combine(current_date, datetime.min.time()), wd).date()
                week_diff = (next_date - start_date).days // 7
                if week_diff % interval == 0:
                    next_dt = datetime.combine(next_date, datetime.min.time().replace(hour=run_hour, minute=run_minute))
                    if next_dt >= current_dt:
                        if end and next_date > end.date():
                            return "завершено"
                        return next_dt.strftime("%d.%m.%Y в %H:%M")
            current_date += timedelta(days=7)
        return "не найдено"

    # 3. MonthlyDOWRecurrence
    monthly_dow = recurrence.get("MonthlyDOWRecurrence")
    if monthly_dow and isinstance(monthly_dow, dict):
        week_map = {"FirstWeek": 1, "SecondWeek": 2, "ThirdWeek": 3, "FourthWeek": 4, "LastWeek": 5}
        target_week = week_map.get(monthly_dow.get("WhichWeek", ""), 1)
        days_obj = monthly_dow.get("DaysOfWeek")
        day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
        weekdays = [idx for eng, idx in day_map.items() if days_obj.get(eng) is True]
        months_obj = monthly_dow.get("MonthsOfYear")
        months = []
        month_map = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                     "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
        if months_obj:
            for eng, num in month_map.items():
                if months_obj.get(eng) is True:
                    months.append(num)
        if not months:
            months = list(range(1, 13))
        current_date = current_dt.date()
        start_date = start.date()
        for year_offset in range(5):
            year = current_date.year + year_offset
            for month in sorted(months):
                if year == current_date.year and month < current_date.month:
                    continue
                candidate = get_date_for_weekday_in_month(year, month, target_week, weekdays)
                if candidate:
                    if candidate < start_date:
                        continue
                    if candidate >= current_date:
                        next_dt = datetime.combine(candidate, datetime.min.time().replace(hour=run_hour, minute=run_minute))
                        if end and candidate > end.date():
                            return "завершено"
                        if next_dt < start:
                            continue
                        return next_dt.strftime("%d.%m.%Y в %H:%M")
        return "не найдено"

    # 4. MonthlyRecurrence (по числам)
    monthly = recurrence.get("MonthlyRecurrence")
    if monthly and isinstance(monthly, dict):
        interval = monthly.get("MonthsInterval", 1)
        days_str = monthly.get("DaysOfMonth", "")
        day_list = []
        for part in days_str.split(','):
            if part.strip().isdigit():
                day_list.append(int(part.strip()))
        if not day_list:
            return "не заданы дни месяца"
        start_date = start.date()
        current_date = current_dt.date()
        for _ in range(200):
            for month_offset in range(0, interval * 12 + 1, interval):
                year = current_date.year
                month = current_date.month + month_offset
                while month > 12:
                    month -= 12
                    year += 1
                for day in sorted(day_list):
                    try:
                        candidate = datetime(year, month, day).date()
                    except ValueError:
                        continue
                    if candidate < start_date:
                        continue
                    if candidate >= current_date:
                        months_diff = (candidate.year - start_date.year) * 12 + (candidate.month - start_date.month)
                        if months_diff % interval == 0:
                            next_dt = datetime.combine(candidate, datetime.min.time().replace(hour=run_hour, minute=run_minute))
                            if end and candidate > end.date():
                                return "завершено"
                            return next_dt.strftime("%d.%m.%Y в %H:%M")
            # переходим к следующему году
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        return "не найдено"

    # 5. MinuteRecurrence
    minute = recurrence.get("MinuteRecurrence")
    if minute and isinstance(minute, dict):
        interval = minute.get("MinutesInterval", 1)
        delta_minutes = (current_dt - start).total_seconds() // 60
        if delta_minutes < 0:
            return start.strftime("%d.%m.%Y в %H:%M")
        else:
            cycles = (delta_minutes // interval) + 1
            next_run = start + timedelta(minutes=cycles * interval)
            if end and next_run > end:
                return "завершено"
            return next_run.strftime("%d.%m.%Y в %H:%M")
    return "нестандартное расписание"


def format_report_details(report: Dict[str, Any]) -> str:
    """
    Форматирует детали отчёта в строку в соответствии с требуемым форматом.
    
    Возвращает:
        Строка с отформатированными данными отчёта
    """
    report_id = report.get("Id", "Unknown")
    report_name = report.get("Name", "Unknown")
    report_path = report.get("Path", "Unknown")
    created_by = report.get("CreatedBy", "Unknown")
    created_date = format_datetime(report.get("CreatedDate"))
    modified_date = format_datetime(report.get("ModifiedDate"))
    modified_by = report.get("ModifiedBy", "Unknown")
    
    lines = []
    lines.append(f"📊 PowerBIReport: {report_name} (ID: {report_id})")
    lines.append(f"   Путь: {report_path}")
    lines.append(f"   Создатель: {created_by} ({created_date})")
    if modified_date:
        lines.append(f"   Изменён: {modified_by} ({modified_date})")
    
    # DataSources
    data_sources = report.get("DataSources", [])
    if not isinstance(data_sources, list):
        if isinstance(data_sources, str):
            try:
                data_sources = json.loads(data_sources)
            except:
                data_sources = []
        else:
            data_sources = []
    
    if data_sources:
        lines.append("\n   🔗 Источники данных:")
        for ds in data_sources:
            conn_str = ds.get("ConnectionString", "N/A")
            ds_created = format_datetime(ds.get("CreatedDate"))
            ds_modified = format_datetime(ds.get("ModifiedDate"))
            lines.append(f"      • {conn_str}")
            if ds_created:
                lines.append(f"        Создан: {ds.get('CreatedBy', '?')} ({ds_created})")
            if ds_modified:
                lines.append(f"        Изменён: {ds.get('ModifiedBy', '?')} ({ds_modified})")
    
    # CacheRefreshPlans
    refresh_plans = report.get("CacheRefreshPlans", [])
    if not isinstance(refresh_plans, list):
        if isinstance(refresh_plans, str):
            try:
                refresh_plans = json.loads(refresh_plans)
            except:
                refresh_plans = []
        else:
            refresh_plans = []
    
    if refresh_plans:
        lines.append("\n   🔄 Расписания обновления кэша:")
        for plan in refresh_plans:
            plan_name = plan.get("Description") or plan.get("Name", "Без названия")
            
            # Получаем расписание
            schedule_raw = plan.get("Schedule")
            schedule_dict = {}
            if schedule_raw is not None:
                if isinstance(schedule_raw, str):
                    try:
                        schedule_dict = json.loads(schedule_raw)
                    except:
                        schedule_dict = {}
                elif isinstance(schedule_raw, dict):
                    schedule_dict = schedule_raw
            
            definition = schedule_dict.get("Definition") if isinstance(schedule_dict.get("Definition"), dict) else {}
            start_dt = definition.get("StartDateTime") if definition else None
            end_dt = definition.get("EndDate") if definition else None
            recurrence = definition.get("Recurrence") if definition else {}
            if recurrence and isinstance(recurrence, str):
                try:
                    recurrence = json.loads(recurrence)
                except:
                    recurrence = {}
            
            schedule_desc = parse_recurrence_to_description(recurrence, start_dt)
            if start_dt and "начиная с" not in schedule_desc:
                date_start = format_date_only(start_dt)
                if date_start:
                    schedule_desc += f" начиная с {date_start}"
            
            last_run = format_datetime_full(plan.get("LastRunTime")) if plan.get("LastRunTime") else None
            last_status = plan.get("LastStatus", "")
            next_run = compute_next_run(recurrence, start_dt, end_dt)
            
            lines.append(f"      • {plan_name}")
            lines.append(f"        {schedule_desc}")
            lines.append(f"        Последний запуск: {last_run}")
            lines.append(f"        Статус: {last_status}")
            lines.append(f"        Следующий запуск: {next_run}")
    else:
        lines.append("\n   🔄 Расписания обновления: отсутствуют")
    
    return "\n".join(lines)