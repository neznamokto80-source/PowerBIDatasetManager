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
        """Применяет фильтры к списку датасетов или отчётов PBIRS."""
        # Определяем режим работы
        if self.main_window.current_mode == 'server':
            self._apply_pbirs_filters()
        else:
            self._apply_service_filters()
    
    def _apply_service_filters(self):
        """Применяет фильтры для Power BI Service (облачные датасеты)."""
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
    
    def _apply_pbirs_filters(self):
        """Применяет PBIRS-фильтры ко всем PBIRS-вкладкам (Отчёты, Источники, Детали)."""
        if not hasattr(self.main_window, 'pbirs_reports') or not self.main_window.pbirs_reports:
            return
        
        reports = self.main_window.pbirs_reports
        filtered_reports = []
        
        for report in reports:
            include = True
            
            # Фильтр "Без расписаний" — отчёты, у которых нет CacheRefreshPlans
            if hasattr(self.main_window, 'filter_pbirs_no_schedule') and self.main_window.filter_pbirs_no_schedule.isChecked():
                refresh_plans = report.get('RefreshPlansList', [])
                if refresh_plans:
                    include = False
            
            # Фильтр "Без аутентификации" — отчёты, у источников данных которых нет Username
            if include and hasattr(self.main_window, 'filter_pbirs_no_auth') and self.main_window.filter_pbirs_no_auth.isChecked():
                data_sources = report.get('DataSourcesList', [])
                has_auth = False
                for ds in data_sources:
                    if ds is None:
                        continue
                    data_model = ds.get('DataModelDataSource', {})
                    if isinstance(data_model, dict):
                        username = data_model.get('Username', '')
                        if username:
                            has_auth = True
                            break
                if has_auth:
                    include = False
            
            # Фильтр "Успешно обновлённые" — LastStatus содержит "success" или "completed"
            if include and hasattr(self.main_window, 'filter_pbirs_success') and self.main_window.filter_pbirs_success.isChecked():
                last_status = report.get('LastStatus', '').lower()
                if 'success' not in last_status and 'completed' not in last_status and 'завершен' not in last_status:
                    include = False
            
            # Фильтр "С ошибками последнего обновления" — LastStatus содержит "error" или "failed"
            if include and hasattr(self.main_window, 'filter_pbirs_errors') and self.main_window.filter_pbirs_errors.isChecked():
                last_status = report.get('LastStatus', '').lower()
                if 'error' not in last_status and 'failed' not in last_status and 'ошибк' not in last_status:
                    include = False
            
            # Фильтр "В процессе обновления" — LastStatus содержит "refreshing" (статус от PBIRS API)
            if include and hasattr(self.main_window, 'filter_pbirs_in_progress') and self.main_window.filter_pbirs_in_progress.isChecked():
                last_status = report.get('LastStatus', '').lower()
                if 'refreshing' not in last_status:
                    include = False
            
            if include:
                filtered_reports.append(report)
        
        # ===== 1. Обновляем таблицу отчётов PBIRS =====
        if hasattr(self.main_window, 'update_pbirs_reports_table'):
            # Получаем текущую выбранную папку
            selected_folder = None
            if hasattr(self.main_window, 'workspace_combo'):
                index = self.main_window.workspace_combo.currentIndex()
                if index >= 0:
                    selected_folder = self.main_window.workspace_combo.itemText(index)
            
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

            # Обновляем статус
            self.main_window.monitor_status.setText("Мониторинг активен")
            self.main_window.monitor_status.setStyleSheet("color: green; font-weight: bold;")

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

            # Обновляем статус
            self.main_window.monitor_status.setText("Мониторинг не активен")
            self.main_window.monitor_status.setStyleSheet("color: black; font-weight: normal;")

        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка остановки мониторинга: {e}")
            self.main_window.status_bar.showMessage("Ошибка остановки мониторинга", 5000)