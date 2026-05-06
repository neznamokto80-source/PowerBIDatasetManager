#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с Power BI API.
Содержит функции для аутентификации, получения данных и управления ресурсами.
"""

import logging
import os
import json
import requests
from datetime import datetime
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
    
    def __init__(self, use_session: bool = True, debug_data_path: Optional[str] = None):
        """
        Инициализация клиента Power BI.

        Args:
            use_session: Использовать сессию requests для повторного использования соединений
            debug_data_path: Путь для сохранения сырых данных (если None, сохранение отключено)
        """
        self.token: Optional[str] = None
        self.session = requests.Session() if use_session else requests
        self._auth_method: Optional[str] = None
        self.debug_data_path = debug_data_path
        if self.debug_data_path:
            os.makedirs(self.debug_data_path, exist_ok=True)

    def _save_raw_data(self, url: str, method: str, data: Union[Dict, List], status_code: int):
        """
        Сохраняет сырые данные ответа в файл для отладки.
        Организует файлы по рабочим областям и датасетам для удобства тестирования.

        Args:
            url: URL запроса
            method: HTTP метод
            data: Данные ответа (словарь или список)
            status_code: Код статуса HTTP
        """
        if not self.debug_data_path:
            return

        # Извлекаем идентификаторы из URL
        workspace_id = None
        dataset_id = None
        
        # Паттерны для извлечения workspace_id и dataset_id из URL Power BI API
        # Пример: /groups/{workspace_id}/datasets/{dataset_id}/...
        import re
        pattern_workspace = r'/groups/([a-zA-Z0-9\-]+)'
        pattern_dataset = r'/datasets/([a-zA-Z0-9\-]+)'
        
        match_ws = re.search(pattern_workspace, url)
        if match_ws:
            workspace_id = match_ws.group(1)
        
        match_ds = re.search(pattern_dataset, url)
        if match_ds:
            dataset_id = match_ds.group(1)
        
        # Определяем тип endpoint (последний сегмент пути)
        endpoint = url.replace(self.POWER_BI_API_BASE, "").strip("/")
        if not endpoint:
            endpoint = "root"
        # Безопасное имя для файла
        safe_endpoint = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in endpoint)
        
        # Извлекаем название датасета из данных (если доступно)
        dataset_name = None
        if isinstance(data, dict) and 'name' in data:
            dataset_name = data.get('name')
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'name' in data[0]:
            # Если это список датасетов, используем имя первого (или общее)
            dataset_name = "datasets_list"
        
        # Безопасное имя датасета (замена недопустимых символов)
        if dataset_name:
            # Ограничим длину и заменим пробелы и спецсимволы
            safe_name = re.sub(r'[^\w\-]', '_', dataset_name)[:50]
        else:
            safe_name = dataset_id if dataset_id else "unknown"
        
        # Дата и время в формате ГГГГММДД_ЧЧММСС
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Микросекунды для уникальности
        micro = datetime.now().strftime("%f")
        
        # Собираем компоненты имени файла
        components = [timestamp]
        if safe_name:
            components.append(safe_name)
        components.append(method)
        components.append(safe_endpoint)
        
        filename = "_".join(components) + f"_{micro}.json"
        filepath = os.path.join(self.debug_data_path, filename)
        
        # Убедимся, что директория существует
        os.makedirs(self.debug_data_path, exist_ok=True)
        
        payload = {
            "url": url,
            "method": method,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
            "workspace_id": workspace_id,
            "dataset_id": dataset_id,
            "data": data
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.debug(f"Сырые данные сохранены в {filepath}")
        except Exception as e:
            logger.warning(f"Не удалось сохранить сырые данные: {e}")
    
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
        if body is not None:
            logger.debug(f"Тело запроса: {body}")
        
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
            raise APIRequestError(f"Ошибка сети при запросе к {url}: {e}", status_code=None) from e
        
        if response.status_code not in self.SUCCESS_STATUS_CODES:
            raise APIRequestError(
                f"Ошибка {response.status_code} при запросе к {url}: {response.text}",
                status_code=response.status_code
            )
        
        # Для DELETE без содержимого
        if response.status_code == 204:
            return {}
        
        # Логируем тело ответа для отладки
        logger.debug(f"Ответ от {url}: статус {response.status_code}, тело: {response.text[:500]}")
        
        # Если тело ответа пустое (например, успешный PATCH возвращает пустой ответ)
        if not response.text.strip():
            return {}
        
        try:
            data = response.json()
            if self.debug_data_path:
                self._save_raw_data(url, method, data, response.status_code)
            return data
        except ValueError as e:
            raise APIRequestError(f"Не удалось разобрать JSON ответ от {url}: {e}", status_code=response.status_code) from e
    
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


class APIRequestError(Exception):
    """Исключение для ошибок запросов к API."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ResourceNotFoundError(Exception):
    """Исключение для случаев, когда ресурс не найден."""


def parse_utc_to_local(utc_str: str, fmt: str = "%d-%m-%Y %H:%M:%S") -> str:
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