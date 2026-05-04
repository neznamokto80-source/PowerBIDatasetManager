#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Провайдер данных для получения информации о датасетах из различных источников.
Генерирует фиктивные данные для демонстрации работы приложения.
"""

import random
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from modules.connection_manager import get_connection_manager


class DatasetStatus(Enum):
    """Статусы датасетов."""
    ACTIVE = "Активен"
    INACTIVE = "Неактивен"
    ERROR = "Ошибка"
    PROCESSING = "В обработке"


class AutoRefreshStatus(Enum):
    """Статусы автообновления."""
    ENABLED = "Вкл"
    DISABLED = "Выкл"
    SCHEDULED = "По расписанию"


class DataProvider:
    """
    Провайдер данных для получения информации о датасетах.
    Поддерживает многопоточное получение данных и кэширование.
    """
    
    def __init__(self):
        """Инициализация провайдера данных."""
        self._lock = threading.RLock()
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_timestamp: Dict[str, datetime] = {}
        self._cache_ttl = 30  # Время жизни кэша в секундах
        self._connection_manager = get_connection_manager()
        
        # Фиктивные имена датасетов для генерации
        self._dataset_names = [
            "Sales Dashboard", "Financial Reports", "Marketing Analytics",
            "Customer Insights", "Inventory Management", "HR Analytics",
            "Supply Chain", "Product Performance", "Web Analytics",
            "Social Media Metrics", "Operational Efficiency", "Quality Control",
            "Risk Assessment", "Budget Planning", "Forecast Models"
        ]
        
        self._descriptions = [
            "Основной дашборд продаж с детализацией по регионам",
            "Финансовая отчетность и анализ прибыльности",
            "Аналитика маркетинговых кампаний и ROI",
            "Инсайты по клиентскому поведению и удержанию",
            "Управление запасами и оптимизация складских остатков",
            "Аналитика персонала и эффективности сотрудников",
            "Мониторинг цепочки поставок и логистики",
            "Анализ производительности продуктов и услуг",
            "Веб-аналитика и метрики посещаемости",
            "Метрики социальных медиа и вовлеченности",
            "Анализ операционной эффективности процессов",
            "Контроль качества и отслеживание дефектов",
            "Оценка рисков и управление compliance",
            "Планирование бюджета и финансовое моделирование",
            "Прогнозные модели и предиктивная аналитика"
        ]
    
    def get_datasets_for_workspace(self, workspace: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Получить список датасетов для указанной рабочей области.
        
        Args:
            workspace: Название рабочей области
            force_refresh: Принудительно обновить данные, игнорируя кэш
            
        Returns:
            Список словарей с информацией о датасетах
        """
        with self._lock:
            # Проверяем кэш
            if not force_refresh and workspace in self._cache:
                cache_age = (datetime.now() - self._cache_timestamp[workspace]).total_seconds()
                if cache_age < self._cache_ttl:
                    return self._cache[workspace].copy()
            
            # Генерируем фиктивные данные
            datasets = self._generate_datasets(workspace)
            
            # Сохраняем в кэш
            self._cache[workspace] = datasets
            self._cache_timestamp[workspace] = datetime.now()
            
            return datasets.copy()
    
    def _generate_datasets(self, workspace: str) -> List[Dict[str, Any]]:
        """
        Сгенерировать фиктивные данные о датасетах для рабочей области.
        
        Args:
            workspace: Название рабочей области
            
        Returns:
            Список словарей с информацией о датасетах
        """
        # Количество датасетов зависит от рабочей области
        workspace_configs = {
            "PROFISOFT": {"count": 12, "active_ratio": 0.9},
            "Домен1": {"count": 8, "active_ratio": 0.7},
            "Домен2": {"count": 6, "active_ratio": 0.5},
            "Домен3": {"count": 4, "active_ratio": 0.3}
        }
        
        config = workspace_configs.get(workspace, {"count": 5, "active_ratio": 0.5})
        count = config["count"]
        active_ratio = config["active_ratio"]
        
        datasets = []
        used_names = set()
        
        for i in range(count):
            # Генерация уникального имени
            base_name = random.choice(self._dataset_names)
            suffix = f" {workspace}" if random.random() < 0.3 else ""
            name = f"{base_name}{suffix}"
            
            # Проверяем уникальность
            if name in used_names:
                name = f"{base_name} {i+1}{suffix}"
            used_names.add(name)
            
            # Генерация статусов
            is_active = random.random() < active_ratio
            status = DatasetStatus.ACTIVE if is_active else DatasetStatus.INACTIVE
            
            # Случайный статус ошибки для неактивных
            if not is_active and random.random() < 0.2:
                status = DatasetStatus.ERROR
            
            # Автообновление
            auto_refresh_prob = 0.7 if is_active else 0.3
            auto_refresh_enabled = random.random() < auto_refresh_prob
            auto_refresh_status = (AutoRefreshStatus.ENABLED if auto_refresh_enabled 
                                  else AutoRefreshStatus.DISABLED)
            
            # Даты обновления
            days_ago = random.randint(0, 30)
            last_update = datetime.now() - timedelta(days=days_ago, 
                                                    hours=random.randint(0, 23),
                                                    minutes=random.randint(0, 59))
            
            # Описание
            description = random.choice(self._descriptions)
            if workspace != "PROFISOFT":
                description = f"[{workspace}] {description}"
            
            # Размер данных (в МБ)
            size_mb = random.randint(10, 1000)
            
            dataset = {
                "id": f"dataset-{workspace.lower()}-{i:03d}",
                "name": name,
                "status": status.value,
                "status_raw": status,
                "last_update": last_update,
                "last_update_str": last_update.strftime("%Y-%m-%d %H:%M"),
                "auto_refresh": auto_refresh_status.value,
                "auto_refresh_raw": auto_refresh_status,
                "auto_refresh_enabled": auto_refresh_enabled,
                "description": description,
                "size_mb": size_mb,
                "workspace": workspace,
                "row_count": random.randint(1000, 100000),
                "refresh_interval_hours": random.choice([1, 2, 6, 12, 24]),
                "has_errors": status == DatasetStatus.ERROR,
                "selected": False  # Для чекбоксов в UI
            }
            
            datasets.append(dataset)
        
        # Сортируем по имени для удобства
        datasets.sort(key=lambda x: x["name"])
        
        return datasets
    
    def refresh_dataset(self, workspace: str, dataset_id: str) -> Dict[str, Any]:
        """
        Обновить указанный датасет.
        
        Args:
            workspace: Название рабочей области
            dataset_id: ID датасета
            
        Returns:
            Словарь с результатом обновления
        """
        # Имитация задержки обновления
        time.sleep(random.uniform(1.0, 3.0))
        
        # Ищем датасет
        datasets = self.get_datasets_for_workspace(workspace)
        dataset = next((d for d in datasets if d["id"] == dataset_id), None)
        
        if not dataset:
            raise ValueError(f"Датасет {dataset_id} не найден в рабочей области {workspace}")
        
        # Обновляем дату последнего обновления
        dataset["last_update"] = datetime.now()
        dataset["last_update_str"] = dataset["last_update"].strftime("%Y-%m-%d %H:%M")
        
        # С вероятностью 10% имитируем ошибку обновления
        success = random.random() < 0.9
        
        result = {
            "success": success,
            "dataset_id": dataset_id,
            "dataset_name": dataset["name"],
            "timestamp": datetime.now().isoformat(),
            "new_status": "Completed" if success else "Failed",
            "message": "Обновление успешно завершено" if success else "Ошибка при обновлении данных",
            "duration_seconds": random.uniform(2.0, 10.0)
        }
        
        # Инвалидируем кэш
        with self._lock:
            if workspace in self._cache:
                del self._cache[workspace]
        
        return result
    
    def toggle_auto_refresh(self, workspace: str, dataset_id: str, enable: bool) -> Dict[str, Any]:
        """
        Включить/выключить автообновление для датасета.
        
        Args:
            workspace: Название рабочей области
            dataset_id: ID датасета
            enable: True - включить, False - выключить
            
        Returns:
            Словарь с результатом операции
        """
        # Имитация задержки
        time.sleep(random.uniform(0.5, 1.5))
        
        # Ищем датасет
        datasets = self.get_datasets_for_workspace(workspace)
        dataset = next((d for d in datasets if d["id"] == dataset_id), None)
        
        if not dataset:
            raise ValueError(f"Датасет {dataset_id} не найден в рабочей области {workspace}")
        
        # Обновляем статус
        new_status = AutoRefreshStatus.ENABLED if enable else AutoRefreshStatus.DISABLED
        
        result = {
            "success": True,
            "dataset_id": dataset_id,
            "dataset_name": dataset["name"],
            "auto_refresh_enabled": enable,
            "auto_refresh_status": new_status.value,
            "timestamp": datetime.now().isoformat(),
            "message": f"Автообновление {'включено' if enable else 'выключено'}"
        }
        
        # Инвалидируем кэш
        with self._lock:
            if workspace in self._cache:
                del self._cache[workspace]
        
        return result
    
    def batch_operation(self, workspace: str, dataset_ids: List[str], 
                       operation: str) -> Dict[str, Any]:
        """
        Выполнить пакетную операцию над несколькими датасетами.
        
        Args:
            workspace: Название рабочей области
            dataset_ids: Список ID датасетов
            operation: Тип операции ("refresh", "enable_auto", "disable_auto")
            
        Returns:
            Словарь с результатами операции
        """
        results = {
            "operation": operation,
            "workspace": workspace,
            "total": len(dataset_ids),
            "success": [],
            "failed": [],
            "start_time": datetime.now().isoformat()
        }
        
        for dataset_id in dataset_ids:
            try:
                if operation == "refresh":
                    result = self.refresh_dataset(workspace, dataset_id)
                elif operation == "enable_auto":
                    result = self.toggle_auto_refresh(workspace, dataset_id, True)
                elif operation == "disable_auto":
                    result = self.toggle_auto_refresh(workspace, dataset_id, False)
                else:
                    raise ValueError(f"Неизвестная операция: {operation}")
                
                results["success"].append({
                    "dataset_id": dataset_id,
                    "result": result
                })
                
            except Exception as e:
                results["failed"].append({
                    "dataset_id": dataset_id,
                    "error": str(e)
                })
        
        results["end_time"] = datetime.now().isoformat()
        results["success_count"] = len(results["success"])
        results["failed_count"] = len(results["failed"])
        
        # Инвалидируем кэш
        with self._lock:
            if workspace in self._cache:
                del self._cache[workspace]
        
        return results
    
    def get_dataset_statistics(self, workspace: str) -> Dict[str, Any]:
        """
        Получить статистику по датасетам в рабочей области.
        
        Args:
            workspace: Название рабочей области
            
        Returns:
            Словарь со статистикой
        """
        datasets = self.get_datasets_for_workspace(workspace)
        
        if not datasets:
            return {
                "total": 0,
                "active": 0,
                "inactive": 0,
                "with_errors": 0,
                "auto_refresh_enabled": 0,
                "total_size_mb": 0,
                "avg_size_mb": 0
            }
        
        total = len(datasets)
        active = sum(1 for d in datasets if d["status_raw"] == DatasetStatus.ACTIVE)
        inactive = sum(1 for d in datasets if d["status_raw"] == DatasetStatus.INACTIVE)
        with_errors = sum(1 for d in datasets if d["has_errors"])
        auto_refresh_enabled = sum(1 for d in datasets if d["auto_refresh_enabled"])
        total_size_mb = sum(d["size_mb"] for d in datasets)
        avg_size_mb = total_size_mb / total if total > 0 else 0
        
        # Самый старый и самый новый датасет
        if datasets:
            oldest = min(datasets, key=lambda x: x["last_update"])
            newest = max(datasets, key=lambda x: x["last_update"])
        else:
            oldest = newest = None
        
        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "with_errors": with_errors,
            "auto_refresh_enabled": auto_refresh_enabled,
            "total_size_mb": total_size_mb,
            "avg_size_mb": round(avg_size_mb, 2),
            "oldest_dataset": oldest["name"] if oldest else None,
            "oldest_update": oldest["last_update_str"] if oldest else None,
            "newest_dataset": newest["name"] if newest else None,
            "newest_update": newest["last_update_str"] if newest else None
        }
    
    def clear_cache(self, workspace: str = None):
        """
        Очистить кэш данных.
        
        Args:
            workspace: Если указана - очистить кэш только для этой области,
                      иначе очистить весь кэш
        """
        with self._lock:
            if workspace:
                if workspace in self._cache:
                    del self._cache[workspace]
                if workspace in self._cache_timestamp:
                    del self._cache_timestamp[workspace]
            else:
                self._cache.clear()
                self._cache_timestamp.clear()


# Функция для удобного доступа к провайдеру
def get_data_provider() -> DataProvider:
    """Получить экземпляр провайдера данных."""
    return DataProvider()


if __name__ == "__main__":
    # Тестирование провайдера данных
    provider = DataProvider()
    
    print("Тестирование DataProvider")
    print("=" * 60)
    
    for workspace in ["PROFISOFT", "Домен1", "Домен2", "Домен3"]:
        print(f"\nРабочая область: {workspace}")
        datasets = provider.get_datasets_for_workspace(workspace)
        print(f"Количество датасетов: {len(datasets)}")
        
        if datasets:
            sample = datasets[0]
            print(f"Пример датасета: {sample['name']}")
            print(f"  Статус: {sample['status']}")
            print(f"  Автообновление: {sample['auto_refresh']}")
            print(f"  Последнее обновление: {sample['last_update_str']}")
        
        stats = provider.get_dataset_statistics(workspace)
        print(f"Статистика: {stats['active']} активных, {stats['auto_refresh_enabled']} с автообновлением")
    
    # Тестирование обновления датасета
    print("\n" + "=" * 60)
    print("Тестирование обновления датасета")
    
    workspace = "PROFISOFT"
    datasets = provider.get_datasets_for_workspace(workspace)
    if datasets:
        dataset_id = datasets[0]["id"]
        print(f"Обновление датасета: {datasets[0]['name']}")
        
        try:
            result = provider.refresh_dataset(workspace, dataset_id)
            print(f"Результат: {result['success']} - {result['message']}")
        except Exception as e:
            print(f"Ошибка: {e}")
    
    print("\nТестирование завершено.")