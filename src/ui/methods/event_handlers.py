#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчики событий пользовательского интерфейса.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton,
    QTreeWidgetItem, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)


class EventHandlers:
    """Обработчики событий UI."""
    
    def __init__(self, main_window):
        """
        Инициализирует обработчики событий.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    def on_workspace_selected(self, index):
        """Обработчик выбора рабочей области."""
        if index < 0 or not self.main_window.workspaces:
            return
        
        workspace_id = self.main_window.workspace_combo.itemData(index)
        if workspace_id:
            self.main_window.current_workspace = workspace_id
            self.main_window.log_message(
                f"Выбрана рабочая область: {self.main_window.workspace_combo.itemText(index)}"
            )
            self.main_window.load_datasets()
    
    def on_dataset_selected(self, item, column):
        """Обработчик выбора датасета."""
        if not item:
            return
        
        # Получаем имя датасета из выбранного элемента
        dataset_name = item.text(0) if isinstance(item, QTreeWidgetItem) else item.text()
        
        # Ищем датасет в списке
        dataset = None
        for ds in self.main_window.datasets:
            if ds.get('name') == dataset_name:
                dataset = ds
                break
        
        if dataset:
            self.main_window.current_dataset = dataset  # сохраняем объект датасета
            self.main_window.update_dataset_details(dataset)
            self.main_window.log_message(f"Выбран датасет: {dataset_name}")
            
            # Включаем кнопки управления
            self.main_window.enable_btn.setEnabled(True)
            self.main_window.disable_btn.setEnabled(True)
            self.main_window.manual_refresh_btn.setEnabled(True)
        else:
            self.main_window.log_message(f"Датасет {dataset_name} не найден в списке")
    
    def on_dataset_double_clicked(self, item):
        """Обработчик двойного клика по датасету."""
        if not item:
            return
        
        # Получаем имя датасета
        dataset_name = item.text(0) if isinstance(item, QTreeWidgetItem) else item.text()
        
        # Ищем датасет
        dataset = None
        for ds in self.main_window.datasets:
            if ds.get('name') == dataset_name:
                dataset = ds
                break
        
        if dataset:
            # Показываем диалог с детальной информацией
            dialog = QDialog(self.main_window)
            dialog.setWindowTitle(f"Детали датасета: {dataset_name}")
            dialog.setGeometry(200, 200, 500, 400)
            
            layout = QVBoxLayout()
            
            info_text = f"""
            Название: {dataset.get('name', 'N/A')}
            ID: {dataset.get('id', 'N/A')}
            Рабочая область: {self.main_window.get_workspace_name(dataset.get('workspaceId', ''))}
            Статус: {dataset.get('status', 'unknown')}
            Последнее обновление: {dataset.get('lastRefreshTime', 'никогда')}
            Следующее обновление: {dataset.get('nextRefreshTime', 'не запланировано')}
            Обновляемость: {'Да' if dataset.get('isRefreshable', False) else 'Нет'}
            Создан: {dataset.get('createdDate', 'N/A')}
            Изменен: {dataset.get('lastUpdate', 'N/A')}
            """
            
            text_edit = QTextEdit()
            text_edit.setPlainText(info_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec()
            
            self.main_window.log_message(f"Открыты детали датасета: {dataset_name}")
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы датасетов."""
        # Определяем, откуда вызвано меню (таблица или дерево)
        sender = self.main_window.sender()
        
        menu = QMenu(self.main_window)
        
        # Общие действия
        refresh_action = QAction("Обновить", self.main_window)
        refresh_action.triggered.connect(self.main_window.refresh_data)
        
        details_action = QAction("Показать детали", self.main_window)
        details_action.triggered.connect(lambda: self.on_dataset_double_clicked(
            sender.currentItem() if hasattr(sender, 'currentItem') else None
        ))
        
        # Действия для выбранного датасета
        if hasattr(sender, 'currentItem') and sender.currentItem():
            enable_action = QAction("Включить автообновление", self.main_window)
            enable_action.triggered.connect(self.main_window.enable_auto_refresh)
            
            disable_action = QAction("Отключить автообновление", self.main_window)
            disable_action.triggered.connect(self.main_window.disable_auto_refresh)
            
            manual_refresh_action = QAction("Запустить обновление вручную", self.main_window)
            manual_refresh_action.triggered.connect(self.main_window.trigger_manual_refresh)
            
            menu.addAction(refresh_action)
            menu.addSeparator()
            menu.addAction(details_action)
            menu.addSeparator()
            menu.addAction(enable_action)
            menu.addAction(disable_action)
            menu.addAction(manual_refresh_action)
        else:
            menu.addAction(refresh_action)
            menu.addAction(details_action)
        
        menu.exec(sender.mapToGlobal(position))