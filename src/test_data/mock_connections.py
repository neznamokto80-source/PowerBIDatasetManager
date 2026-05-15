#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фиктивные данные для тестирования и демонстрации.
Содержит мок-подключения и демо-датасеты.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


# ========== Фиктивные подключения ==========

def get_mock_connections() -> Dict[str, Dict[str, Any]]:
    """
    Возвращает словарь фиктивных подключений к рабочим областям.
    Используется в connection_manager.py для демонстрации.
    """
    workspaces = ["DefaultWorkspace", "Workspace1", "Workspace2", "Workspace3"]
    connections = {}
    for workspace in workspaces:
        connections[workspace] = {
            "name": workspace,
            "type": "PowerBI" if workspace == "DefaultWorkspace" else "SQL",
            "host": f"server-{workspace.lower()}.example.com",
            "port": 1433 if workspace != "DefaultWorkspace" else 443,
            "connected": True,
            "last_check": datetime.now(),
            "latency_ms": random.randint(10, 100)
        }
    return connections


def get_mock_workspaces() -> List[str]:
    """Возвращает список доступных рабочих областей."""
    return ["DefaultWorkspace", "Workspace1", "Workspace2", "Workspace3"]


# ========== Демо-датасеты ==========

def get_demo_datasets(workspace: str = "DefaultWorkspace") -> List[Dict[str, Any]]:
    """
    Возвращает фиксированные демо-датасеты для скриншотов.
    Соответствует данным из data_provider._generate_demo_datasets.
    """
    if workspace != "DefaultWorkspace":
        return []
    
    from datetime import datetime, timedelta
    
    demo_datasets = [
        {
            "id": "dataset-default-001",
            "name": "Sales Dashboard",
            "status": "Активен",
            "last_update": datetime.now() - timedelta(hours=2),
            "last_update_str": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "lastRefreshTime": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "auto_refresh": "Вкл",
            "auto_refresh_enabled": True,
            "refresh_schedule": {
                "enabled": True,
                "times": ["09:00", "18:00"],
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            },
            "isRefreshable": True,
            "nextRefreshTime": "",
            "description": "Основной дашборд продаж с детализацией по регионам",
            "size_mb": 250,
            "workspace": workspace,
            "row_count": 50000,
            "refresh_interval_hours": 12,
            "has_errors": False,
            "selected": False
        },
        {
            "id": "dataset-default-002",
            "name": "Financial Reports",
            "status": "Активен",
            "last_update": datetime.now() - timedelta(days=1),
            "last_update_str": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "lastRefreshTime": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "auto_refresh": "Вкл",
            "auto_refresh_enabled": True,
            "refresh_schedule": {
                "enabled": True,
                "times": [],
                "days": []
            },
            "isRefreshable": True,
            "nextRefreshTime": "",
            "description": "Финансовая отчетность и анализ прибыльности",
            "size_mb": 180,
            "workspace": workspace,
            "row_count": 30000,
            "refresh_interval_hours": 24,
            "has_errors": False,
            "selected": False
        },
        {
            "id": "dataset-default-003",
            "name": "Marketing Analytics",
            "status": "Активен",
            "last_update": datetime.now() - timedelta(days=3),
            "last_update_str": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "lastRefreshTime": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "auto_refresh": "Выкл",
            "auto_refresh_enabled": False,
            "refresh_schedule": {
                "enabled": False,
                "times": [],
                "days": []
            },
            "isRefreshable": False,
            "nextRefreshTime": "",
            "description": "Аналитика маркетинговых кампаний и ROI",
            "size_mb": 320,
            "workspace": workspace,
            "row_count": 75000,
            "refresh_interval_hours": 6,
            "has_errors": False,
            "selected": False
        },
        {
            "id": "dataset-default-004",
            "name": "Customer Insights",
            "status": "Неактивен",
            "last_update": datetime.now() - timedelta(days=10),
            "last_update_str": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
            "lastRefreshTime": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
            "auto_refresh": "Выкл",
            "auto_refresh_enabled": False,
            "refresh_schedule": {
                "enabled": False,
                "times": [],
                "days": []
            },
            "isRefreshable": False,
            "nextRefreshTime": "",
            "description": "Инсайты по клиентскому поведению и удержанию",
            "size_mb": 150,
            "workspace": workspace,
            "row_count": 20000,
            "refresh_interval_hours": 1,
            "has_errors": False,
            "selected": False
        },
        {
            "id": "dataset-default-005",
            "name": "Inventory Management",
            "status": "Ошибка",
            "last_update": datetime.now() - timedelta(days=15),
            "last_update_str": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d %H:%M"),
            "lastRefreshTime": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d %H:%M"),
            "auto_refresh": "Выкл",
            "auto_refresh_enabled": False,
            "refresh_schedule": {
                "enabled": False,
                "times": [],
                "days": []
            },
            "isRefreshable": False,
            "nextRefreshTime": "",
            "description": "Управление запасами и оптимизация складских остатков",
            "size_mb": 420,
            "workspace": workspace,
            "row_count": 100000,
            "refresh_interval_hours": 2,
            "has_errors": True,
            "selected": False
        }
    ]
    return demo_datasets


def get_random_datasets(workspace: str, count: int = 8) -> List[Dict[str, Any]]:
    """
    Генерирует случайные датасеты для тестирования.
    Используется в data_provider для не-демо режима.
    """
    dataset_names = [
        "Sales Dashboard", "Financial Reports", "Marketing Analytics",
        "Customer Insights", "Inventory Management", "HR Analytics",
        "Supply Chain", "Product Performance", "Web Analytics",
        "Social Media Metrics", "Operational Efficiency", "Quality Control",
        "Risk Assessment", "Budget Planning", "Forecast Models"
    ]
    
    descriptions = [
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
    
    datasets = []
    used_names = set()
    
    for i in range(count):
        base_name = random.choice(dataset_names)
        suffix = f" {workspace}" if random.random() < 0.3 else ""
        name = f"{base_name}{suffix}"
        
        if name in used_names:
            name = f"{base_name} {i+1}{suffix}"
        used_names.add(name)
        
        is_active = random.random() < 0.8
        status = "Активен" if is_active else "Неактивен"
        if not is_active and random.random() < 0.2:
            status = "Ошибка"
        
        auto_refresh_enabled = random.random() < (0.7 if is_active else 0.3)
        refresh_schedule = {}
        if auto_refresh_enabled:
            refresh_schedule['enabled'] = True
            if random.random() < 0.5:
                refresh_schedule['times'] = ["09:00", "18:00"]
                refresh_schedule['days'] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            else:
                refresh_schedule['times'] = []
                refresh_schedule['days'] = []
        else:
            refresh_schedule['enabled'] = False
            refresh_schedule['times'] = []
            refresh_schedule['days'] = []
        
        days_ago = random.randint(0, 30)
        last_update = datetime.now() - timedelta(days=days_ago,
                                                hours=random.randint(0, 23),
                                                minutes=random.randint(0, 59))
        
        dataset = {
            "id": f"dataset-{workspace.lower()}-{i:03d}",
            "name": name,
            "status": status,
            "last_update": last_update,
            "last_update_str": last_update.strftime("%Y-%m-%d %H:%M"),
            "lastRefreshTime": last_update.strftime("%Y-%m-%d %H:%M"),
            "auto_refresh": "Вкл" if auto_refresh_enabled else "Выкл",
            "auto_refresh_enabled": auto_refresh_enabled,
            "refresh_schedule": refresh_schedule,
            "isRefreshable": auto_refresh_enabled,
            "nextRefreshTime": "",
            "description": random.choice(descriptions),
            "size_mb": random.randint(10, 1000),
            "workspace": workspace,
            "row_count": random.randint(1000, 100000),
            "refresh_interval_hours": random.choice([1, 2, 6, 12, 24]),
            "has_errors": status == "Ошибка",
            "selected": False
        }
        datasets.append(dataset)
    
    datasets.sort(key=lambda x: x["name"])
    return datasets


# ========== Утилиты для тестирования ==========

def get_mock_connection_stats() -> Dict[str, Any]:
    """Возвращает фиктивную статистику подключений."""
    return {
        "total_connections": 4,
        "active_connections": 3,
        "inactive_connections": 1,
        "workspaces": {
            "DefaultWorkspace": {
                "connected": True,
                "type": "PowerBI",
                "last_activity": datetime.now(),
                "latency_ms": 45
            },
            "Workspace1": {
                "connected": True,
                "type": "SQL",
                "last_activity": datetime.now() - timedelta(minutes=5),
                "latency_ms": 78
            },
            "Workspace2": {
                "connected": True,
                "type": "SQL",
                "last_activity": datetime.now() - timedelta(minutes=10),
                "latency_ms": 92
            },
            "Workspace3": {
                "connected": False,
                "type": "SQL",
                "last_activity": datetime.now() - timedelta(hours=1),
                "latency_ms": 120
            }
        }
    }