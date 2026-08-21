#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы загрузки данных из Power BI (рабочие области, датасеты, обновление).
"""

import logging
from datetime import datetime, timedelta

from PyQt5.QtWidgets import QTableWidgetItem, QTreeWidgetItem
from PyQt5.QtGui import QBrush

from src.operations.refresh_operations import ProgressManager
from src.operations.base_operations import BaseOperations
from src.ui.theme_colors import ThemeColors
from src.core.data_provider import get_data_provider

logger = logging.getLogger(__name__)


class DataLoadingMethods(BaseOperations):
    """Методы для загрузки данных из Power BI."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы загрузки данных.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        super().__init__(main_window)
        self.progress = ProgressManager(main_window)
    
    # ========== Вспомогательные функции для работы со временем ==========
    # Унаследованы от BaseMethods (_parse_time, _convert_utc_to_local,
    # _convert_schedule_times, _calculate_next_refresh, _format_datetime_for_display)
    
    # ========== ИСПРАВЛЕНИЕ: новый метод для обогащения датасета ==========
    def _enrich_dataset_refresh_info(self, dataset: dict) -> None:
        """
        Обновляет в словаре dataset поля, связанные со следующим обновлением:
        - nextRefreshTime (строка для отображения)
        Модифицирует переданный словарь на месте.
        """
        refresh_schedule = dataset.get('refresh_schedule', {})
        enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None

        # Значение по умолчанию
        next_refresh = dataset.get('nextRefreshTime', 'не запланировано')

        # Если автообновление выключено
        if enabled is False:
            next_refresh = "N/A"
        else:
            # Пытаемся вычислить следующее обновление, если есть времена
            times = refresh_schedule.get('times', []) if isinstance(refresh_schedule, dict) else []
            if enabled is True and times:
                # Конвертируем из UTC+6 в UTC+5 (Екатеринбург)
                from_offset = 6
                to_offset = 5
                schedule_times_local = self._convert_schedule_times(times, from_offset, to_offset)
                current_time = datetime.now()
                next_refresh_dt = self._calculate_next_refresh(schedule_times_local, current_time)
                if next_refresh_dt:
                    next_refresh = self._format_datetime_for_display(next_refresh_dt)
                else:
                    next_refresh = "не запланировано"
            elif enabled is True:
                # Включено, но нет времен → не запланировано
                next_refresh = "не запланировано"

        # Сохраняем обратно
        dataset['nextRefreshTime'] = next_refresh
    
    # ========== Основные методы ==========
    
    def refresh_data(self):
        """Обновление данных для текущего режима (service или server)."""
        # Используем контекстный менеджер для автоматического управления прогресс-баром
        with self.progress.with_progress("Загрузка данных...", indeterminate=True):
            try:
                self.main_window.log_message("Обновление данных...")
                self.main_window.status_bar.showMessage("Обновление данных...")
                
                if self.main_window.current_mode == 'server':
                    # Режим PBIRS (server)
                    if not self.main_window.client:
                        self.main_window.log_message("Не подключено к Power BI Report Server")
                        self.main_window.status_bar.showMessage("Не подключено к PBIRS", 3000)
                        return
                    
                    # Загружаем отчеты PBIRS (внутри load_pbirs_reports уже применяются фильтры)
                    self.main_window.load_pbirs_reports()
                    
                    # Применяем все фильтры (папка + чекбоксы) ко всем PBIRS-вкладкам
                    if hasattr(self.main_window, 'apply_filters'):
                        self.main_window.apply_filters()
                    
                    self.main_window.status_bar.showMessage("Данные PBIRS обновлены", 3000)
                    self.main_window.log_message("✓ Данные PBIRS обновлены")
                    
                else:
                    # Режим Power BI Service (service)
                    if not self.main_window.client or not self.main_window.current_workspace:
                        self.main_window.log_message("Не подключено к Power BI или не выбрана рабочая область")
                        self.main_window.status_bar.showMessage("Не подключено к Power BI", 3000)
                        return
                    
                    # Обновляем список датасетов
                    self.main_window.load_datasets()
                    
                    # Если есть выбранный датасет, обновляем его детали
                    if self.main_window.current_dataset:
                        self.main_window.update_dataset_details(self.main_window.current_dataset)
                    
                    self.main_window.status_bar.showMessage("Данные обновлены", 3000)
                    self.main_window.log_message("✓ Данные обновлены")
                
            except Exception as e:
                self.main_window.log_message(f"✗ Ошибка при обновлении данных: {e}")
                self.main_window.status_bar.showMessage("Ошибка обновления", 5000)
    
    def load_workspaces(self):
        """Загружает список рабочих областей (для service) или папок отчетов (для server)."""
        # Используем контекстный менеджер для автоматического управления прогресс-баром
        with self.progress.with_progress("Загрузка...", indeterminate=True):
            try:
                if self.main_window.current_mode == 'server':
                    self.main_window.log_message("Обновление списка папок отчетов PBIRS...")
                    self.main_window.status_bar.showMessage("Загрузка папок отчетов...")
                    
                    # Если отчеты еще не загружены, загружаем их
                    if not hasattr(self.main_window, 'pbirs_reports') or not self.main_window.pbirs_reports:
                        self.main_window.load_pbirs_reports()
                    
                    # Используем уже извлеченные папки
                    if hasattr(self.main_window, 'pbirs_folders'):
                        folders = self.main_window.pbirs_folders
                    else:
                        # Извлекаем папки из отчетов
                        from src.core.connection_pbirs import PBIRSConnectionMethods
                        extractor = PBIRSConnectionMethods(self.main_window)
                        folders = extractor._extract_folders_from_reports(self.main_window.pbirs_reports)
                        self.main_window.pbirs_folders = folders
                    
                    self.main_window.log_message(f"✓ Загружено папок: {len(folders)}")
                    
                    # Обновление комбобокса с опцией "Все папки"
                    self.main_window.workspace_combo.clear()
                    # Добавляем опцию "Все папки" в начало
                    self.main_window.workspace_combo.addItem("Все папки")
                    if folders:
                        for folder in folders:
                            self.main_window.workspace_combo.addItem(folder)
                        self.main_window.workspace_combo.setCurrentIndex(0)  # Выбираем "Все папки"
                        # Вызываем обработчик выбора папки (пока ничего)
                        # self.main_window.on_workspace_selected(0)
                    else:
                        # Если папок нет, оставляем только "Все папки"
                        pass
                    
                    self.main_window.status_bar.showMessage("Папки отчетов обновлены", 3000)
                    
                else:  # режим service или None
                    self.main_window.log_message("Обновление списка рабочих областей...")
                    self.main_window.status_bar.showMessage("Загрузка рабочих областей...")
                    
                    self.main_window.workspaces = self.main_window.client.get_workspaces()
                    self.main_window.log_message(f"✓ Загружено рабочих областей: {len(self.main_window.workspaces)}")
                    
                    # Обновление комбобокса
                    self.main_window.workspace_combo.clear()
                    if self.main_window.workspaces:
                        for ws in self.main_window.workspaces:
                            name = ws.get('name', 'Без имени')
                            self.main_window.workspace_combo.addItem(name, ws.get('id'))
                    else:
                        self.main_window.workspace_combo.addItem("Нет рабочих областей")
                    
                    # Если есть рабочие области, выбираем первую
                    if self.main_window.workspaces:
                        self.main_window.current_workspace = self.main_window.workspaces[0].get('id')
                        self.main_window.workspace_combo.setCurrentIndex(0)
                        self.main_window.load_datasets()
                    
                    self.main_window.status_bar.showMessage("Рабочие области обновлены", 3000)
                
            except Exception as e:
                self.main_window.log_message(f"✗ Ошибка загрузки: {e}")
                self.main_window.status_bar.showMessage("Ошибка загрузки", 5000)
    
    def load_datasets(self):
        """Загружает датасеты из выбранной рабочей области."""
        if not self.main_window.current_workspace:
            self.main_window.log_message("Не выбрана рабочая область")
            return
        
        # Показываем прогресс-бар в режиме с конкретным процентом (без текста, только процент)
        self.progress.show(None, indeterminate=False)
        try:
            self.main_window.log_message(
                f"Загрузка датасетов из рабочей области {self.main_window.current_workspace}..."
            )
            self.main_window.status_bar.showMessage("Загрузка датасетов...")
            
            # Определяем callback для обновления прогресса
            def update_progress(current, total, message):
                if total > 0:
                    percent = int(current / total * 100)
                else:
                    percent = 0
                # Обновляем прогресс-бар (без текста, только процент)
                self.progress.update(percent, 100, None)
                # Обновляем статус-бар
                self.main_window.status_bar.showMessage(f"Загрузка: {percent}%")
                # Принудительно обрабатываем события UI
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
            
            # Используем integration для получения обогащенных данных с отслеживанием прогресса
            if self.main_window.integration:
                datasets = self.main_window.integration.get_dataset_list(
                    self.main_window.current_workspace,
                    progress_callback=update_progress
                )
            else:
                datasets = self.main_window.client.get_datasets_in_workspace(self.main_window.current_workspace)
            
            # ========== ИСПРАВЛЕНИЕ: обогащаем каждый датасет актуальным nextRefreshTime ==========
            for ds in datasets:
                self._enrich_dataset_refresh_info(ds)
            
            self.main_window.datasets = datasets
            self.main_window.log_message(f"✓ Загружено датасетов: {len(datasets)}")
            
            # Обновление статистики (по всем датасетам)
            self.update_stats(datasets)
            
            # Применяем текущие фильтры для обновления таблицы и дерева
            self.main_window.apply_filters()
            
            self.main_window.status_bar.showMessage("Датасеты загружены", 3000)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка загрузки датасетов: {e}")
            self.main_window.status_bar.showMessage("Ошибка загрузки", 5000)
        finally:
            self.progress.hide()   # скрываем прогресс-бар после завершения
    
    def load_test_data(self):
        """Загружает тестовые данные (демо-режим) для скриншотов."""
        try:
            self.main_window.log_message("Загрузка тестовых данных (демо-режим)...")
            self.main_window.status_bar.showMessage("Загрузка тестовых данных...")
            
            # Создаем провайдер данных в демо-режиме
            provider = get_data_provider(demo_mode=True)
            
            # Используем фиктивную рабочую область (или текущую, если есть)
            workspace = self.main_window.current_workspace or "DefaultWorkspace"
            
            # Получаем демо-датасеты
            datasets = provider.get_datasets_for_workspace(workspace, force_refresh=False)
            
            # Обогащаем каждый датасет информацией о следующем обновлении
            for ds in datasets:
                self._enrich_dataset_refresh_info(ds)
            
            self.main_window.datasets = datasets
            self.main_window.log_message(f"✓ Загружено тестовых датасетов: {len(datasets)}")
            
            # Обновление статистики (по всем датасетам)
            self.update_stats(datasets)
            
            # Применяем текущие фильтры для обновления таблицы и дерева
            self.main_window.apply_filters()
            
            self.main_window.status_bar.showMessage("Тестовые данные загружены", 3000)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка загрузки тестовых данных: {e}")
            self.main_window.status_bar.showMessage("Ошибка загрузки тестовых данных", 5000)
    
    def update_dataset_table(self, datasets):
        """Обновляет таблицу датасетов."""
        self.main_window.dataset_table.setRowCount(len(datasets))
        for row, ds in enumerate(datasets):
            name = ds.get('name', 'Без имени')
            # Получаем ID рабочей области из разных возможных ключей
            workspace_id = ds.get('workspaceId') or ds.get('workspace_id', '')
            workspace = self.main_window.get_workspace_name(workspace_id)
            dataset_id = ds.get('id', '') or ds.get('datasetId', '')
            status = ds.get('status', 'unknown')
            # Преобразуем статус "unknown" в "в процессе обновления" для отображения
            if status.lower() == 'unknown':
                status = 'в процессе обновления'
            last_refresh = ds.get('lastRefreshTime', 'никогда')
            # ========== ИСПРАВЛЕНИЕ: теперь nextRefreshTime уже обогащён ==========
            next_refresh = ds.get('nextRefreshTime', 'не запланировано')
            
            # Определяем статус автоматического обновления
            auto_refresh_status = "Неизвестно"
            refresh_schedule = ds.get('refresh_schedule', {})
            enabled = None
            if isinstance(refresh_schedule, dict):
                enabled = refresh_schedule.get('enabled')
                if enabled is True:
                    auto_refresh_status = "Включено"
                elif enabled is False:
                    auto_refresh_status = "Выключено"
                elif 'days' in refresh_schedule or 'times' in refresh_schedule:
                    auto_refresh_status = "Настроено"
            
            self.main_window.dataset_table.setItem(row, 0, QTableWidgetItem(name))
            self.main_window.dataset_table.setItem(row, 1, QTableWidgetItem(workspace))
            self.main_window.dataset_table.setItem(row, 2, QTableWidgetItem(dataset_id))
            self.main_window.dataset_table.setItem(row, 3, QTableWidgetItem(status))
            self.main_window.dataset_table.setItem(row, 4, QTableWidgetItem(last_refresh))
            self.main_window.dataset_table.setItem(row, 5, QTableWidgetItem(next_refresh))
            self.main_window.dataset_table.setItem(row, 6, QTableWidgetItem(auto_refresh_status))
            
            # Цветовое выделение строк - используем общую логику определения цвета
            background_color = ThemeColors.get_dataset_background_color(ds, self.main_window.current_theme)
            
            if background_color:
                brush = QBrush(background_color)
                for col in range(self.main_window.dataset_table.columnCount()):
                    item = self.main_window.dataset_table.item(row, col)
                    if item:
                        item.setBackground(brush)
        
        # Обновляем комбобокс выбора датасета на вкладке детали
        self.main_window.update_details_dataset_combo(datasets)
    
    def update_stats(self, datasets):
        """Обновляет статистику."""
        total = len(datasets)
        # Считаем датасеты с включенным автообновлением (refresh_schedule.enabled == True)
        enabled = 0
        for ds in datasets:
            refresh_schedule = ds.get('refresh_schedule', {})
            if isinstance(refresh_schedule, dict) and refresh_schedule.get('enabled') is True:
                enabled += 1
        failed = sum(1 for ds in datasets if ds.get('status', '').lower() == 'failed')
        
        # Время получения данных (текущее время)
        last_update = self._format_datetime_for_display(datetime.now())
        
        self.main_window.total_datasets_label.setText(f"Всего датасетов: {total}")
        self.main_window.enabled_refresh_label.setText(f"С обновлением: {enabled}")
        self.main_window.failed_refresh_label.setText(f"С ошибками: {failed}")
        self.main_window.last_update_label.setText(f"Последнее обновление: {last_update}")
    
    def get_workspace_name(self, workspace_id):
        """Возвращает имя рабочей области по ID."""
        for ws in self.main_window.workspaces:
            if ws.get('id') == workspace_id:
                return ws.get('name', 'Без имени')
        return workspace_id
    
    def get_schedule_display_for_dataset(self, dataset):
        """
        Обновляет nextRefreshTime в dataset и возвращает строки для блока расписания.

        Returns:
            Кортеж (schedule_text, auto_refresh_status, next_refresh, enabled).
        """
        self._enrich_dataset_refresh_info(dataset)
        next_refresh = dataset.get('nextRefreshTime', 'не запланировано')

        refresh_schedule = dataset.get('refresh_schedule', {})
        schedule_text = 'не настроено'
        auto_refresh_status = 'Неизвестно'
        enabled = None
        schedule_times_local = []

        if isinstance(refresh_schedule, dict) and refresh_schedule:
            enabled = refresh_schedule.get('enabled')
            if enabled is True:
                auto_refresh_status = 'Включено'
            elif enabled is False:
                auto_refresh_status = 'Выключено'
            else:
                auto_refresh_status = 'Настроено (статус неизвестен)'

            days = refresh_schedule.get('days', [])
            times = refresh_schedule.get('times', [])
            timezone = refresh_schedule.get('localTimeZoneId', '')

            if days and times:
                days_str = ', '.join(days) if isinstance(days, list) else str(days)
                times_str = ', '.join(times) if isinstance(times, list) else str(times)
                schedule_text = f'Дни: {days_str}\nВремя: {times_str}'
                if timezone:
                    schedule_text += f'\nЧасовой пояс: {timezone}'
                if enabled is not None:
                    schedule_text += f'\nСтатус: {"Включено" if enabled else "Выключено"}'

                from_offset = 6
                to_offset = 5
                schedule_times_local = self._convert_schedule_times(times, from_offset, to_offset)
                schedule_text += f'\nВремя (Екатеринбург): {", ".join(schedule_times_local)}'
            else:
                schedule_text = 'расписание не настроено'
        else:
            auto_refresh_status = 'Не настроено'

        if enabled is False:
            next_refresh = "N/A"
        elif enabled is True and schedule_times_local and next_refresh in ('не запланировано', ''):
            current_time = datetime.now()
            next_refresh_dt = self._calculate_next_refresh(schedule_times_local, current_time)
            if next_refresh_dt:
                next_refresh = self._format_datetime_for_display(next_refresh_dt)

        return schedule_text, auto_refresh_status, next_refresh, enabled

    def update_dataset_details(self, dataset):
        """Обновляет детальную информацию о выбранном датасете."""
        if not dataset:
            return
        
        name = dataset.get('name', 'Без имени')
        dataset_id = dataset.get('id', 'N/A')
        workspace_id = dataset.get('workspaceId') or dataset.get('workspace_id', '')
        workspace_name = self.main_window.get_workspace_name(workspace_id)
        status = dataset.get('status', 'unknown')
        # Преобразуем статус "unknown" в "в процессе обновления" для отображения
        if status.lower() == 'unknown':
            status = 'в процессе обновления'
        last_refresh = dataset.get('lastRefreshTime', 'никогда')
        schedule_text, auto_refresh_status, next_refresh, enabled = (
            self.get_schedule_display_for_dataset(dataset)
        )
        
        # Получаем информацию о последнем обновлении
        last_refresh_info = dataset.get('last_refresh', {})
        last_refresh_details = 'нет данных'
        if isinstance(last_refresh_info, dict) and last_refresh_info:
            end_time = last_refresh_info.get('endTime', '')
            refresh_status = last_refresh_info.get('status', '')
            refresh_type = last_refresh_info.get('refreshType', '')
            
            details_parts = []
            if end_time:
                # Конвертируем endTime из UTC в локальное время (Екатеринбург UTC+5)
                try:
                    # Парсим ISO строку
                    from datetime import datetime as dt
                    utc_dt = dt.fromisoformat(end_time.replace('Z', '+00:00'))
                    # Добавляем 5 часов (UTC+5)
                    local_dt = utc_dt + timedelta(hours=5)
                    # Округляем до минут
                    local_dt_rounded = local_dt.replace(second=0, microsecond=0)
                    formatted = local_dt_rounded.strftime('%d.%m.%Y, %H:%M')
                    details_parts.append(f'Время: {formatted} (Екатеринбург)')
                    # Обновляем last_refresh для отображения в основном поле
                    last_refresh = formatted
                except Exception:
                    details_parts.append(f'Время: {end_time}')
            if refresh_status:
                details_parts.append(f'Статус: {refresh_status}')
            if refresh_type:
                details_parts.append(f'Тип: {refresh_type}')
            
            if details_parts:
                last_refresh_details = '; '.join(details_parts)
        
        # Обновляем поля деталей
        self.main_window.detail_name.setText(name)
        self.main_window.detail_id.setText(dataset_id)
        self.main_window.detail_workspace.setText(workspace_name)
        self.main_window.detail_refresh_status.setText(status)
        self.main_window.detail_last_refresh.setText(last_refresh)
        self.main_window.detail_next_refresh.setText(next_refresh)
        self.main_window.detail_schedule.setText(schedule_text)
        
        # Добавляем информацию о статусе автоматического обновления
        # Создаем или используем существующие поля, если они есть
        if hasattr(self.main_window, 'detail_auto_refresh'):
            self.main_window.detail_auto_refresh.setText(auto_refresh_status)
        
        # Добавляем информацию о последнем обновлении (детали)
        if hasattr(self.main_window, 'detail_last_refresh_details'):
            self.main_window.detail_last_refresh_details.setText(last_refresh_details)
        
        # Обновляем статус кнопок в зависимости от состояния автообновления
        # enabled может быть True (включено), False (выключено), None (не настроено)
        if enabled is True:
            # Автообновление включено - кнопка "Включить" неактивна, "Выключить" активна
            self.main_window.enable_btn.setEnabled(False)
            self.main_window.disable_btn.setEnabled(True)
        else:
            # Автообновление выключено или не настроено - кнопка "Включить" активна, "Выключить" неактивна
            self.main_window.enable_btn.setEnabled(True)
            self.main_window.disable_btn.setEnabled(False)
        
        # Кнопка ручного обновления активна, если датасет поддерживает обновление
        is_refreshable = dataset.get('isRefreshable', False)
        self.main_window.manual_refresh_btn.setEnabled(is_refreshable)
        if hasattr(self.main_window, 'edit_schedule_btn'):
            self.main_window.edit_schedule_btn.setEnabled(True)
        
        # Загружаем расписание в UI элементы управления (если они существуют)
        refresh_schedule = dataset.get('refresh_schedule', {})
        if hasattr(self.main_window, 'load_schedule_to_ui'):
            self.main_window.load_schedule_to_ui(refresh_schedule)