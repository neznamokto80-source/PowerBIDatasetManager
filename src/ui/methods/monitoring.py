#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы мониторинга в реальном времени.
"""

import logging

logger = logging.getLogger(__name__)


class MonitoringMethods:
    """Методы для мониторинга в реальном времени."""
    
    def __init__(self, main_window):
        """
        Инициализирует методы мониторинга.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def start_monitoring(self):
        """Запускает мониторинг в реальном времени."""
        if self.main_window.auto_refresh_enabled:
            self.main_window.log_message("Мониторинг уже запущен")
            return
        
        try:
            # Запускаем таймер с интервалом 60 секунд (можно настроить)
            interval = 60000  # 60 секунд в миллисекундах
            self.main_window.update_timer.start(interval)
            self.main_window.auto_refresh_enabled = True
            
            # Обновляем UI
            self.main_window.start_monitor_btn.setEnabled(False)
            self.main_window.stop_monitor_btn.setEnabled(True)
            self.main_window.status_bar.showMessage("Мониторинг запущен", 3000)
            self.main_window.log_message(f"✓ Мониторинг запущен (интервал: {interval//1000} сек)")
            
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
            self.main_window.status_bar.showMessage("Мониторинг остановлен", 3000)
            self.main_window.log_message("✓ Мониторинг остановлен")
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка остановки мониторинга: {e}")
            self.main_window.status_bar.showMessage("Ошибка остановки мониторинга", 5000)