#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы управления состоянием пользовательского интерфейса.
"""

import logging

logger = logging.getLogger(__name__)


class UIStateMethods:
    """Методы для управления состоянием UI."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы управления состоянием UI.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def update_ui_for_disconnected_state(self):
        """Обновляет UI для состояния 'не подключено'."""
        # Очищаем все данные
        self.main_window.workspace_combo.clear()
        self.main_window.workspace_combo.addItem("-- Не подключено --")
        self.main_window.workspace_combo.setEnabled(False)
        
        self.main_window.dataset_tree.clear()
        self.main_window.dataset_tree.setHeaderLabels(["Название", "Статус", "Обновление"])
        
        # Очищаем таблицу
        self.main_window.dataset_table.setRowCount(0)
        
        # Обновляем статистику
        self.main_window.total_datasets_label.setText("Всего датасетов: --")
        self.main_window.enabled_refresh_label.setText("С обновлением: --")
        self.main_window.failed_refresh_label.setText("С ошибками: --")
        self.main_window.last_update_label.setText("Последнее обновление: --")
        
        # Обновляем детали
        self.main_window.detail_name.setText("-")
        self.main_window.detail_id.setText("-")
        self.main_window.detail_workspace.setText("-")
        self.main_window.detail_refresh_status.setText("-")
        self.main_window.detail_last_refresh.setText("-")
        self.main_window.detail_next_refresh.setText("-")
        self.main_window.detail_schedule.setText("-")
        
        # Отключаем кнопки управления
        self.main_window.enable_btn.setEnabled(False)
        self.main_window.disable_btn.setEnabled(False)
        self.main_window.manual_refresh_btn.setEnabled(False)
        if hasattr(self.main_window, 'edit_schedule_btn'):
            self.main_window.edit_schedule_btn.setEnabled(False)
        
        # Отключаем фильтры
        self.main_window.filter_enabled.setEnabled(False)
        self.main_window.filter_recent.setEnabled(False)
        self.main_window.filter_errors.setEnabled(False)
        self.main_window.filter_except_not_use.setEnabled(False)
        self.main_window.filter_in_progress.setEnabled(False)
        
        # Отключаем мониторинг
        self.main_window.start_monitor_btn.setEnabled(False)
        self.main_window.stop_monitor_btn.setEnabled(False)
        
        # Обновляем кнопку подключения
        if hasattr(self.main_window, 'connect_btn'):
            self.main_window.connect_btn.setText("Подключить")
            self.main_window.connect_btn.setEnabled(True)
    
    def update_ui_for_connected_state(self):
        """Обновляет UI для состояния 'подключено'."""
        # Включаем комбобокс рабочих областей
        self.main_window.workspace_combo.setEnabled(True)
        self.main_window.workspace_combo.clear()
        if self.main_window.workspaces:
            for ws in self.main_window.workspaces:
                name = ws.get('name', 'Без имени')
                self.main_window.workspace_combo.addItem(name, ws.get('id'))
        else:
            self.main_window.workspace_combo.addItem("Нет рабочих областей")
        
        # Включаем фильтры
        self.main_window.filter_enabled.setEnabled(True)
        self.main_window.filter_recent.setEnabled(True)
        self.main_window.filter_errors.setEnabled(True)
        self.main_window.filter_except_not_use.setEnabled(True)
        self.main_window.filter_in_progress.setEnabled(True)
        
        # Включаем кнопки управления (позже, когда выбран датасет)
        self.main_window.enable_btn.setEnabled(False)
        self.main_window.disable_btn.setEnabled(False)
        self.main_window.manual_refresh_btn.setEnabled(False)
        if hasattr(self.main_window, 'edit_schedule_btn'):
            self.main_window.edit_schedule_btn.setEnabled(False)
        self.main_window.start_monitor_btn.setEnabled(True)
        self.main_window.stop_monitor_btn.setEnabled(False)
        
        # Обновляем статус
        self.main_window.status_bar.showMessage("Подключено", 3000)
        self.main_window.log_message("UI обновлен для состояния 'подключено'")
    
    def log_message(self, message: str):
        """Добавляет сообщение в лог через стандартный логгер."""
        # Логируем через стандартный логгер - обработчик QTextEditLogHandler
        # сам добавит запись в UI с правильным форматом
        logger.info(message)