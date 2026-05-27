#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с Power BI Report Server API.
Содержит функции для аутентификации через NTLM, получения данных и управления ресурсами.
"""

import logging
import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class PowerBIReportServerClient:
    """Клиент для работы с Power BI Report Server API."""
    
    # Коды успешных HTTP статусов
    SUCCESS_STATUS_CODES = {200, 201, 202, 204}
    
    def __init__(self, server_url: str, username: str = None, password: str = None, 
                 use_session: bool = True, debug_data_path: Optional[str] = None):
        """
        Инициализация клиента Power BI Report Server.

        Args:
            server_url: Базовый URL сервера (например, http://PBIRSServer/Reports)
            username: Имя пользователя для NTLM аутентификации (опционально, используется текущий пользователь Windows)
            password: Пароль для NTLM аутентификации
            use_session: Использовать сессию requests для повторного использования соединений
            debug_data_path: Путь для сохранения сырых данных (если None, сохранение отключено)
        """
        # Убираем завершающий слэш если есть
        server_url = server_url.rstrip('/')
        self.base_url = f"{server_url}/api/v2.0"
        
        # Инициализация аутентификации
        self.auth = None
        try:
            from requests_ntlm import HttpNtlmAuth
            
            if username and password:
                self.auth = HttpNtlmAuth(username, password)
                logger.info("Используется NTLM аутентификация с указанными учетными данными")
            else:
                # Используем аутентификацию с пустыми учетными данными (текущий контекст Windows)
                self.auth = HttpNtlmAuth('', '')
                logger.info("Используется NTLM аутентификация с текущим пользователем Windows (пустые учетные данные)")
                    
        except ImportError:
            logger.warning("Библиотека requests_ntlm не установлена. Установите: pip install requests_ntlm")
            raise ImportError("Для работы с Power BI Report Server требуется библиотека requests_ntlm")
        
        self.session = requests.Session() if use_session else requests
        self.debug_data_path = debug_data_path
        if self.debug_data_path:
            os.makedirs(self.debug_data_path, exist_ok=True)
    
    def _save_raw_data(self, url: str, method: str, data: Union[Dict, List], status_code: int):
        """
        Сохраняет сырые данные ответа в файл для отладки.
        """
        if not self.debug_data_path:
            return
        
        logger.info("Сохранение сырых данных для %s %s (статус: %d)", method, url, status_code)
        
        # Извлекаем идентификаторы из URL
        report_id = None
        import re
        pattern_report = r'/PowerBIReports\(([^)]+)\)'
        match_report = re.search(pattern_report, url)
        if match_report:
            report_id = match_report.group(1)
        
        # Определяем тип endpoint
        endpoint = url.replace(self.base_url, "").strip("/")
        if not endpoint:
            endpoint = "root"
        # Безопасное имя для файла
        safe_endpoint = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in endpoint)
        
        # Дата и время в формате ГГГГММДД_ЧЧММСС
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        micro = datetime.now().strftime("%f")
        
        # Собираем компоненты имени файла
        components = [timestamp, safe_endpoint, method]
        if report_id:
            components.append(report_id[:20])
        
        filename = "_".join(components) + f"_{micro}.json"
        
        # Создаем абсолютный путь
        import os
        debug_dir = os.path.abspath(self.debug_data_path)
        filepath = os.path.join(debug_dir, filename)
        
        # Убедимся, что директория существует
        os.makedirs(debug_dir, exist_ok=True)
        
        payload = {
            "url": url,
            "method": method,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
            "report_id": report_id,
            "data": data
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info("Сырые данные сохранены в %s", filepath)
        except Exception as e:
            logger.error("Не удалось сохранить сырые данные в %s: %s", filepath, str(e))
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 30
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Универсальная функция для запросов к Power BI Report Server API.
        
        Args:
            endpoint: Конечная точка API (например, "PowerBIReports")
            method: HTTP метод (GET, POST, PATCH, DELETE)
            data: Тело запроса (для POST/PATCH)
            params: Параметры запроса
            timeout: Таймаут запроса в секундах
        
        Returns:
            Ответ API в виде словаря или списка
        """
        url = f"{self.base_url}/{endpoint}"
        
        logger.debug(f"Выполнение запроса {method} {url}")
        if data is not None:
            logger.debug(f"Тело запроса: {data}")
        
        try:
            response = self.session.request(
                method,
                url,
                auth=self.auth,
                json=data,
                params=params,
                timeout=timeout,
                headers={"Content-Type": "application/json"} if data else {}
            )
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Ошибка сети при запросе к {url}: {e}", status_code=None) from e
        
        if response.status_code not in self.SUCCESS_STATUS_CODES:
            raise APIRequestError(
                f"Ошибка {response.status_code} при запросе к {url}: {response.text}",
                status_code=response.status_code
            )
        
        # Для DELETE без содержимого (статус 204)
        if response.status_code == 204:
            if self.debug_data_path:
                self._save_raw_data(url, method, {"status": "204 No Content"}, response.status_code)
            return {}
        
        # Логируем тело ответа для отладки
        logger.debug(f"Ответ от {url}: статус {response.status_code}, тело: {response.text[:500]}")
        
        # Если тело ответа пустое
        if not response.text.strip():
            if self.debug_data_path:
                self._save_raw_data(url, method, {"status": "Empty response"}, response.status_code)
            return {}
        
        try:
            result = response.json()
            if self.debug_data_path:
                self._save_raw_data(url, method, result, response.status_code)
            return result
        except ValueError as e:
            # Если JSON невалидный, но есть текст ответа
            if self.debug_data_path:
                self._save_raw_data(url, method, {"raw_text": response.text, "error": str(e)}, response.status_code)
            raise APIRequestError(f"Не удалось разобрать JSON ответ от {url}: {e}", status_code=response.status_code) from e
    
    def get_powerbi_reports(self) -> List[Dict[str, Any]]:
        """
        Получает список всех Power BI отчетов (включая их датасеты).
        
        Returns:
            Список отчетов Power BI
        """
        try:
            data = self._make_request("PowerBIReports")
            return data.get("value", [])
        except Exception as e:
            logger.error(f"Ошибка при получении списка отчетов: {e}")
            return []
    
    def get_extended_reports(self, include_ssrs: bool = True) -> List[Dict[str, Any]]:
        """
        Получает расширенные данные отчетов с источниками данных и расписаниями.
        Адаптировано из предоставленного скрипта.
        
        Args:
            include_ssrs: Включать ли SSRS отчеты (тип "Reports")
        
        Returns:
            Список отчетов с расширенными данными
        """
        try:
            # Функция для получения CacheRefreshPlans с историей
            def get_cache_refresh_plans_for_report(report_type: str, report_id: str):
                """Запрашивает CacheRefreshPlans для конкретного отчёта."""
                try:
                    # Получаем планы обновления кэша
                    plans_data = self._make_request(f"{report_type}({report_id})/CacheRefreshPlans")
                    plans = plans_data.get("value", [])
                    
                    # Для каждого плана загружаем историю
                    for plan in plans:
                        plan_id = plan.get("Id")
                        if plan_id:
                            try:
                                history_data = self._make_request(f"CacheRefreshPlans({plan_id})/History")
                                plan["History"] = history_data.get("value", [])
                            except Exception:
                                plan["History"] = []
                    return plans
                except Exception as e:
                    logger.debug(f"Ошибка получения CacheRefreshPlans для {report_type}/{report_id}: {e}")
                    return []
            
            all_items = []
            
            # Типы отчетов для загрузки
            report_types = ["PowerBIReports"]
            if include_ssrs:
                report_types.append("Reports")
            
            for report_type in report_types:
                try:
                    # Получаем отчеты с расширенными данными (DataSources)
                    params = {
                        "$select": "Id,Name,Path,CreatedBy,Description,Size,Type",
                        "$expand": "DataSources",
                        "$format": "json"
                    }
                    
                    # Используем существующий метод _make_request с параметрами
                    data = self._make_request(report_type, params=params)
                    items = data.get("value", [])
                    
                    # Для каждого отчёта загружаем расписания
                    for item in items:
                        report_id = item.get("Id")
                        if report_id:
                            plans = get_cache_refresh_plans_for_report(report_type, report_id)
                            item["CacheRefreshPlans"] = plans
                        else:
                            item["CacheRefreshPlans"] = []
                        
                        # Добавляем тип отчета для идентификации
                        item["ReportType"] = "PowerBIReport" if report_type == "PowerBIReports" else "SSRSReport"
                    
                    all_items.extend(items)
                    
                except Exception as e:
                    logger.warning(f"Ошибка при загрузке отчетов типа {report_type}: {e}")
                    # Продолжаем с другим типом отчетов
            
            logger.info(f"Загружено расширенных отчетов: {len(all_items)}")
            return all_items
            
        except Exception as e:
            logger.error(f"Ошибка при получении расширенных данных отчетов: {e}")
            # Fallback на обычный метод
            return self.get_powerbi_reports()
    
    def get_cache_refresh_plans(self, report_id: str) -> List[Dict[str, Any]]:
        """
        Возвращает список планов обновления кэша для отчета.
        
        Args:
            report_id: ID отчета
        
        Returns:
            Список планов обновления кэша
        """
        try:
            data = self._make_request(f"PowerBIReports({report_id})/CacheRefreshPlans")
            return data.get("value", [])
        except Exception as e:
            logger.error(f"Ошибка при получении планов обновления кэша для отчета {report_id}: {e}")
            return []
    
    def execute_cache_refresh_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Немедленно запускает план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
        
        Returns:
            Результат выполнения
        """
        try:
            return self._make_request(f"CacheRefreshPlans({plan_id})/Model.Execute", method="POST")
        except Exception as e:
            logger.error(f"Ошибка при выполнении плана обновления кэша {plan_id}: {e}")
            raise
    
    def create_cache_refresh_plan(self, report_id: str, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает новый план обновления кэша для отчета.
        
        Args:
            report_id: ID отчета
            plan_data: Данные плана обновления кэша
        
        Returns:
            Созданный план
        """
        try:
            return self._make_request(f"PowerBIReports({report_id})/CacheRefreshPlans", method="POST", data=plan_data)
        except Exception as e:
            logger.error(f"Ошибка при создании плана обновления кэша для отчета {report_id}: {e}")
            raise
    
    def update_cache_refresh_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновляет существующий план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
            plan_data: Обновленные данные плана
        
        Returns:
            Обновленный план
        """
        try:
            return self._make_request(f"CacheRefreshPlans({plan_id})", method="PATCH", data=plan_data)
        except Exception as e:
            logger.error(f"Ошибка при обновлении плана обновления кэша {plan_id}: {e}")
            raise
    
    def delete_cache_refresh_plan(self, plan_id: str) -> None:
        """
        Удаляет план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
        """
        try:
            self._make_request(f"CacheRefreshPlans({plan_id})", method="DELETE")
        except Exception as e:
            logger.error(f"Ошибка при удалении плана обновления кэша {plan_id}: {e}")
            raise
    
    def get_report_details(self, report_id: str) -> Dict[str, Any]:
        """
        Получает детальную информацию об отчете.
        
        Args:
            report_id: ID отчета
        
        Returns:
            Информация об отчете
        """
        try:
            return self._make_request(f"PowerBIReports({report_id})")
        except Exception as e:
            logger.error(f"Ошибка при получении информации об отчете {report_id}: {e}")
            raise
    
    def get_report_data_sources(self, report_id: str) -> List[Dict[str, Any]]:
        """
        Получает источники данных для указанного отчёта.
        
        Args:
            report_id: ID отчета
        
        Returns:
            Список источников данных, каждый элемент - словарь с полями:
            Name, ConnectionString, DataSourceType, CredentialRetrieval, etc.
        """
        try:
            data = self._make_request(f"reports('{report_id}')/DataSources")
            return data.get('value', [])
        except Exception as e:
            logger.error(f"Ошибка при получении источников данных для отчета {report_id}: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Проверяет подключение к серверу.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            self._make_request("PowerBIReports", params={"$top": 1})
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к серверу: {e}")
            return False

    def authenticate(self) -> str:
        """
        Заглушка для совместимости с интерфейсом PowerBIClient.
        Для PBIRS аутентификация не требуется (используется NTLM при каждом запросе).
        
        Returns:
            Пустую строку (токен не используется)
        """
        logger.info("Аутентификация для Power BI Report Server не требуется (используется NTLM)")
        # Проверяем подключение
        if self.test_connection():
            return ""
        else:
            raise AuthenticationError("Не удалось подключиться к серверу PBIRS")

    def set_debug_path(self, debug_data_path: Optional[str]) -> None:
        """
        Устанавливает путь для сохранения сырых данных отладки.
        
        Args:
            debug_data_path: Путь к директории или None для отключения
        """
        self.debug_data_path = debug_data_path
        if self.debug_data_path:
            os.makedirs(self.debug_data_path, exist_ok=True)


# Исключения (совместимые с powerbi_client.py)
class AuthenticationError(Exception):
    """Исключение для ошибок аутентификации."""
    pass


class APIRequestError(Exception):
    """Исключение для ошибок запросов к API."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ResourceNotFoundError(Exception):
    """Исключение для случаев, когда ресурс не найден."""
    pass


if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    print("Тестирование модуля Power BI Report Server Client...")
    
    # Пример использования (нужно указать реальный URL сервера)
    # client = PowerBIReportServerClient("http://localhost/Reports")
    # if client.test_connection():
    #     print("Подключение успешно")
    #     reports = client.get_powerbi_reports()
    #     print(f"Найдено отчетов: {len(reports)}")
    # else:
    #     print("Не удалось подключиться к серверу")
    
    print("Тест завершен (требуется реальный сервер для полного тестирования).")