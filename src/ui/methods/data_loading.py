#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы загрузки данных из Power BI (рабочие области, датасеты, обновление).
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import QTableWidgetItem, QTreeWidgetItem
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QBrush, QColor

from .progress_manager import ProgressManager

logger = logging.getLogger(__name__)


class DataLoadingMethods:
    """Методы для загрузки данных из Power BI."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы загрузки данных.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
        self.progress = ProgressManager(main_window)
    
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
    
    # ========== Основные методы ==========
    
    def refresh_data(self):
        """Обновление данных."""
        if not self.main_window.client or not self.main_window.current_workspace:
            self.main_window.log_message("Не подключено к Power BI или не выбрана рабочая область")
            return
        
        # Используем контекстный менеджер для автоматического управления прогресс-баром
        with self.progress.with_progress("Загрузка данных...", indeterminate=True):
            try:
                self.main_window.log_message("Обновление данных...")
                self.main_window.status_bar.showMessage("Обновление данных...")
                
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
        """Загружает список рабочих областей из Power BI."""
        # Используем контекстный менеджер для автоматического управления прогресс-баром
        with self.progress.with_progress("Загрузка рабочих областей...", indeterminate=True):
            try:
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
                self.main_window.log_message(f"✗ Ошибка загрузки рабочих областей: {e}")
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
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
            
            # Используем integration для получения обогащенных данных с отслеживанием прогресса
            if self.main_window.integration:
                datasets = self.main_window.integration.get_dataset_list(
                    self.main_window.current_workspace,
                    progress_callback=update_progress
                )
            else:
                datasets = self.main_window.client.get_datasets_in_workspace(self.main_window.current_workspace)
            
            self.main_window.datasets = datasets
            self.main_window.log_message(f"✓ Загружено датасетов: {len(datasets)}")
            
            # Обновление дерева датасетов
            self.main_window.dataset_tree.clear()
            for ds in datasets:
                name = ds.get('name', 'Без имени')
                status = ds.get('status', 'unknown')
                refresh = ds.get('lastRefreshTime', 'никогда')
                item = QTreeWidgetItem([name, status, refresh])
                
                # Цветовое выделение для дерева
                background_color = None
                status_lower = status.lower()
                if status_lower in ('failed', 'error'):
                    background_color = QColor(255, 200, 200)  # светло-красный
                else:
                    refresh_schedule = ds.get('refresh_schedule', {})
                    enabled = refresh_schedule.get('enabled') if isinstance(refresh_schedule, dict) else None
                    if enabled is False:
                        # Выбор цвета в зависимости от темы
                        if self.main_window.current_theme == "Тёмная":
                            background_color = QColor(60, 60, 60)  # тёмно-серый для тёмной темы
                        else:
                            background_color = QColor(240, 240, 240)  # светло-серый для светлой темы
                
                if background_color:
                    brush = QBrush(background_color)
                    for col in range(item.columnCount()):
                        item.setBackground(col, brush)
                
                self.main_window.dataset_tree.addTopLevelItem(item)
            
            # Обновление таблицы датасетов
            self.update_dataset_table(datasets)
            
            # Обновление статистики
            self.update_stats(datasets)
            
            self.main_window.status_bar.showMessage("Датасеты загружены", 3000)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка загрузки датасетов: {e}")
            self.main_window.status_bar.showMessage("Ошибка загрузки", 5000)
        finally:
            self.progress.hide()   # скрываем прогресс-бар после завершения
    
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
            last_refresh = ds.get('lastRefreshTime', 'никогда')
            next_refresh = ds.get('nextRefreshTime', 'не запланировано')
            
            # Определяем статус автоматического обновления
            auto_refresh_status = "Неизвестно"
            refresh_schedule = ds.get('refresh_schedule', {})
            enabled = None
            schedule_times_local = []
            if isinstance(refresh_schedule, dict):
                enabled = refresh_schedule.get('enabled')
                if enabled is True:
                    auto_refresh_status = "Включено"
                elif enabled is False:
                    auto_refresh_status = "Выключено"
                elif 'days' in refresh_schedule or 'times' in refresh_schedule:
                    auto_refresh_status = "Настроено"
                
                # Если расписание включено, вычисляем следующее обновление
                if enabled is True:
                    times = refresh_schedule.get('times', [])
                    if times:
                        # Конвертируем времена из UTC+6 в UTC+5 (Екатеринбург)
                        from_offset = 6  # UTC+6
                        to_offset = 5    # UTC+5
                        schedule_times_local = self._convert_schedule_times(times, from_offset, to_offset)
                        # Вычисляем следующее обновление
                        current_time = datetime.now()
                        next_refresh_dt = self._calculate_next_refresh(schedule_times_local, current_time)
                        if next_refresh_dt:
                            next_refresh = self._format_datetime_for_display(next_refresh_dt)
            
            # Если автообновление выключено, следующее обновление = N/A
            if enabled is False:
                next_refresh = "N/A"
            
            self.main_window.dataset_table.setItem(row, 0, QTableWidgetItem(name))
            self.main_window.dataset_table.setItem(row, 1, QTableWidgetItem(workspace))
            self.main_window.dataset_table.setItem(row, 2, QTableWidgetItem(dataset_id))
            self.main_window.dataset_table.setItem(row, 3, QTableWidgetItem(status))
            self.main_window.dataset_table.setItem(row, 4, QTableWidgetItem(last_refresh))
            self.main_window.dataset_table.setItem(row, 5, QTableWidgetItem(next_refresh))
            self.main_window.dataset_table.setItem(row, 6, QTableWidgetItem(auto_refresh_status))
            
            # Цветовое выделение строк
            background_color = None
            status_lower = status.lower()
            if status_lower in ('failed', 'error'):
                background_color = QColor(255, 200, 200)  # светло-красный
            elif enabled is False:
                # Выбор цвета в зависимости от темы
                if self.main_window.current_theme == "Тёмная":
                    background_color = QColor(60, 60, 60)  # тёмно-серый для тёмной темы
                else:
                    background_color = QColor(250, 250, 250)  # очень светло-серый для светлой темы
            elif next_refresh == "не запланировано":
                # Выделение строк, где следующее обновление не запланировано
                if self.main_window.current_theme == "Тёмная":
                    background_color = QColor(80, 80, 40)  # тёмно-жёлтый для тёмной темы
                else:
                    background_color = QColor(255, 255, 230)  # очень светло-жёлтый для светлой темы
            
            if background_color:
                brush = QBrush(background_color)
                for col in range(self.main_window.dataset_table.columnCount()):
                    item = self.main_window.dataset_table.item(row, col)
                    if item:
                        item.setBackground(brush)
    
    def update_stats(self, datasets):
        """Обновляет статистику."""
        total = len(datasets)
        enabled = sum(1 for ds in datasets if ds.get('isRefreshable', False))
        failed = sum(1 for ds in datasets if ds.get('status', '').lower() == 'failed')
        
        # Собираем все времена последнего обновления, которые не являются пустыми или "никогда"
        refresh_times = []
        for ds in datasets:
            time_val = ds.get('lastRefreshTime')
            if time_val and time_val != 'никогда' and time_val != '':
                refresh_times.append(time_val)
        
        if refresh_times:
            # Находим максимальное время (последнее обновление)
            last_update = max(refresh_times)
        else:
            last_update = 'никогда'
        
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
    
    def update_dataset_details(self, dataset):
        """Обновляет детальную информацию о выбранном датасете."""
        if not dataset:
            return
        
        name = dataset.get('name', 'Без имени')
        dataset_id = dataset.get('id', 'N/A')
        workspace_id = dataset.get('workspaceId') or dataset.get('workspace_id', '')
        workspace_name = self.main_window.get_workspace_name(workspace_id)
        status = dataset.get('status', 'unknown')
        last_refresh = dataset.get('lastRefreshTime', 'никогда')
        next_refresh = dataset.get('nextRefreshTime', 'не запланировано')
        
        # Получаем информацию о расписании
        refresh_schedule = dataset.get('refresh_schedule', {})
        schedule_text = 'не настроено'
        auto_refresh_status = 'Неизвестно'
        enabled = None
        
        # Переменные для вычисления следующего обновления
        schedule_times_local = []
        schedule_timezone = ''
        schedule_days = []
        
        if isinstance(refresh_schedule, dict) and refresh_schedule:
            enabled = refresh_schedule.get('enabled')
            if enabled is True:
                auto_refresh_status = 'Включено'
            elif enabled is False:
                auto_refresh_status = 'Выключено'
            else:
                auto_refresh_status = 'Настроено (статус неизвестен)'
            
            # Формируем текст расписания
            days = refresh_schedule.get('days', [])
            times = refresh_schedule.get('times', [])
            timezone = refresh_schedule.get('localTimeZoneId', '')
            
            # Сохраняем для вычислений
            schedule_days = days if isinstance(days, list) else []
            schedule_timezone = timezone
            
            if days and times:
                days_str = ', '.join(days) if isinstance(days, list) else str(days)
                times_str = ', '.join(times) if isinstance(times, list) else str(times)
                schedule_text = f'Дни: {days_str}\nВремя: {times_str}'
                if timezone:
                    schedule_text += f'\nЧасовой пояс: {timezone}'
                if enabled is not None:
                    schedule_text += f'\nСтатус: {"Включено" if enabled else "Выключено"}'
                
                # Конвертируем времена расписания из UTC+6 в UTC+5 (Екатеринбург)
                # Предполагаем, что timezone = "Central Asia Standard Time" (UTC+6)
                # Пользовательский часовой пояс: Екатеринбург (UTC+5)
                from_offset = 6  # UTC+6
                to_offset = 5    # UTC+5
                schedule_times_local = self._convert_schedule_times(times, from_offset, to_offset)
                
                # Добавляем конвертированное расписание в текст
                schedule_text += f'\nВремя (Екатеринбург): {", ".join(schedule_times_local)}'
            else:
                schedule_text = 'расписание не настроено'
        else:
            auto_refresh_status = 'Не настроено'
        
        # Если автообновление выключено, следующее обновление = N/A
        if enabled is False:
            next_refresh = "N/A"
        elif enabled is True and schedule_times_local:
            # Вычисляем следующее обновление на основе текущего времени в Екатеринбурге
            current_time = datetime.now()
            # Предполагаем, что текущее время уже в локальном поясе пользователя (UTC+5)
            next_refresh_dt = self._calculate_next_refresh(schedule_times_local, current_time)
            if next_refresh_dt:
                next_refresh = self._format_datetime_for_display(next_refresh_dt)
            else:
                next_refresh = "не удалось вычислить"
        
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