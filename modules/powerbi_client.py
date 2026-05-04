#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с Power BI API.
Содержит функции для аутентификации, получения данных и управления ресурсами.
"""

import requests
from azure.identity import InteractiveBrowserCredential, AzureCliCredential
from datetime import datetime
import dateutil.parser
from typing import Optional, Dict, Any, List


class PowerBIClient:
    """Клиент для работы с Power BI API."""
    
    # Константы
    POWER_BI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
    POWER_BI_API_BASE = "https://api.powerbi.com/v1.0/myorg"
    
    def __init__(self):
        """Инициализация клиента Power BI."""
        self.token = None
        self.session = requests.Session()
    
    def authenticate(self) -> str:
        """
        Получение токена доступа для Power BI Service.
        
        Returns:
            Токен доступа (строка)
        
        Raises:
            Exception: Если не удалось получить токен
        """
        try:
            # Попытка использовать учётные данные из Azure CLI (удобно для CI/CD)
            credential = AzureCliCredential()
            token = credential.get_token(*self.POWER_BI_SCOPE)
            print("✓ Аутентификация через Azure CLI успешна.")
            self.token = token.token
            return self.token
        except Exception as cli_error:
            print("Не удалось использовать Azure CLI, переходим к интерактивному входу...")
            try:
                # Интерактивный вход через браузер
                credential = InteractiveBrowserCredential()
                token = credential.get_token(*self.POWER_BI_SCOPE)
                print("✓ Интерактивная аутентификация успешна.")
                self.token = token.token
                return self.token
            except Exception as interactive_error:
                raise Exception(
                    "Не удалось получить токен. Убедитесь, что у вас есть доступ к Power BI и вы выполнили вход."
                ) from interactive_error
    
    def get_token(self) -> str:
        """Возвращает текущий токен, при необходимости выполняет аутентификацию."""
        if not self.token:
            return self.authenticate()
        return self.token
    
    def make_request(
        self, 
        url: str, 
        method: str = "GET", 
        body: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Универсальная функция для запросов к Power BI API.
        
        Args:
            url: Полный URL для запроса
            method: HTTP метод (GET, POST, PATCH, DELETE)
            body: Тело запроса (для POST/PATCH)
        
        Returns:
            Ответ API в виде словаря
        
        Raises:
            Exception: При ошибке HTTP запроса
        """
        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = self.session.request(method, url, headers=headers, json=body)
        
        if response.status_code not in (200, 201, 202, 204):
            raise Exception(f"Ошибка {response.status_code}: {response.text}")
        
        # Для DELETE без содержимого
        if response.status_code == 204:
            return {}
        
        return response.json()
    
    def get_workspace_by_name(self, workspace_name: str) -> Dict[str, Any]:
        """
        Находит рабочую область по имени (без учёта регистра).
        
        Args:
            workspace_name: Имя рабочей области
        
        Returns:
            Информация о рабочей области
        
        Raises:
            Exception: Если рабочая область не найдена
        """
        url = f"{self.POWER_BI_API_BASE}/groups"
        data = self.make_request(url)
        groups = data.get("value", [])
        
        for group in groups:
            if group.get("name", "").lower() == workspace_name.lower():
                return group
        
        raise Exception(f"Рабочая область с именем '{workspace_name}' не найдена.")
    
    def get_datasets_in_workspace(
        self, 
        workspace_id: str, 
        excluded_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Возвращает список датасетов в рабочей области.
        
        Args:
            workspace_id: ID рабочей области
            excluded_names: Список имён для исключения
        
        Returns:
            Список датасетов
        """
        if excluded_names is None:
            excluded_names = ["not_use", "Usage Metrics Model"]
        
        url = f"{self.POWER_BI_API_BASE}/groups/{workspace_id}/datasets"
        data = self.make_request(url)
        all_datasets = data.get("value", [])
        
        filtered = []
        for ds in all_datasets:
            name = ds.get("name", "")
            # Исключаем датасеты, содержащие подстроки из excluded_names
            if any(excl in name for excl in excluded_names):
                continue
            filtered.append(ds)
        
        return filtered
    
    def get_refresh_schedule(self, workspace_id: str, dataset_id: str) -> Dict[str, Any]:
        """
        Получает настройки расписания обновлений датасета.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
        
        Returns:
            Настройки расписания
        """
        url = f"{self.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule"
        return self.make_request(url)
    
    def get_last_refresh(self, workspace_id: str, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию о последнем обновлении (top=1).
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
        
        Returns:
            Информация о последнем обновлении или None
        """
        url = f"{self.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top=1"
        data = self.make_request(url)
        refreshes = data.get("value", [])
        
        if refreshes:
            return refreshes[0]
        return None
    
    def get_all_refreshes(self, workspace_id: str, dataset_id: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Возвращает список последних обновлений датасета.
        
        Args:
            workspace_id: ID рабочей области
            dataset_id: ID датасета
            top: Количество записей для получения
        
        Returns:
            Список обновлений
        """
        url = f"{self.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top={top}"
        data = self.make_request(url)
        return data.get("value", [])
    
    def get_workspaces(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех рабочих областей.
        
        Returns:
            Список рабочих областей
        """
        url = f"{self.POWER_BI_API_BASE}/groups"
        data = self.make_request(url)
        return data.get("value", [])


def parse_utc_to_local(utc_str: str) -> str:
    """
    Преобразует строку UTC в локальное время (формат YYYY-MM-DD HH:MM:SS).
    
    Args:
        utc_str: Строка времени в формате UTC
    
    Returns:
        Строка времени в локальном формате или "—" при ошибке
    """
    try:
        utc_time = dateutil.parser.isoparse(utc_str)
        local_time = utc_time.astimezone()
        return local_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "—"


if __name__ == "__main__":
    # Тестирование модуля
    print("Тестирование модуля Power BI Client...")
    client = PowerBIClient()
    
    try:
        token = client.authenticate()
        print(f"Токен получен (первые 20 символов): {token[:20]}...")
        
        workspaces = client.get_workspaces()
        print(f"Найдено рабочих областей: {len(workspaces)}")
        
        if workspaces:
            sample_workspace = workspaces[0]
            print(f"Пример рабочей области: {sample_workspace.get('name')} (ID: {sample_workspace.get('id')})")
        
        print("Тест завершен успешно.")
    except Exception as e:
        print(f"Ошибка тестирования: {e}")