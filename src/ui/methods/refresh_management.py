#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы управления обновлениями датасетов.
"""

import logging

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)


class RefreshManagementMethods:
    """Методы для управления обновлениями датасетов."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы управления обновлениями.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def enable_auto_refresh(self):
        """Включает автоматическое обновление для выбранного датасета."""
        if not self.main_window.current_dataset or not self.main_window.current_workspace:
            self.main_window.log_message("Не выбран датасет или рабочая область")
            return
        
        try:
            dataset_id = self.main_window.current_dataset.get('id')
            dataset_name = self.main_window.current_dataset.get('name', dataset_id)
            self.main_window.log_message(
                f"Включение автообновления для датасета {dataset_name}..."
            )
            self.main_window.status_bar.showMessage("Включение автообновления...")
            
            result = self.main_window.refresh_manager.enable_auto_refresh(
                self.main_window.current_workspace,
                dataset_id
            )
            
            self.main_window.log_message("✓ Автообновление включено")
            self.main_window.status_bar.showMessage("Автообновление включено", 3000)
            
            # Обновляем данные, чтобы отразить изменения
            self.main_window.refresh_data()
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка включения автообновления: {e}")
            self.main_window.status_bar.showMessage("Ошибка включения автообновления", 5000)
            QMessageBox.critical(
                self.main_window,
                "Ошибка",
                f"Не удалось включить автообновление:\n{str(e)}"
            )
    
    def disable_auto_refresh(self):
        """Отключает автоматическое обновление для выбранного датасета."""
        if not self.main_window.current_dataset or not self.main_window.current_workspace:
            self.main_window.log_message("Не выбран датасет или рабочая область")
            return
        
        try:
            dataset_id = self.main_window.current_dataset.get('id')
            dataset_name = self.main_window.current_dataset.get('name', dataset_id)
            self.main_window.log_message(
                f"Отключение автообновления для датасета {dataset_name}..."
            )
            self.main_window.status_bar.showMessage("Отключение автообновления...")
            
            result = self.main_window.refresh_manager.disable_auto_refresh(
                self.main_window.current_workspace,
                dataset_id
            )
            
            self.main_window.log_message("✓ Автообновление отключено")
            self.main_window.status_bar.showMessage("Автообновление отключено", 3000)
            
            # Обновляем данные
            self.main_window.refresh_data()
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка отключения автообновления: {e}")
            self.main_window.status_bar.showMessage("Ошибка отключения автообновления", 5000)
            QMessageBox.critical(
                self.main_window,
                "Ошибка",
                f"Не удалось отключить автообновление:\n{str(e)}"
            )
    
    def trigger_manual_refresh(self):
        """Запускает ручное обновление выбранного датасета."""
        if not self.main_window.current_dataset or not self.main_window.current_workspace:
            self.main_window.log_message("Не выбран датасет или рабочая область")
            return
        
        try:
            dataset_id = self.main_window.current_dataset.get('id')
            dataset_name = self.main_window.current_dataset.get('name', dataset_id)
            self.main_window.log_message(
                f"Запуск ручного обновления для датасета {dataset_name}..."
            )
            self.main_window.status_bar.showMessage("Запуск обновления...")
            
            # Используем data_provider для обновления
            result = self.main_window.data_provider.refresh_dataset(
                self.main_window.current_workspace,
                dataset_id
            )
            
            self.main_window.log_message("✓ Ручное обновление запущено")
            self.main_window.status_bar.showMessage("Обновление запущено", 3000)
            
            # Обновляем данные через несколько секунд
            QTimer.singleShot(5000, self.main_window.refresh_data)
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка запуска ручного обновления: {e}")
            self.main_window.status_bar.showMessage("Ошибка запуска обновления", 5000)
            QMessageBox.critical(
                self.main_window,
                "Ошибка",
                f"Не удалось запустить обновление:\n{str(e)}"
            )