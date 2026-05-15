#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль управления обновлениями Power BI датасетов.
Включает функции для включения/отключения автоматического обновления и ручного запуска.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from .powerbi_client import PowerBIClient, parse_utc_to_local
from .refresh_operations import (
    enable_auto_refresh as enable_auto_refresh_op,
    disable_auto_refresh as disable_auto_refresh_op,
    trigger_manual_refresh as trigger_manual_refresh_op,
    update_refresh_schedule as update_refresh_schedule_op,
)

logger = logging.getLogger(__name__)


class RefreshManager:
    """Менеджер для управления обновлениями датасетов Power BI."""
    
    # Константы статусов обновлений
    COMPLETED_STATUSES = {"Completed", "Failed", "Disabled", "Cancelled"}
    
    # Константы типов обновлений
    REFRESH_TYPES = {
        "Full", "ClearValues", "Calculate", "DataOnly",
        "Automatic", "Defragment"
    }
    
    # Константы опций уведомлений
    NOTIFY_OPTIONS = {
        "NoNotification", "MailOnFailure", "MailOnCompletion"
    }
    
    def __init__(self, client: PowerBIClient):
        """
        Инициализация менеджера обновлений.
        
        Args:
            client: Клиент Power BI
        """
        self.client = client
        logger.debug("RefreshManager инициализирован")
    
    def enable_auto_refresh(
        self,
        workspace_id: str,
        dataset_id: str,
        schedule: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Включает автоматическое обновление для датасета.

        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
            schedule: Настройки расписания (если None, используется расписание по умолчанию)

        Returns:
            Результат операции

        Raises:
            APIRequestError: При ошибке запроса к API
        """
        return enable_auto_refresh_op(self.client, workspace_id, dataset_id, schedule)
    
    def disable_auto_refresh(self, workspace_id: str, dataset_id: str) -> Dict[str, Any]:
        """
        Отключает автоматическое обновление для датасета.

        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета

        Returns:
            Результат операции

        Raises:
            APIRequestError: При ошибке запроса к API
        """
        return disable_auto_refresh_op(self.client, workspace_id, dataset_id)

    def update_refresh_schedule(
        self,
        workspace_id: str,
        dataset_id: str,
        schedule: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Создаёт или обновляет расписание обновления (PATCH refreshSchedule).

        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
            schedule: Поля расписания (enabled, days, times, localTimeZoneId, notifyOption)

        Returns:
            Результат операции
        """
        return update_refresh_schedule_op(self.client, workspace_id, dataset_id, schedule)

    def trigger_manual_refresh(
        self,
        workspace_id: str,
        dataset_id: str,
        notify_option: str = "NoNotification",
        refresh_type: str = "Full"
    ) -> Dict[str, Any]:
        """
        Запускает ручное обновление датасета.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
            notify_option: Опция уведомления
            refresh_type: Тип обновления
        
        Returns:
            Результат операции
        
        Raises:
            ValueError: При недопустимых значениях параметров
            APIRequestError: При ошибке запроса к API
        """
        return trigger_manual_refresh_op(
            self.client,
            workspace_id,
            dataset_id,
            notify_option,
            refresh_type
        )
    
    def get_refresh_status(
        self,
        workspace_id: str,
        dataset_id: str,
        refresh_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получает статус конкретного обновления или последнего обновления.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
            refresh_id: ID обновления (если None, возвращает последнее)
        
        Returns:
            Статус обновления
        
        Raises:
            APIRequestError: При ошибке запроса к API
        """
        if refresh_id:
            url = f"{self.client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes/{refresh_id}"
            logger.debug(f"Получение статуса обновления {refresh_id}")
        else:
            url = f"{self.client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top=1"
            logger.debug(f"Получение статуса последнего обновления")
        
        return self.client.make_request(url)
    
    def wait_for_refresh_completion(
        self,
        workspace_id: str,
        dataset_id: str,
        refresh_id: str,
        poll_interval: int = 10,
        timeout: int = 3600
    ) -> Dict[str, Any]:
        """
        Ожидает завершения обновления, периодически проверяя статус.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
            refresh_id: ID обновления
            poll_interval: Интервал проверки в секундах
            timeout: Максимальное время ожидания в секундах
        
        Returns:
            Финальный статус обновления
        
        Raises:
            TimeoutError: Если обновление не завершилось за timeout
            APIRequestError: При ошибке запроса к API
        """
        start_time = time.time()
        logger.info(f"Ожидание завершения обновления {refresh_id} (таймаут: {timeout}с)")
        
        while time.time() - start_time < timeout:
            status = self.get_refresh_status(workspace_id, dataset_id, refresh_id)
            current_status = status.get("status", "Unknown")
            
            logger.debug(f"Статус обновления {refresh_id}: {current_status}")
            
            # Проверяем завершенные статусы
            if current_status in self.COMPLETED_STATUSES:
                logger.info(f"Обновление {refresh_id} завершено со статусом: {current_status}")
                return status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Обновление {refresh_id} не завершилось за {timeout} секунд")
    
    def batch_enable_refresh(
        self,
        workspace_id: str,
        dataset_ids: List[str],
        schedule: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Включает автоматическое обновление для нескольких датасетов.
        
        Args:
            workspace_id: ID рабочей области
            dataset_ids: Список ID датасетов
            schedule: Настройки расписания
        
        Returns:
            Результаты для каждого датасета
        """
        results = {"success": [], "failed": []}
        logger.info(f"Пакетное включение автообновления для {len(dataset_ids)} датасетов")
        
        for dataset_id in dataset_ids:
            try:
                result = self.enable_auto_refresh(workspace_id, dataset_id, schedule)
                results["success"].append({
                    "dataset_id": dataset_id,
                    "result": result
                })
                logger.info(f"✓ Включено обновление для датасета {dataset_id}")
            except Exception as e:
                results["failed"].append({
                    "dataset_id": dataset_id,
                    "error": str(e)
                })
                logger.error(f"✗ Ошибка для датасета {dataset_id}: {e}")
        
        logger.info(
            f"Пакетное включение завершено: успешно {len(results['success'])}, "
            f"ошибок {len(results['failed'])}"
        )
        return results
    
    def batch_disable_refresh(
        self,
        workspace_id: str,
        dataset_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Отключает автоматическое обновление для нескольких датасетов.
        
        Args:
            workspace_id: ID рабочей области
            dataset_ids: Список ID датасетов
        
        Returns:
            Результаты для каждого датасета
        """
        results = {"success": [], "failed": []}
        logger.info(f"Пакетное отключение автообновления для {len(dataset_ids)} датасетов")
        
        for dataset_id in dataset_ids:
            try:
                result = self.disable_auto_refresh(workspace_id, dataset_id)
                results["success"].append({
                    "dataset_id": dataset_id,
                    "result": result
                })
                logger.info(f"✓ Отключено обновление для датасета {dataset_id}")
            except Exception as e:
                results["failed"].append({
                    "dataset_id": dataset_id,
                    "error": str(e)
                })
                logger.error(f"✗ Ошибка для датасета {dataset_id}: {e}")
        
        logger.info(
            f"Пакетное отключение завершено: успешно {len(results['success'])}, "
            f"ошибок {len(results['failed'])}"
        )
        return results
    
    def get_refresh_history(
        self,
        workspace_id: str,
        dataset_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Получает историю обновлений датасета.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
            limit: Максимальное количество записей
        
        Returns:
            Список обновлений с дополнительной информацией
        """
        logger.debug(f"Получение истории обновлений для датасета {dataset_id}, лимит: {limit}")
        
        refreshes = self.client.get_all_refreshes(workspace_id, dataset_id, top=limit)
        
        enhanced_refreshes = []
        for refresh in refreshes:
            enhanced = refresh.copy()
            
            # Добавляем читаемое время
            if "startTime" in refresh:
                enhanced["startTimeLocal"] = parse_utc_to_local(refresh["startTime"])
            if "endTime" in refresh:
                enhanced["endTimeLocal"] = parse_utc_to_local(refresh["endTime"])
            
            # Рассчитываем длительность, если есть оба времени
            if "startTime" in refresh and "endTime" in refresh:
                try:
                    start = datetime.fromisoformat(refresh["startTime"].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(refresh["endTime"].replace('Z', '+00:00'))
                    duration = end - start
                    enhanced["durationSeconds"] = duration.total_seconds()
                    enhanced["durationFormatted"] = str(duration)
                except Exception as e:
                    logger.debug(f"Ошибка расчета длительности: {e}")
                    enhanced["durationSeconds"] = None
                    enhanced["durationFormatted"] = "—"
            
            enhanced_refreshes.append(enhanced)
        
        logger.debug(f"Получено {len(enhanced_refreshes)} записей истории обновлений")
        return enhanced_refreshes
    
    def get_refresh_summary(
        self,
        workspace_id: str,
        dataset_id: str
    ) -> Dict[str, Any]:
        """
        Возвращает сводную информацию об обновлениях датасета.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
        
        Returns:
            Сводная информация
        """
        logger.debug(f"Получение сводной информации об обновлениях для датасета {dataset_id}")
        
        history = self.get_refresh_history(workspace_id, dataset_id, limit=50)
        
        if not history:
            return {
                "total_refreshes": 0,
                "last_refresh": None,
                "success_rate": 0.0,
                "average_duration": None
            }
        
        # Статистика
        total = len(history)
        successful = sum(1 for r in history if r.get("status") == "Completed")
        success_rate = (successful / total) * 100 if total > 0 else 0.0
        
        # Средняя длительность
        durations = [
            r["durationSeconds"] for r in history
            if r.get("durationSeconds") is not None
        ]
        avg_duration = sum(durations) / len(durations) if durations else None
        
        # Последнее обновление
        last_refresh = history[0] if history else None
        
        return {
            "total_refreshes": total,
            "last_refresh": last_refresh,
            "success_rate": success_rate,
            "average_duration": avg_duration,
            "successful_count": successful,
            "failed_count": total - successful
        }


if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    print("Тестирование модуля управления обновлениями...")
    
    try:
        from powerbi_client import PowerBIClient
        
        client = PowerBIClient()
        client.authenticate()
        
        manager = RefreshManager(client)
        
        # Получаем список рабочих областей для теста
        workspaces = client.get_workspaces()
        if not workspaces:
            print("Нет рабочих областей для тестирования.")
        else:
            workspace = workspaces[0]
            workspace_id = workspace["id"]
            workspace_name = workspace["name"]
            
            print(f"Тестирование на рабочей области: {workspace_name} (ID: {workspace_id})")
            
            # Получаем датасеты
            datasets = client.get_datasets_in_workspace(workspace_id)
            print(f"Найдено датасетов: {len(datasets)}")
            
            if datasets:
                dataset = datasets[0]
                dataset_id = dataset["id"]
                dataset_name = dataset["name"]
                
                print(f"\nТестирование на датасете: {dataset_name} (ID: {dataset_id})")
                
                # Получаем текущее расписание
                try:
                    schedule = client.get_refresh_schedule(workspace_id, dataset_id)
                    print(f"Текущее расписание: enabled={schedule.get('enabled', False)}")
                except Exception as e:
                    print(f"Ошибка получения расписания: {e}")
                
                # Тест получения истории обновлений
                try:
                    history = manager.get_refresh_history(workspace_id, dataset_id, limit=5)
                    print(f"История обновлений: {len(history)} записей")
                except Exception as e:
                    print(f"Ошибка получения истории: {e}")
                
                # Тест получения сводной информации
                try:
                    summary = manager.get_refresh_summary(workspace_id, dataset_id)
                    print(f"Сводная информация: {summary['total_refreshes']} обновлений, "
                          f"успешных: {summary['successful_count']}")
                except Exception as e:
                    print(f"Ошибка получения сводной информации: {e}")
        
        print("\nТест завершен успешно.")
        
    except Exception as e:
        print(f"Ошибка тестирования: {e}")