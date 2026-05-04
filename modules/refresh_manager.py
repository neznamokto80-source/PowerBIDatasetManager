#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль управления обновлениями Power BI датасетов.
Включает функции для включения/отключения автоматического обновления и ручного запуска.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
from .powerbi_client import PowerBIClient, parse_utc_to_local


class RefreshManager:
    """Менеджер для управления обновлениями датасетов Power BI."""
    
    def __init__(self, client: PowerBIClient):
        """
        Инициализация менеджера обновлений.
        
        Args:
            client: Клиент Power BI
        """
        self.client = client
    
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
        """
        if schedule is None:
            # Расписание по умолчанию: ежедневно в 3:00
            schedule = {
                "value": {
                    "enabled": True,
                    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    "times": ["03:00"],
                    "localTimeZoneId": "UTC",
                    "notifyOption": "NoNotification"
                }
            }
        
        url = f"{self.client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule"
        return self.client.make_request(url, method="PATCH", body=schedule)
    
    def disable_auto_refresh(self, workspace_id: str, dataset_id: str) -> Dict[str, Any]:
        """
        Отключает автоматическое обновление для датасета.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
        
        Returns:
            Результат операции
        """
        schedule = {
            "value": {
                "enabled": False
            }
        }
        
        url = f"{self.client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule"
        return self.client.make_request(url, method="PATCH", body=schedule)
    
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
            notify_option: Опция уведомления ("NoNotification", "MailOnFailure", "MailOnCompletion")
            refresh_type: Тип обновления ("Full", "ClearValues", "Calculate", "DataOnly", "Automatic", "Defragment")
        
        Returns:
            Результат операции
        """
        body = {
            "notifyOption": notify_option
        }
        
        if refresh_type != "Full":
            body["type"] = refresh_type
        
        url = f"{self.client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        return self.client.make_request(url, method="POST", body=body)
    
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
        """
        if refresh_id:
            url = f"{self.client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes/{refresh_id}"
        else:
            url = f"{self.client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top=1"
        
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
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_refresh_status(workspace_id, dataset_id, refresh_id)
            current_status = status.get("status", "Unknown")
            
            print(f"Статус обновления {refresh_id}: {current_status}")
            
            # Проверяем завершенные статусы
            if current_status in ["Completed", "Failed", "Disabled", "Cancelled"]:
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
        
        for dataset_id in dataset_ids:
            try:
                result = self.enable_auto_refresh(workspace_id, dataset_id, schedule)
                results["success"].append({
                    "dataset_id": dataset_id,
                    "result": result
                })
                print(f"✓ Включено обновление для датасета {dataset_id}")
            except Exception as e:
                results["failed"].append({
                    "dataset_id": dataset_id,
                    "error": str(e)
                })
                print(f"✗ Ошибка для датасета {dataset_id}: {e}")
        
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
        
        for dataset_id in dataset_ids:
            try:
                result = self.disable_auto_refresh(workspace_id, dataset_id)
                results["success"].append({
                    "dataset_id": dataset_id,
                    "result": result
                })
                print(f"✓ Отключено обновление для датасета {dataset_id}")
            except Exception as e:
                results["failed"].append({
                    "dataset_id": dataset_id,
                    "error": str(e)
                })
                print(f"✗ Ошибка для датасета {dataset_id}: {e}")
        
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
                except:
                    enhanced["durationSeconds"] = None
                    enhanced["durationFormatted"] = "—"
            
            enhanced_refreshes.append(enhanced)
        
        return enhanced_refreshes


def create_default_schedule(
    days: List[str] = None,
    times: List[str] = None,
    timezone: str = "UTC",
    notify_option: str = "NoNotification"
) -> Dict[str, Any]:
    """
    Создает настройки расписания по умолчанию.
    
    Args:
        days: Дни недели (по умолчанию все дни)
        times: Время обновления (по умолчанию ["03:00"])
        timezone: Часовой пояс (по умолчанию "UTC")
        notify_option: Опция уведомления
    
    Returns:
        Настройки расписания
    """
    if days is None:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    if times is None:
        times = ["03:00"]
    
    return {
        "value": {
            "enabled": True,
            "days": days,
            "times": times,
            "localTimeZoneId": timezone,
            "notifyOption": notify_option
        }
    }


if __name__ == "__main__":
    # Тестирование модуля
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
        
        print("\nТест завершен успешно.")
        
    except Exception as e:
        print(f"Ошибка тестирования: {e}")