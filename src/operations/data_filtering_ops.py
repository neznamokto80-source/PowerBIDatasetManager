#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Операции фильтрации и мониторинга датасетов.
Объединяет функционал из filtering.py и monitoring.py.
"""

import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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
        """Применяет фильтры к списку датасетов или отчётов PBIRS."""
        # Определяем режим работы
        if self.main_window.current_mode == 'server':
            self._apply_pbirs_filters()
        else:
            self._apply_service_filters()
    
    def _apply_service_filters(self):
        """Применяет фильтры для Power BI Service (облачные датасеты).

        Логика мультивыбора: если выбрано несколько чекбоксов, датасет проходит,
        если соответствует ЛЮБОМУ из выбранных критериев (OR).
        Если ни один чекбокс не выбран — показываются все датасеты.
        Текстовый фильтр по названию работает как AND (дополнительное сужение).
        """
        if not self.main_window.datasets:
            return
        
        # Определяем, какие чекбоксы активны
        checkbox_filters = []
        
        if self.main_window.filter_enabled.isChecked():
            checkbox_filters.append('enabled')
        if self.main_window.filter_recent.isChecked():
            checkbox_filters.append('disabled')
        if self.main_window.filter_errors.isChecked():
            checkbox_filters.append('errors')
        if self.main_window.filter_except_not_use.isChecked():
            checkbox_filters.append('except_not_use')
        if self.main_window.filter_in_progress.isChecked():
            checkbox_filters.append('in_progress')
        
        # Получаем текстовый фильтр по названию (AND)
        name_filter_text = None
        if hasattr(self.main_window, 'dataset_name_filter') and self.main_window.dataset_name_filter:
            name_filter_text = self.main_window.dataset_name_filter.text().strip().lower()
        
        filtered_datasets = []
        
        for ds in self.main_window.datasets:
            # Текстовый фильтр по названию (AND — применяется всегда)
            if name_filter_text:
                dataset_name = ds.get('name', '').lower()
                if name_filter_text not in dataset_name:
                    continue
            
            # Если ни один чекбокс не выбран — показываем все датасеты
            if not checkbox_filters:
                filtered_datasets.append(ds)
                continue
            
            # Мультивыбор (OR): датасет проходит, если соответствует ЛЮБОМУ из выбранных критериев
            match = False
            
            for filter_name in checkbox_filters:
                if filter_name == 'enabled':
                    refresh_schedule = ds.get('refresh_schedule', {})
                    enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None
                    if enabled is True:
                        match = True
                        break
                
                elif filter_name == 'disabled':
                    refresh_schedule = ds.get('refresh_schedule', {})
                    enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None
                    if enabled is False:
                        match = True
                        break
                
                elif filter_name == 'errors':
                    status = ds.get('status', '').lower()
                    if 'failed' in status or 'error' in status:
                        match = True
                        break
                
                elif filter_name == 'except_not_use':
                    name = ds.get('name', '').lower()
                    if 'not_use' not in name:
                        match = True
                        break
                
                elif filter_name == 'in_progress':
                    status = ds.get('status', '').lower()
                    if 'in progress' in status or 'refreshing' in status or 'unknown' in status:
                        match = True
                        break
            
            if match:
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
    
    def _apply_pbirs_filters(self):
        """Применяет PBIRS-фильтры ко всем PBIRS-вкладкам (Отчёты, Источники, Детали).

        Логика мультивыбора: если выбрано несколько чекбоксов, отчёт проходит,
        если соответствует ЛЮБОМУ из выбранных критериев (OR).
        Если ни один чекбокс не выбран — показываются все отчёты (после фильтра по папке).
        Фильтр по папке работает как AND (обязательный).
        """
        if not hasattr(self.main_window, 'pbirs_reports') or not self.main_window.pbirs_reports:
            return
        
        reports = self.main_window.pbirs_reports
        filtered_reports = []
        
        # Определяем выбранную папку для фильтрации
        selected_folder = None
        if hasattr(self.main_window, 'workspace_combo'):
            index = self.main_window.workspace_combo.currentIndex()
            if index >= 0:
                selected_folder = self.main_window.workspace_combo.itemText(index)
        
        # Сначала фильтруем по папке (AND — обязательный фильтр)
        folder_filtered = []
        for report in reports:
            if selected_folder and selected_folder != "Все папки" and selected_folder != '/':
                report_folder = report.get('FolderDisplay', '/')
                # Нормализуем: добавляем ведущий слеш если отсутствует
                if not selected_folder.startswith('/'):
                    selected_folder_norm = '/' + selected_folder
                else:
                    selected_folder_norm = selected_folder
                # Проверяем, начинается ли папка отчёта с выбранной папки (включая подпапки)
                if report_folder == selected_folder_norm or report_folder.startswith(selected_folder_norm + '/'):
                    folder_filtered.append(report)
            else:
                folder_filtered.append(report)
        
        # Определяем, какие чекбоксы активны
        checkbox_filters = []
        
        # Фильтр "Без расписаний"
        if hasattr(self.main_window, 'filter_pbirs_no_schedule') and self.main_window.filter_pbirs_no_schedule.isChecked():
            checkbox_filters.append('no_schedule')
        
        # Фильтр "Без аутентификации"
        if hasattr(self.main_window, 'filter_pbirs_no_auth') and self.main_window.filter_pbirs_no_auth.isChecked():
            checkbox_filters.append('no_auth')
        
        # Фильтр "Успешно обновлённые"
        if hasattr(self.main_window, 'filter_pbirs_success') and self.main_window.filter_pbirs_success.isChecked():
            checkbox_filters.append('success')
        
        # Фильтр "С ошибками последнего обновления"
        if hasattr(self.main_window, 'filter_pbirs_errors') and self.main_window.filter_pbirs_errors.isChecked():
            checkbox_filters.append('errors')
        
        # Фильтр "В процессе обновления"
        if hasattr(self.main_window, 'filter_pbirs_in_progress') and self.main_window.filter_pbirs_in_progress.isChecked():
            checkbox_filters.append('in_progress')
        
        # Если ни один чекбокс не выбран — показываем все отчёты (после фильтра по папке)
        if not checkbox_filters:
            filtered_reports = folder_filtered
        else:
            # Мультивыбор (OR): отчёт проходит, если соответствует ЛЮБОМУ из выбранных критериев
            for report in folder_filtered:
                match = False
                
                for filter_name in checkbox_filters:
                    if filter_name == 'no_schedule':
                        # Отчёт без расписаний — нет CacheRefreshPlans
                        refresh_plans = report.get('RefreshPlansList', [])
                        if not refresh_plans:
                            match = True
                            break
                    
                    elif filter_name == 'no_auth':
                        # Отчёт без аутентификации — у всех источников данных нет Username
                        data_sources = report.get('DataSourcesList', [])
                        all_no_auth = True
                        for ds in data_sources:
                            if ds is None:
                                continue
                            data_model = ds.get('DataModelDataSource', {})
                            if isinstance(data_model, dict):
                                username = data_model.get('Username', '')
                                if username:
                                    all_no_auth = False
                                    break
                        if all_no_auth and data_sources:
                            match = True
                            break
                    
                    elif filter_name == 'success':
                        # Успешно обновлённые
                        last_status = report.get('LastStatus', '').lower()
                        if 'success' in last_status or 'completed' in last_status or 'завершен' in last_status:
                            match = True
                            break
                    
                    elif filter_name == 'errors':
                        # С ошибками последнего обновления
                        last_status = report.get('LastStatus', '').lower()
                        if 'error' in last_status or 'failed' in last_status or 'ошибк' in last_status:
                            match = True
                            break
                    
                    elif filter_name == 'in_progress':
                        # В процессе обновления
                        last_status = report.get('LastStatus', '').lower()
                        if 'refreshing' in last_status:
                            match = True
                            break
                
                if match:
                    filtered_reports.append(report)
        
        # Фильтр "Одинаковое время обновления" (AND — применяется после OR-фильтров)
        if hasattr(self.main_window, 'filter_pbirs_same_time') and self.main_window.filter_pbirs_same_time.isChecked():
            filtered_reports = self._filter_same_time_reports(filtered_reports)
        
        # ===== 1. Обновляем таблицу отчётов PBIRS =====
        if hasattr(self.main_window, 'update_pbirs_reports_table'):
            # Получаем фильтр по названию
            name_filter = None
            if hasattr(self.main_window, 'pbirs_report_name_filter'):
                name_filter = self.main_window.pbirs_report_name_filter.text().strip()
                if not name_filter:
                    name_filter = None
            
            self.main_window.update_pbirs_reports_table(filtered_reports, selected_folder, name_filter)
        
        # ===== 2. Обновляем таблицу источников PBIRS =====
        if hasattr(self.main_window, 'pbirs_sources_data') and hasattr(self.main_window, 'update_pbirs_sources_table'):
            # Фильтруем источники: оставляем только те, что принадлежат отфильтрованным отчётам
            filtered_report_ids = {r.get('Id', '') for r in filtered_reports}
            filtered_sources = [
                s for s in self.main_window.pbirs_sources_data
                if s.get('ReportId', '') in filtered_report_ids
            ]
            
            # Определяем текущие фильтры источников (из UI)
            report_filter = None
            source_filter = None
            kind_filter = None
            user_filter = None
            if hasattr(self.main_window, 'pbirs_sources_report_filter'):
                report_filter = self.main_window.pbirs_sources_report_filter.text()
            if hasattr(self.main_window, 'pbirs_sources_source_filter'):
                index = self.main_window.pbirs_sources_source_filter.currentIndex()
                if index >= 0:
                    source_filter = self.main_window.pbirs_sources_source_filter.currentText()
                    if source_filter == "Все источники":
                        source_filter = None
            if hasattr(self.main_window, 'pbirs_sources_kind_filter'):
                combo = self.main_window.pbirs_sources_kind_filter
                kind_filter = combo.currentText().strip()
                if not kind_filter or kind_filter == "Все типы":
                    kind_filter = None
            if hasattr(self.main_window, 'pbirs_sources_user_filter'):
                combo = self.main_window.pbirs_sources_user_filter
                user_filter = combo.currentText().strip()
                if not user_filter or user_filter == "Все пользователи":
                    user_filter = None
            
            self.main_window.update_pbirs_sources_table(
                filtered_sources, report_filter, source_filter, kind_filter, user_filter
            )
        
        # ===== 3. Обновляем таблицу деталей PBIRS =====
        if hasattr(self.main_window, 'update_pbirs_details_table'):
            name_filter = None
            if hasattr(self.main_window, 'pbirs_details_name_filter'):
                name_filter = self.main_window.pbirs_details_name_filter.text()
            self.main_window.update_pbirs_details_table(filtered_reports, name_filter)
        
        # ===== 4. Обновляем комбобокс выбора отчёта на вкладке "Детали PBIRS" =====
        if hasattr(self.main_window, 'pbirs_operations') and hasattr(self.main_window.pbirs_operations, '_update_pbirs_details_report_combo'):
            self.main_window.pbirs_operations._update_pbirs_details_report_combo(filtered_reports)
        
        # ===== 5. Обновляем статистику PBIRS =====
        if hasattr(self.main_window, 'update_pbirs_stats'):
            self.main_window.update_pbirs_stats(filtered_reports)
        
        self.main_window.log_message(f"Применены PBIRS-фильтры. Показано отчётов: {len(filtered_reports)}")
    
    # ========== Методы мониторинга ==========
    
    def start_monitoring(self):
        """Запускает мониторинг в реальном времени."""
        if self.main_window.auto_refresh_enabled:
            self.main_window.log_message("Мониторинг уже запущен")
            return

        try:
            # Получаем выбранный интервал из UI
            interval = self.main_window.get_monitor_interval()
            self.main_window.update_timer.start(interval)
            self.main_window.auto_refresh_enabled = True

            # Обновляем UI
            self.main_window.start_monitor_btn.setEnabled(False)
            self.main_window.stop_monitor_btn.setEnabled(True)
            self.main_window.status_bar.showMessage("Мониторинг запущен", 3000)
            self.main_window.log_message(f"✓ Мониторинг запущен (интервал: {interval//1000} сек)")

            # Обновляем статус в заголовке группы
            self.main_window._update_monitor_group_title()

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
            self.main_window.status_bar.showMessage("Мониторинг остановлен", 5000)
            self.main_window.log_message("✓ Мониторинг остановлен")

            # Обновляем статус в заголовке группы
            self.main_window._update_monitor_group_title()

        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка остановки мониторинга: {e}")
            self.main_window.status_bar.showMessage("Ошибка остановки мониторинга", 5000)

    @staticmethod
    def _parse_next_run_to_minutes(next_run_str: str) -> Optional[datetime]:
        """
        Парсит строку NextRunDisplay в datetime, округлённый до минут.
        Поддерживает форматы:
        - "Сегодня, HH:MM"
        - "Завтра, HH:MM"
        - "Послезавтра, HH:MM"
        - "ДеньНедели, HH:MM"
        - "DD.MM.YYYY, HH:MM"
        - "DD.MM.YYYY в HH:MM"
        """
        if not next_run_str or next_run_str in ["Не запланировано", "Просрочено"]:
            return None

        now = datetime.now()
        text = next_run_str.strip()

        # Формат "Сегодня, HH:MM"
        m = re.match(r'^Сегодня,\s*(\d{1,2}):(\d{2})$', text)
        if m:
            dt = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
            return dt

        # Формат "Завтра, HH:MM"
        m = re.match(r'^Завтра,\s*(\d{1,2}):(\d{2})$', text)
        if m:
            dt = (now + timedelta(days=1)).replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
            return dt

        # Формат "Послезавтра, HH:MM"
        m = re.match(r'^Послезавтра,\s*(\d{1,2}):(\d{2})$', text)
        if m:
            dt = (now + timedelta(days=2)).replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
            return dt

        # Формат "ДеньНедели, HH:MM" (Понедельник, Вторник, ...)
        days_map = {
            'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3,
            'пятница': 4, 'суббота': 5, 'воскресенье': 6
        }
        m = re.match(r'^(\w+),\s*(\d{1,2}):(\d{2})$', text)
        if m:
            day_name = m.group(1).lower()
            if day_name in days_map:
                target_weekday = days_map[day_name]
                hour = int(m.group(2))
                minute = int(m.group(3))
                # Ищем ближайший день недели вперёд (не сегодня)
                current_weekday = now.weekday()
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:
                    days_ahead += 7
                dt = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                return dt

        # Формат "DD.MM.YYYY, HH:MM" или "DD.MM.YYYY в HH:MM"
        m = re.match(r'(\d{2})\.(\d{2})\.(\d{4})[,\s]+в?\s*(\d{1,2}):(\d{2})', text)
        if m:
            try:
                day, month, year, hour, minute = map(int, m.groups())
                return datetime(year, month, day, hour, minute)
            except:
                return None

        return None

    def _filter_same_time_reports(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрует отчёты: оставляет только те, у которых хотя бы 1 источник данных (ConnectionString)
        совпадает с другим отчётом И время следующего обновления совпадает (с округлением до минут).
        "Не запланировано" не считается совпадением.
        """
        if not reports:
            return []

        # Строим индекс: (ConnectionString, datetime_rounded_to_minutes) -> список отчётов
        index = defaultdict(list)

        for report in reports:
            next_run_str = report.get('NextRunDisplay', '')
            next_run_dt = self._parse_next_run_to_minutes(next_run_str)
            if next_run_dt is None:
                continue

            data_sources = report.get('DataSourcesList', [])
            conn_strings = set()
            for ds in data_sources:
                if ds is None:
                    continue
                conn_str = ds.get('ConnectionString', '')
                if conn_str:
                    # Нормализуем: берём первую часть до точки с запятой
                    if ';' in conn_str:
                        conn_str = conn_str.split(';')[0]
                    conn_strings.add(conn_str)

            if not conn_strings:
                continue

            for conn_str in conn_strings:
                key = (conn_str, next_run_dt)
                index[key].append(report)

        # Собираем отчёты, у которых есть хотя бы один "дубликат" по ключу
        result = []
        seen_ids = set()

        for key, rep_list in index.items():
            if len(rep_list) >= 2:
                for rep in rep_list:
                    rep_id = rep.get('Id', '')
                    if rep_id not in seen_ids:
                        seen_ids.add(rep_id)
                        result.append(rep)

        return result