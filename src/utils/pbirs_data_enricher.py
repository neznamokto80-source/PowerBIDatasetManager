#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для обогащения данных отчетов PBIRS.
"""

import json
from typing import List, Dict, Any, Optional
from .schedule_parser import extract_refresh_plan_details, format_schedule_for_display
from .next_run_calculator import get_next_run_display_string
from .pbirs_formatter import (
    format_datetime_full,
    compute_next_run,
    parse_recurrence_to_description,
    format_datetime,
    format_date_only
)
from datetime import datetime
import re


def enrich_report_data(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Обогащает данные отчета дополнительной информацией.
    """
    if not report:
        return {}
    
    enriched = report.copy()
    
    # Сохраняем новые поля
    enriched['CreatedBy'] = report.get('CreatedBy', '')
    enriched['CreatedDate'] = report.get('CreatedDate', '')
    enriched['ModifiedBy'] = report.get('ModifiedBy', '')
    enriched['ModifiedDate'] = report.get('ModifiedDate', '')
    
    # Определяем тип отчета
    report_type = report.get('Type', 'Unknown')
    if report_type == 'PowerBIReport':
        enriched['ReportTypeDisplay'] = 'Power BI'
    elif report_type == 'PaginatedReport':
        enriched['ReportTypeDisplay'] = 'Paginated Report'
    elif report_type == 'LinkedReport':
        enriched['ReportTypeDisplay'] = 'Linked Report'
    else:
        enriched['ReportTypeDisplay'] = report_type
    
    # Обрабатываем источники данных
    data_sources = report.get('DataSources', [])
    if isinstance(data_sources, str):
        try:
            data_sources = json.loads(data_sources)
        except:
            data_sources = []
    
    enriched['DataSourcesList'] = data_sources if isinstance(data_sources, list) else []
    
    # Форматируем источники данных для краткого отображения
    if enriched['DataSourcesList']:
        connection_strings = []
        for ds in enriched['DataSourcesList']:
            if ds is None:
                continue
            conn_str = ds.get('ConnectionString', '')
            # Извлекаем Username из вложенного объекта DataModelDataSource
            data_model = ds.get('DataModelDataSource', {})
            if isinstance(data_model, dict):
                username = data_model.get('Username', '')
            else:
                username = ''
            enriched['DataSourcesList'][enriched['DataSourcesList'].index(ds)]['Username'] = username
            if conn_str:
                if ';' in conn_str:
                    conn_str = conn_str.split(';')[0]
                connection_strings.append(conn_str)
        
        if connection_strings:
            unique_conn_strs = []
            for cs in connection_strings:
                if cs not in unique_conn_strs:
                    unique_conn_strs.append(cs)
            
            brief = ', '.join(unique_conn_strs[:3])
            if len(unique_conn_strs) > 3:
                brief += f' и ещё {len(unique_conn_strs) - 3}'
            if len(brief) > 80:
                brief = brief[:77] + '...'
            enriched['DataSourcesBrief'] = brief
        else:
            enriched['DataSourcesBrief'] = 'Нет источников'
    else:
        enriched['DataSourcesBrief'] = 'Нет источников'
    
    # Обрабатываем планы обновления кэша
    refresh_plans = report.get('CacheRefreshPlans', [])
    if isinstance(refresh_plans, str):
        try:
            refresh_plans = json.loads(refresh_plans)
        except:
            refresh_plans = []
    
    enriched['RefreshPlansList'] = refresh_plans if isinstance(refresh_plans, list) else []
    
    # Извлекаем детали расписаний
    enriched_plans = []
    last_status = None
    last_run_time = None
    next_run_display = "Не запланировано"
    
    for plan in enriched['RefreshPlansList']:
        plan_details = extract_refresh_plan_details(plan)
        enriched_plans.append(plan_details)
        
        if plan_details.get('LastRunTime'):
            if not last_run_time or plan_details['LastRunTime'] > last_run_time:
                last_run_time = plan_details['LastRunTime']
                last_status = plan_details.get('LastStatus')
        
        if plan_details.get('RecurrenceType'):
            plan_next_run = get_next_run_display_string(
                plan_details.get('StartDateTime'),
                plan_details.get('EndDate'),
                plan_details.get('RecurrenceType'),
                plan_details.get('RecurrenceRaw'),
                plan_details.get('LastRunTime')
            )
            if plan_next_run != "Не запланировано":
                next_run_display = plan_next_run
    
    enriched['RefreshPlansDetails'] = enriched_plans
    enriched['LastStatus'] = last_status or "Не запускался"
    # Краткое отображение статуса (обрезанный до ~50 символов) — по аналогии с DataSourcesBrief
    last_status_full = enriched['LastStatus']
    if last_status_full and len(last_status_full) > 50:
        enriched['LastStatusBrief'] = last_status_full[:47] + '...'
    else:
        enriched['LastStatusBrief'] = last_status_full
    enriched['LastRunTime'] = last_run_time
    enriched['NextRunDisplay'] = next_run_display
    
    # Новые поля форматирования
    enriched['LastRunDisplayFull'] = format_datetime_full(last_run_time) if last_run_time else "Никогда"
    
    if last_run_time:
        enriched['LastRunDisplay'] = last_run_time
    else:
        enriched['LastRunDisplay'] = "Никогда"
    
    # Добавляем описание расписания для каждого плана обновления и вычисляем следующий запуск
    next_run_candidates = []
    for plan in enriched.get('RefreshPlansList', []):
        schedule_raw = plan.get('Schedule')
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
        
        plan['ScheduleDescription'] = schedule_desc
        
        next_run_str = compute_next_run(recurrence, start_dt, end_dt)
        plan['NextRun'] = next_run_str
        
        next_run_dt = _parse_next_run_datetime(next_run_str)
        if next_run_dt:
            next_run_candidates.append((next_run_dt, next_run_str))
    
    if next_run_candidates:
        next_run_candidates.sort(key=lambda x: x[0])
        next_run_detailed = next_run_candidates[0][1]
    else:
        next_run_detailed = "Не запланировано"
    
    enriched['NextRunDisplayDetailed'] = next_run_detailed
    
    # Форматируем размер
    size_bytes = report.get('Size', 0)
    if size_bytes:
        size_mb = round(size_bytes / (1024 * 1024), 2)
        enriched['SizeDisplay'] = f"{size_mb} МБ"
    else:
        enriched['SizeDisplay'] = "0 МБ"
    
    # Форматируем путь для отображения папки
    path = report.get('Path', '')
    if path:
        if not isinstance(path, str):
            path = str(path)
        if '/' in path:
            folder = '/'.join(path.split('/')[:-1])
            if not folder.startswith('/'):
                folder = '/' + folder
        else:
            folder = '/'
        enriched['FolderDisplay'] = folder
    else:
        enriched['FolderDisplay'] = '/'
    
    return enriched


def _parse_next_run_datetime(next_run_str: str) -> Optional[datetime]:
    """Парсит строку следующего запуска в объект datetime."""
    if not next_run_str or next_run_str in ["не запланирован", "Не запланировано", "завершено",
                                           "не найдено", "нестандартное расписание", "ошибка в дате начала"]:
        return None
    
    pattern = r'(\d{2})\.(\d{2})\.(\d{4})\s+в\s+(\d{2}):(\d{2})'
    match = re.search(pattern, next_run_str)
    if match:
        try:
            day, month, year, hour, minute = map(int, match.groups())
            return datetime(year, month, day, hour, minute)
        except:
            return None
    
    pattern2 = r'(\d{2})\.(\d{2})\.(\d{4}),\s+(\d{2}):(\d{2})'
    match = re.search(pattern2, next_run_str)
    if match:
        try:
            day, month, year, hour, minute = map(int, match.groups())
            return datetime(year, month, day, hour, minute)
        except:
            return None
    
    return None


def enrich_reports_list(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Обогащает список отчетов."""
    return [enrich_report_data(report) for report in reports]


def extract_data_sources_for_table(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Извлекает все источники данных из отчетов для таблицы на вкладке "Источники PBIRS"."""
    sources = []
    for report in reports:
        report_id = report.get('Id', 'Unknown')
        report_name = report.get('Name', 'Без имени')
        report_path = report.get('Path', '')
        folder = report.get('FolderDisplay', '/')
        
        data_sources = report.get('DataSourcesList', [])
        for ds in data_sources:
            if ds is None:
                continue
            source_name = ds.get('Name', 'Без имени')
            connection_string = ds.get('ConnectionString', '')
            data_source_type = ds.get('DataSourceType', 'Unknown')
            created_by = ds.get('CreatedBy', '')
            created_date = ds.get('CreatedDate', '')
            modified_by = ds.get('ModifiedBy', '')
            modified_date = ds.get('ModifiedDate', '')
            # Извлекаем Username из вложенного объекта DataModelDataSource
            data_model = ds.get('DataModelDataSource', {})
            if isinstance(data_model, dict):
                username = data_model.get('Username', '')
            else:
                username = ''
            
            if connection_string and len(connection_string) > 150:
                short_conn = connection_string[:147] + '...'
            else:
                short_conn = connection_string
            
            created_date_formatted = format_datetime(created_date) if created_date else ""
            modified_date_formatted = format_datetime(modified_date) if modified_date else ""
            
            sources.append({
                'ReportId': report_id,
                'ReportName': report_name,
                'ReportPath': report_path,
                'Folder': folder,
                'DataSourceName': source_name,
                'ConnectionString': connection_string,
                'ConnectionStringShort': short_conn,
                'DataSourceType': data_source_type,
                'CreatedBy': created_by,
                'CreatedDate': created_date,
                'CreatedDateFormatted': created_date_formatted,
                'ModifiedBy': modified_by,
                'ModifiedDate': modified_date,
                'ModifiedDateFormatted': modified_date_formatted,
                'Username': username
            })
    return sources


def get_unique_data_source_names(reports: List[Dict[str, Any]]) -> List[str]:
    """Возвращает список уникальных имен источников данных для фильтра."""
    source_names = set()
    for report in reports:
        data_sources = report.get('DataSourcesList', [])
        for ds in data_sources:
            name = ds.get('Name')
            if name:
                source_names.add(name)
    return sorted(list(source_names))