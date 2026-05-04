#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с Power BI API.
Содержит функции для аутентификации, получения данных и управления ресурсами.
"""

import logging
import requests
from azure.identity import InteractiveBrowserCredential, AzureCliCredential
import dateutil.parser
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger(__name__)


class PowerBIClient:
    """Клиент для работы с Power BI API."""
    
    # Константы API
    POWER_BI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
    POWER_BI_API_BASE = "https://api.powerbi.com/v1.0/myorg"
    
    # Коды успешных HTTP статусов
    SUCCESS_STATUS_CODES = {200, 201, 202, 204}
    
    def __init__(self, use_session: bool = True):
        """
        Инициализация клиента Power BI.
        
        Args:
            use_session: Использовать сессию requests для повторного использования соединений
        """
        self.token: Optional[str] = None
        self.session = requests.Session() if use_session else requests
        self._auth_method: Optional[str] = None
    
    def authenticate(self) -> str:
        """
        Получение токена доступа для Power BI Service.
        
        Returns:
            Токен доступа (строка)
        
        Raises:
            AuthenticationError: Если не удалось получить токен
        """
        auth_methods = [
            ("Azure CLI", AzureCliCredential),
            ("Interactive Browser", InteractiveBrowserCredential),
        ]
        
        for method_name, credential_class in auth_methods:
            try:
                credential = credential_class()
                token = credential.get_token(*self.POWER_BI_SCOPE)
                self.token = token.token
                self._auth_method = method_name
                logger.info(f"Аутентификация через {method_name} успешна.")
                return self.token
            except Exception as e:
                logger.debug(f"Аутентификация через {method_name} не удалась: {e}")
                continue
        
        raise AuthenticationError(
            "Не удалось получить токен. Убедитесь, что у вас есть доступ к Power BI и вы выполнили вход."
        )
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Возвращает текущий токен, при необходимости выполняет аутентификацию.
        
        Args:
            force_refresh: Принудительно обновить токен
        
        Returns:
            Токен доступа
        """
        if force_refresh or not self.token:
            return self.authenticate()
        return self.token
    
    def make_request(
        self,
        url: str,
        method: str = "GET",
        body: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 30
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Универсальная функция для запросов к Power BI API.
        
        Args:
            url: Полный URL для запроса
            method: HTTP метод (GET, POST, PATCH, DELETE)
            body: Тело запроса (для POST/PATCH)
            params: Параметры запроса
            timeout: Таймаут запроса в секундах
        
        Returns:
            Ответ API в виде словаря или списка
        
        Raises:
            APIRequestError: При ошибке HTTP запроса
        """
        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Выполнение запроса {method} {url}")
        
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                json=body,
                params=params,
                timeout=timeout
            )
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Ошибка сети при запросе к {url}: {e}") from e
        
        if response.status_code not in self.SUCCESS_STATUS_CODES:
            raise APIRequestError(
                f"Ошибка {response.status_code} при запросе к {url}: {response.text}"
            )
        
        # Для DELETE без содержимого
        if response.status_code == 204:
            return {}
        
        try:
            return response.json()
        except ValueError as e:
            raise APIRequestError(f"Не удалось разобрать JSON ответ от {url}: {e}") from e
    
    def get_workspace_by_name(self, workspace_name: str) -> Dict[str, Any]:
        """
        Находит рабочую область по имени (без учёта регистра).
        
        Args:
            workspace_name: Имя рабочей области
        
        Returns:
            Информация о рабочей области
        
        Raises:
            ResourceNotFoundError: Если рабочая область не найдена
        """
        url = f"{self.POWER_BI_API_BASE}/groups"
        data = self.make_request(url)
        groups = data.get("value", [])
        
        for group in groups:
            if group.get("name", "").lower() == workspace_name.lower():
                return group
        
        raise ResourceNotFoundError(f"Рабочая область с именем '{workspace_name}' не найдена.")
    
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
            excluded_names = ["Usage Metrics Model"]
        
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
    
    def get_all_refreshes(
        self,
        workspace_id: str,
        dataset_id: str,
        top: int = 10
    ) -> List[Dict[str, Any]]:
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
    
    def get_auth_method(self) -> Optional[str]:
        """Возвращает метод аутентификации, который был использован."""
        return self._auth_method


class AuthenticationError(Exception):
    """Исключение для ошибок аутентификации."""
    pass


class APIRequestError(Exception):
    """Исключение для ошибок запросов к API."""
    pass


class ResourceNotFoundError(Exception):
    """Исключение для случаев, когда ресурс не найден."""
    pass


def parse_utc_to_local(utc_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Преобразует строку UTC в локальное время.
    
    Args:
        utc_str: Строка времени в формате UTC
        fmt: Формат вывода времени
    
    Returns:
        Строка времени в локальном формате или "—" при ошибке
    """
    try:
        utc_time = dateutil.parser.isoparse(utc_str)
        local_time = utc_time.astimezone()
        return local_time.strftime(fmt)
    except Exception as e:
        logger.debug(f"Ошибка преобразования времени '{utc_str}': {e}")
        return "—"


if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    print("Тестирование модуля Power BI Client...")
    client = PowerBIClient()
    
    try:
        token = client.authenticate()
        print(f"Токен получен (первые 20 символов): {token[:20]}...")
        print(f"Метод аутентификации: {client.get_auth_method()}")
        
        workspaces = client.get_workspaces()
        print(f"Найдено рабочих областей: {len(workspaces)}")
        
        if workspaces:
            sample_workspace = workspaces[0]
            print(f"Пример рабочей области: {sample_workspace.get('name')} (ID: {sample_workspace.get('id')})")
        
        print("Тест завершен успешно.")
    except Exception as e:
        print(f"Ошибка тестирования: {e}")