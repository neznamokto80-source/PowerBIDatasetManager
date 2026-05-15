#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Операции управления обновлениями датасетов и прогресс-баром.
Объединяет функционал из refresh_management.py и progress_manager.py.
"""

import logging
from typing import Any, Dict, Optional

from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import QTimer

from src.core.powerbi_client import APIRequestError

logger = logging.getLogger(__name__)


class ProgressManager:
    """Менеджер для управления прогресс-баром."""
    
    def __init__(self, main_window):
        """
        Инициализирует менеджер прогресс-бара.
        
        Args:
            main_window: Главное окно приложения, содержащее progress_bar
        """
        self.main_window = main_window
    
    def show(self, text: Optional[str] = None, indeterminate: bool = True):
        """
        Показывает прогресс-бар.
        
        Args:
            text: Текст для отображения в прогресс-баре. Если None, используется текст по умолчанию.
            indeterminate: Если True, прогресс-бар будет неопределенным (анимированным).
                          Если False, будет отображаться конкретный прогресс (0-100).
        """
        if not hasattr(self.main_window, 'progress_bar'):
            return
        
        progress_bar = self.main_window.progress_bar
        
        # Показываем прогресс-бар
        progress_bar.setVisible(True)
        
        # Устанавливаем режим прогресса
        if indeterminate:
            progress_bar.setRange(0, 0)  # Неопределенный прогресс
        else:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
        
        # Устанавливаем текст
        if text:
            progress_bar.setFormat(text)
        else:
            if indeterminate:
                # Неопределенный режим - текст по умолчанию "Загрузка..."
                progress_bar.setFormat("Загрузка...")
            else:
                # Определенный режим - формат только процента
                progress_bar.setFormat("%p%")
    
    def hide(self):
        """Скрывает прогресс-бар."""
        if hasattr(self.main_window, 'progress_bar'):
            self.main_window.progress_bar.setVisible(False)
    
    def update(self, value: int, maximum: int = 100, text: Optional[str] = None):
        """
        Обновляет прогресс-бар с конкретным значением.
        
        Args:
            value: Текущее значение прогресса (0-100)
            maximum: Максимальное значение (по умолчанию 100)
            text: Текст для отображения (опционально)
        """
        if not hasattr(self.main_window, 'progress_bar'):
            return
        
        progress_bar = self.main_window.progress_bar
        
        # Устанавливаем диапазон и значение
        progress_bar.setRange(0, maximum)
        progress_bar.setValue(value)
        
        # Устанавливаем текст, если передан
        if text:
            progress_bar.setFormat(text)
    
    def set_indeterminate(self, indeterminate: bool = True):
        """
        Устанавливает режим неопределенного прогресса.
        
        Args:
            indeterminate: Если True, прогресс-бар будет неопределенным.
        """
        if not hasattr(self.main_window, 'progress_bar'):
            return
        
        if indeterminate:
            self.main_window.progress_bar.setRange(0, 0)
        else:
            self.main_window.progress_bar.setRange(0, 100)
    
    def is_visible(self) -> bool:
        """Проверяет, виден ли прогресс-бар."""
        if hasattr(self.main_window, 'progress_bar'):
            return self.main_window.progress_bar.isVisible()
        return False
    
    def with_progress(self, text: Optional[str] = None, indeterminate: bool = True):
        """
        Контекстный менеджер для автоматического показа/скрытия прогресс-бара.
        
        Пример использования:
            with progress_manager.with_progress("Загрузка данных..."):
                # Код, выполняемый во время показа прогресс-бара
                load_data()
        
        Args:
            text: Текст для отображения
            indeterminate: Режим неопределенного прогресса
        """
        return ProgressContext(self, text, indeterminate)


class ProgressContext:
    """Контекстный менеджер для прогресс-бара."""
    
    def __init__(self, manager: ProgressManager, text: Optional[str], indeterminate: bool):
        self.manager = manager
        self.text = text
        self.indeterminate = indeterminate
    
    def __enter__(self):
        self.manager.show(self.text, self.indeterminate)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.hide()
        return False  # Не подавляем исключения


class RefreshOperations:
    """Операции для управления обновлениями датасетов."""
    
    def __init__(self, main_window):
        """
        Инициализирует операции управления обновлениями.
        
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

        from src.ui.schedule_editor_dialog import ScheduleEditorDialog
        
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

    def update_refresh_schedule(self, workspace_id: str, dataset_id: str, payload: Dict[str, Any]):
        """
        Обновляет расписание обновления для указанного датасета.
        
        Args:
            workspace_id: Идентификатор рабочей области
            dataset_id: Идентификатор датасета
            payload: Словарь с параметрами расписания (days, times, localTimeZoneId, notifyOption, enabled)
        """
        if not self.main_window.refresh_manager:
            raise ValueError("RefreshManager не инициализирован")
        
        try:
            self.main_window.log_message(f"Сохранение расписания для датасета {dataset_id}...")
            self.main_window.status_bar.showMessage("Сохранение расписания...")
            
            self.main_window.refresh_manager.update_refresh_schedule(workspace_id, dataset_id, payload)
            
            self.main_window.log_message("✓ Расписание сохранено")
            self.main_window.status_bar.showMessage("Расписание сохранено", 3000)
            
            # Обновляем данные, чтобы отразить изменения
            self.main_window.refresh_data()
            
        except Exception as e:
            self.main_window.log_message(f"✗ Ошибка сохранения расписания: {e}")
            self.main_window.status_bar.showMessage("Ошибка сохранения расписания", 5000)
            raise