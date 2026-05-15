#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Методы управления обновлениями датасетов.
"""

import logging
from typing import Any, Dict, Optional

from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import QTimer

from src.core.powerbi_client import APIRequestError
from src.ui.schedule_editor_dialog import ScheduleEditorDialog

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

    def _resync_current_dataset_after_load(self, dataset_id: str) -> None:
        """Подставляет в current_dataset актуальную запись после load_datasets."""
        for d in self.main_window.datasets or []:
            if d.get("id") == dataset_id:
                self.main_window.current_dataset = d
                self.main_window.update_dataset_details(d)
                return

    def edit_refresh_schedule(
        self,
        dataset: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Открывает диалог создания/изменения/удаления расписания обновления.

        Returns:
            True после успешного сохранения или удаления расписания; False при отмене, ошибке или без действия.
        """
        if not self.main_window.refresh_manager or not self.main_window.client:
            self.main_window.log_message("Нет подключения к Power BI")
            QMessageBox.warning(
                self.main_window,
                "Расписание",
                "Подключитесь к Power BI, чтобы управлять расписанием.",
            )
            return False

        ds = dataset or self.main_window.current_dataset
        ws = workspace_id or self.main_window.current_workspace
        if not ds or not ws:
            self.main_window.log_message("Не выбран датасет или рабочая область")
            QMessageBox.warning(
                self.main_window,
                "Расписание",
                "Выберите датасет и рабочую область.",
            )
            return False

        dataset_id = ds.get("id")
        if not dataset_id:
            QMessageBox.warning(self.main_window, "Расписание", "У датасета нет идентификатора.")
            return False

        initial: Dict[str, Any] = {}
        try:
            initial = self.main_window.client.get_refresh_schedule(ws, dataset_id)
        except APIRequestError as e:
            if e.status_code != 404:
                self.main_window.log_message(f"✗ Ошибка чтения расписания: {e}")
                QMessageBox.critical(
                    self.main_window,
                    "Ошибка",
                    f"Не удалось получить расписание:\n{e}",
                )
                return False

        dlg = ScheduleEditorDialog(self.main_window, initial_schedule=initial)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False

        action = dlg.action()
        dataset_name = ds.get("name", dataset_id)

        try:
            if action == ScheduleEditorDialog.ACTION_DELETE:
                self.main_window.log_message(f"Отключение расписания для {dataset_name}...")
                self.main_window.status_bar.showMessage("Удаление расписания...")
                self.main_window.refresh_manager.disable_auto_refresh(ws, dataset_id)
                self.main_window.log_message("✓ Запланированное обновление отключено")
                self.main_window.status_bar.showMessage("Расписание отключено", 3000)
            elif action == ScheduleEditorDialog.ACTION_SAVE:
                payload = dlg.get_schedule_payload()
                self.main_window.log_message(f"Сохранение расписания для {dataset_name}...")
                self.main_window.status_bar.showMessage("Сохранение расписания...")
                self.main_window.refresh_manager.update_refresh_schedule(ws, dataset_id, payload)
                self.main_window.log_message("✓ Расписание сохранено")
                self.main_window.status_bar.showMessage("Расписание сохранено", 3000)
            else:
                return False

            self.main_window.refresh_data()
            self._resync_current_dataset_after_load(dataset_id)
            return True

        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка расписания: {e}")
            self.main_window.status_bar.showMessage("Ошибка расписания", 5000)
            QMessageBox.critical(
                self.main_window,
                "Ошибка",
                f"Не удалось применить изменения расписания:\n{e}",
            )
            return False
    
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
            
            # Используем refresh_manager для обновления
            result = self.main_window.refresh_manager.trigger_manual_refresh(
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
    
    def enable_auto_refresh_selected(self, datasets):
        """Включает автоматическое обновление для выбранных датасетов."""
        if not datasets:
            self.main_window.log_message("Нет выбранных датасетов")
            return
        
        count = len(datasets)
        self.main_window.log_message(f"Включение автообновления для {count} датасетов...")
        self.main_window.status_bar.showMessage(f"Включение автообновления для {count} датасетов...")
        
        success = 0
        errors = []
        
        for i, dataset in enumerate(datasets):
            dataset_id = dataset.get('id')
            dataset_name = dataset.get('name', dataset_id)
            workspace_id = dataset.get('workspaceId', self.main_window.current_workspace)
            if not workspace_id:
                errors.append(f"{dataset_name}: нет рабочей области")
                continue
            
            try:
                self.main_window.refresh_manager.enable_auto_refresh(workspace_id, dataset_id)
                success += 1
                self.main_window.log_message(f"✓ {dataset_name}: автообновление включено")
            except Exception as e:
                errors.append(f"{dataset_name}: {str(e)}")
        
        # Итоговое сообщение
        if errors:
            self.main_window.log_message(f"✗ Ошибки при включении автообновления: {', '.join(errors)}")
            self.main_window.status_bar.showMessage(f"Ошибки при включении автообновления", 5000)
            QMessageBox.warning(
                self.main_window,
                "Частичный успех",
                f"Включено для {success} из {count} датасетов.\nОшибки:\n" + "\n".join(errors)
            )
        else:
            self.main_window.log_message(f"✓ Автообновление включено для всех {count} датасетов")
            self.main_window.status_bar.showMessage(f"Автообновление включено для {count} датасетов", 3000)
        
        # Обновляем данные
        self.main_window.refresh_data()
    
    def disable_auto_refresh_selected(self, datasets):
        """Отключает автоматическое обновление для выбранных датасетов."""
        if not datasets:
            self.main_window.log_message("Нет выбранных датасетов")
            return
        
        count = len(datasets)
        self.main_window.log_message(f"Отключение автообновления для {count} датасетов...")
        self.main_window.status_bar.showMessage(f"Отключение автообновления для {count} датасетов...")
        
        success = 0
        errors = []
        
        for i, dataset in enumerate(datasets):
            dataset_id = dataset.get('id')
            dataset_name = dataset.get('name', dataset_id)
            workspace_id = dataset.get('workspaceId', self.main_window.current_workspace)
            if not workspace_id:
                errors.append(f"{dataset_name}: нет рабочей области")
                continue
            
            try:
                self.main_window.refresh_manager.disable_auto_refresh(workspace_id, dataset_id)
                success += 1
                self.main_window.log_message(f"✓ {dataset_name}: автообновление отключено")
            except Exception as e:
                errors.append(f"{dataset_name}: {str(e)}")
        
        # Итоговое сообщение
        if errors:
            self.main_window.log_message(f"✗ Ошибки при отключении автообновления: {', '.join(errors)}")
            self.main_window.status_bar.showMessage(f"Ошибки при отключении автообновления", 5000)
            QMessageBox.warning(
                self.main_window,
                "Частичный успех",
                f"Отключено для {success} из {count} датасетов.\nОшибки:\n" + "\n".join(errors)
            )
        else:
            self.main_window.log_message(f"✓ Автообновление отключено для всех {count} датасетов")
            self.main_window.status_bar.showMessage(f"Автообновление отключено для {count} датасетов", 3000)
        
        # Обновляем данные
        self.main_window.refresh_data()
    
    def trigger_manual_refresh_selected(self, datasets):
        """Запускает ручное обновление для выбранных датасетов."""
        if not datasets:
            self.main_window.log_message("Нет выбранных датасетов")
            return
        
        count = len(datasets)
        self.main_window.log_message(f"Запуск ручного обновления для {count} датасетов...")
        self.main_window.status_bar.showMessage(f"Запуск обновления для {count} датасетов...")
        
        success = 0
        errors = []
        
        for i, dataset in enumerate(datasets):
            dataset_id = dataset.get('id')
            dataset_name = dataset.get('name', dataset_id)
            workspace_id = dataset.get('workspaceId', self.main_window.current_workspace)
            if not workspace_id:
                errors.append(f"{dataset_name}: нет рабочей области")
                continue
            
            try:
                self.main_window.refresh_manager.trigger_manual_refresh(workspace_id, dataset_id)
                success += 1
                self.main_window.log_message(f"✓ {dataset_name}: ручное обновление запущено")
            except Exception as e:
                errors.append(f"{dataset_name}: {str(e)}")
        
        # Итоговое сообщение
        if errors:
            self.main_window.log_message(f"✗ Ошибки при запуске обновления: {', '.join(errors)}")
            self.main_window.status_bar.showMessage(f"Ошибки при запуске обновления", 5000)
            QMessageBox.warning(
                self.main_window,
                "Частичный успех",
                f"Запущено для {success} из {count} датасетов.\nОшибки:\n" + "\n".join(errors)
            )
        else:
            self.main_window.log_message(f"✓ Ручное обновление запущено для всех {count} датасетов")
            self.main_window.status_bar.showMessage(f"Обновление запущено для {count} датасетов", 3000)
        
    def trigger_manual_refresh_selected(self, datasets):
        """Запускает ручное обновление для выбранных датасетов."""