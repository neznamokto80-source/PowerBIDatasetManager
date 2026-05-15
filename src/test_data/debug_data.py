#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для сохранения сырых данных API-запросов в каталог debug/.
Используется для отладки и анализа работы с Power BI API.
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Union, Dict, List, Optional

logger = logging.getLogger(__name__)


class DebugDataSaver:
    """
    Сохраняет сырые данные ответа в файл для отладки.
    Организует файлы по рабочим областям и датасетам для удобства тестирования.
    """
    
    POWER_BI_API_BASE = "https://api.powerbi.com/v1.0/myorg/"
    
    def __init__(self, debug_data_path: Optional[str] = None):
        """
        Инициализирует сохранение отладочных данных.
        
        Args:
            debug_data_path: Путь к каталогу для сохранения сырых данных.
                             Если None, сохранение отключено.
        """
        self.debug_data_path = debug_data_path
    
    def save_raw_data(self, url: str, method: str, data: Union[Dict, List], status_code: int):
        """
        Сохраняет сырые данные ответа в файл для отладки.
        
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
    
    def is_enabled(self) -> bool:
        """Проверяет, включено ли сохранение отладочных данных."""
        return self.debug_data_path is not None and os.path.isdir(self.debug_data_path)


# Глобальный экземпляр для удобного использования
_debug_saver: Optional[DebugDataSaver] = None


def init_debug_saver(debug_data_path: Optional[str] = None):
    """
    Инициализирует глобальный отладчик сырых данных.
    
    Args:
        debug_data_path: Путь к каталогу для сохранения сырых данных.
                         Если None, сохранение отключено.
    """
    global _debug_saver
    _debug_saver = DebugDataSaver(debug_data_path)


def get_debug_saver() -> DebugDataSaver:
    """
    Возвращает глобальный экземпляр отладчика сырых данных.
    Если не инициализирован, создает с путем по умолчанию (debug/ в корне проекта).
    """
    global _debug_saver
    if _debug_saver is None:
        # Путь по умолчанию
        default_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug')
        _debug_saver = DebugDataSaver(default_path)
    return _debug_saver


def save_raw_data(url: str, method: str, data: Union[Dict, List], status_code: int):
    """
    Сохраняет сырые данные ответа в файл для отладки (удобная обертка).
    
    Args:
        url: URL запроса
        method: HTTP метод
        data: Данные ответа (словарь или список)
        status_code: Код статуса HTTP
    """
    saver = get_debug_saver()
    saver.save_raw_data(url, method, data, status_code)


def enable_debug_logging(enable: bool = True, custom_path: Optional[str] = None):
    """
    Включает или отключает сохранение сырых данных.
    
    Args:
        enable: Включить сохранение
        custom_path: Пользовательский путь для сохранения (если None, используется путь по умолчанию)
    """
    global _debug_saver
    if enable:
        path = custom_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug')
        _debug_saver = DebugDataSaver(path)
        logger.info(f"Сохранение сырых данных включено. Путь: {path}")
    else:
        _debug_saver = DebugDataSaver(None)
        logger.info("Сохранение сырых данных отключено.")


def is_debug_logging_enabled() -> bool:
    """Проверяет, включено ли сохранение сырых данных."""
    saver = get_debug_saver()
    return saver.is_enabled()