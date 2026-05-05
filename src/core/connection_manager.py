#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер подключений (синглтон) для управления соединениями с источниками данных.
Обеспечивает единую точку подключения на весь сеанс приложения.
"""

import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import random


class ConnectionManager:
    """
    Синглтон-менеджер подключений.
    Управляет подключениями к различным источникам данных (фиктивные для демонстрации).
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Реализация синглтона с потокобезопасностью."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Инициализация менеджера подключений."""
        if getattr(self, '_initialized', False):
            return
        
        self._lock = threading.RLock()
        self._connections: Dict[str, Any] = {}
        self._active_workspace: str = "DefaultWorkspace"
        self._connection_status: Dict[str, bool] = {}
        self._last_activity: Dict[str, datetime] = {}
        self._initialized = True
        
        # Инициализируем фиктивные подключения
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Инициализация фиктивных подключений для демонстрации."""
        workspaces = ["DefaultWorkspace", "Workspace1", "Workspace2", "Workspace3"]
        
        with self._lock:
            for workspace in workspaces:
                self._connections[workspace] = {
                    "name": workspace,
                    "type": "PowerBI" if workspace == "DefaultWorkspace" else "SQL",
                    "host": f"server-{workspace.lower()}.example.com",
                    "port": 1433 if workspace != "DefaultWorkspace" else 443,
                    "connected": True,
                    "last_check": datetime.now(),
                    "latency_ms": random.randint(10, 100)
                }
                self._connection_status[workspace] = True
                self._last_activity[workspace] = datetime.now()
    
    def get_connection(self, workspace: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о подключении для указанной рабочей области.
        
        Args:
            workspace: Название рабочей области
            
        Returns:
            Словарь с информацией о подключении или None
        """
        with self._lock:
            if workspace in self._connections:
                # Обновляем время последней активности
                self._last_activity[workspace] = datetime.now()
                return self._connections[workspace].copy()
            return None
    
    def set_active_workspace(self, workspace: str) -> bool:
        """
        Установить активную рабочую область.
        
        Args:
            workspace: Название рабочей области
            
        Returns:
            True если область существует и подключена, иначе False
        """
        with self._lock:
            if workspace in self._connections:
                self._active_workspace = workspace
                return self._connection_status.get(workspace, False)
            return False
    
    def get_active_workspace(self) -> str:
        """Получить текущую активную рабочую область."""
        with self._lock:
            return self._active_workspace
    
    def get_available_workspaces(self) -> List[str]:
        """Получить список доступных рабочих областей."""
        with self._lock:
            return list(self._connections.keys())
    
    def get_connection_status(self, workspace: str = None) -> bool:
        """
        Получить статус подключения для рабочей области.
        
        Args:
            workspace: Название рабочей области (если None - активная)
            
        Returns:
            True если подключение активно, иначе False
        """
        with self._lock:
            if workspace is None:
                workspace = self._active_workspace
            
            if workspace in self._connection_status:
                # Для демонстрации иногда возвращаем случайный статус
                if random.random() < 0.05:  # 5% шанс на "потерю" соединения
                    return False
                return self._connection_status[workspace]
            return False
    
    def simulate_connection_loss(self, workspace: str):
        """
        Имитация потери соединения (для тестирования).
        
        Args:
            workspace: Название рабочей области
        """
        with self._lock:
            if workspace in self._connection_status:
                self._connection_status[workspace] = False
                self._connections[workspace]["connected"] = False
    
    def restore_connection(self, workspace: str):
        """
        Восстановить соединение.
        
        Args:
            workspace: Название рабочей области
        """
        with self._lock:
            if workspace in self._connection_status:
                self._connection_status[workspace] = True
                self._connections[workspace]["connected"] = True
                self._connections[workspace]["last_check"] = datetime.now()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по всем подключениям.
        
        Returns:
            Словарь со статистикой
        """
        with self._lock:
            stats = {
                "total_connections": len(self._connections),
                "active_connections": sum(1 for s in self._connection_status.values() if s),
                "inactive_connections": sum(1 for s in self._connection_status.values() if not s),
                "workspaces": {}
            }
            
            for workspace, conn in self._connections.items():
                stats["workspaces"][workspace] = {
                    "connected": self._connection_status.get(workspace, False),
                    "type": conn["type"],
                    "last_activity": self._last_activity.get(workspace, None),
                    "latency_ms": conn["latency_ms"]
                }
            
            return stats
    
    def execute_query(self, workspace: str, query: str) -> List[Dict[str, Any]]:
        """
        Выполнить фиктивный запрос к источнику данных.
        
        Args:
            workspace: Название рабочей области
            query: Текст запроса
            
        Returns:
            Список словарей с результатами
        """
        if not self.get_connection_status(workspace):
            raise ConnectionError(f"Нет подключения к рабочей области {workspace}")
        
        # Имитация задержки сети
        time.sleep(random.uniform(0.1, 0.5))
        
        # Фиктивные результаты для демонстрации
        return [
            {"query": query, "workspace": workspace, "timestamp": datetime.now().isoformat()},
            {"result": "success", "rows_affected": random.randint(1, 100)}
        ]
    
    def close_all_connections(self):
        """Закрыть все подключения."""
        with self._lock:
            for workspace in self._connection_status:
                self._connection_status[workspace] = False
                self._connections[workspace]["connected"] = False
    
    def __str__(self) -> str:
        """Строковое представление менеджера подключений."""
        stats = self.get_connection_stats()
        return (f"ConnectionManager: {stats['active_connections']}/"
                f"{stats['total_connections']} активных подключений, "
                f"активная область: {self._active_workspace}")


# Функция для удобного доступа к менеджеру
def get_connection_manager() -> ConnectionManager:
    """Получить экземпляр менеджера подключений."""
    return ConnectionManager()


if __name__ == "__main__":
    # Тестирование менеджера подключений
    cm1 = ConnectionManager()
    cm2 = ConnectionManager()
    
    print(f"Один и тот же экземпляр? {cm1 is cm2}")
    print(f"Доступные области: {cm1.get_available_workspaces()}")
    print(f"Активная область: {cm1.get_active_workspace()}")
    
    # Смена активной области
    cm1.set_active_workspace("Домен1")
    print(f"Новая активная область: {cm1.get_active_workspace()}")
    
    # Получение статистики
    stats = cm1.get_connection_stats()
    print(f"Статистика: {stats}")
    
    # Выполнение запроса
    try:
        results = cm1.execute_query("Домен1", "SELECT * FROM datasets")
        print(f"Результаты запроса: {results}")
    except ConnectionError as e:
        print(f"Ошибка подключения: {e}")