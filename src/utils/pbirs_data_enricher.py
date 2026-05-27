#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для обогащения данных отчетов PBIRS.
"""

import json
from typing import List, Dict, Any, Optional
from .schedule_parser import extract_refresh_plan_details, format_schedule_for_display
from .next_run_calculator import get_next_run_display_string


def enrich_report_data(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Обогащает данные отчета дополнительной информацией.
    
    Args:
        report: Словарь с данными отчета от PBIRS API
    
    Returns:
        Обогащенный словарь с дополнительными полями
    """
    if not report:
        return {}
    
    enriched = report.copy()
    
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
        # Фильтруем None элементы и извлекаем имена
        source_names = []
        for ds in enriched['DataSourcesList']:
            if ds is None:
                continue
            name = ds.get('Name', 'Без имени')
            if name is None:
                name = 'Без имени'
            source_names.append(name)
        if source_names:
            enriched['DataSourcesBrief'] = ', '.join(source_names[:3])  # Первые 3 источника
            if len(source_names) > 3:
                enriched['DataSourcesBrief'] += f' и ещё {len(source_names) - 3}'
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
        
        # Определяем последний статус и время запуска
        if plan_details.get('LastRunTime'):
            if not last_run_time or plan_details['LastRunTime'] > last_run_time:
                last_run_time = plan_details['LastRunTime']
                last_status = plan_details.get('LastStatus')
        
        # Вычисляем следующее обновление для этого плана
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
    enriched['LastRunTime'] = last_run_time
    enriched['NextRunDisplay'] = next_run_display
    
    # Форматируем время последнего запуска
    if last_run_time:
        # Упрощенное форматирование - можно улучшить
        enriched['LastRunDisplay'] = last_run_time
    else:
        enriched['LastRunDisplay'] = "Никогда"
    
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
        # Убедимся, что path - строка
        if not isinstance(path, str):
            path = str(path)
        # Извлекаем папку из пути
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


def enrich_reports_list(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Обогащает список отчетов.
    
    Args:
        reports: Список словарей с данными отчетов
    
    Returns:
        Список обогащенных отчетов
    """
    return [enrich_report_data(report) for report in reports]


def extract_data_sources_for_table(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Извлекает все источники данных из отчетов для таблицы на вкладке "Источники PBIRS".
    
    Args:
        reports: Список обогащенных отчетов
    
    Returns:
        Список словарей с источниками данных
    """
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
            
            # Усекаем ConnectionString для отображения
            if connection_string and len(connection_string) > 100:
                short_conn = connection_string[:100] + '...'
            else:
                short_conn = connection_string
            
            sources.append({
                'ReportId': report_id,
                'ReportName': report_name,
                'ReportPath': report_path,
                'Folder': folder,
                'DataSourceName': source_name,
                'ConnectionString': connection_string,
                'ConnectionStringShort': short_conn
            })
    
    return sources


def get_unique_data_source_names(reports: List[Dict[str, Any]]) -> List[str]:
    """
    Возвращает список уникальных имен источников данных для фильтра.
    
    Args:
        reports: Список обогащенных отчетов
    
    Returns:
        Список уникальных имен источников данных
    """
    source_names = set()
    
    for report in reports:
        data_sources = report.get('DataSourcesList', [])
        for ds in data_sources:
            name = ds.get('Name')
            if name:
                source_names.add(name)
    
    return sorted(list(source_names))