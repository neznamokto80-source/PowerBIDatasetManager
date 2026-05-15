#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль операций обновления Power BI датасетов.
Включает функции для включения/отключения автоматического обновления и ручного запуска.
"""

import logging
from typing import Dict, Any, Optional, List
from .powerbi_client import PowerBIClient, APIRequestError

logger = logging.getLogger(__name__)


def create_default_schedule(
    days: List[str] = None,
    times: List[str] = None,
    timezone: str = "Central Asia Standard Time",
    notify_option: str = "MailOnFailure"
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
        "enabled": True,
        "days": days,
        "times": times,
        "localTimeZoneId": timezone,
        "notifyOption": notify_option
    }


def _clean_schedule(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Удаляет служебные поля из расписания (например, @odata.context).
    
    Args:
        schedule: Расписание, полученное от API
        
    Returns:
        Очищенное расписание
    """
    # Копируем словарь, чтобы не изменять оригинал
    cleaned = schedule.copy()
    # Удаляем поля, начинающиеся с '@'
    keys_to_remove = [key for key in cleaned.keys() if key.startswith('@')]
    for key in keys_to_remove:
        del cleaned[key]
    return cleaned


def _prepare_schedule_for_update(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Подготавливает расписание для отправки в PATCH-запросе.
    Оставляет только поля, которые принимает API Power BI.
    Разрешённые поля: enabled, days, times, localTimeZoneId, notifyOption.
    
    Args:
        schedule: Расписание (очищенное от служебных полей)
        
    Returns:
        Тело запроса для PATCH
    """
    # Поля, которые API принимает для обновления расписания (в т.ч. notifyOption)
    allowed_fields = {"enabled", "days", "times", "localTimeZoneId", "notifyOption"}
    prepared = {key: schedule[key] for key in schedule.keys() if key in allowed_fields}
    return prepared


def update_refresh_schedule(
    client: PowerBIClient,
    workspace_id: str,
    dataset_id: str,
    schedule: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Создаёт или полностью обновляет расписание обновления датасета (PATCH).

    Args:
        client: Клиент Power BI
        workspace_id: ID рабочей области
        dataset_id: ID датасета
        schedule: Словарь расписания (как в ответе GET refreshSchedule), без служебных полей @odata.*

    Returns:
        Ответ API

    Raises:
        APIRequestError: При ошибке запроса
    """
    cleaned = _clean_schedule(dict(schedule))
    prepared = _prepare_schedule_for_update(cleaned)
    body = {"value": prepared}
    url = f"{client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule"
    logger.info(
        "Обновление расписания датасета %s в workspace %s: enabled=%s, слотов времени=%s",
        dataset_id,
        workspace_id,
        prepared.get("enabled"),
        len(prepared.get("times") or []),
    )
    logger.debug("PATCH refreshSchedule: %s", body)
    return client.make_request(url, method="PATCH", body=body)


def enable_auto_refresh(
    client: PowerBIClient,
    workspace_id: str,
    dataset_id: str,
    schedule: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Включает автоматическое обновление для датасета.

    Args:
        client: Клиент Power BI
        workspace_id: ID рабочей области
        dataset_id: ID датасета
        schedule: Настройки расписания (если None, используется расписание по умолчанию)

    Returns:
        Результат операции

    Raises:
        APIRequestError: При ошибке запроса к API
    """
    schedule_to_update = None
    
    # Если расписание передано явно, используем его
    if schedule is not None:
        schedule_to_update = _clean_schedule(schedule)
        schedule_to_update["enabled"] = True
        logger.debug(f"Используется переданное расписание, установлено enabled=True")
    else:
        # Пытаемся получить текущее расписание
        try:
            current_schedule = client.get_refresh_schedule(workspace_id, dataset_id)
            # Очищаем от служебных полей
            current_schedule = _clean_schedule(current_schedule)
            # Обновляем только поле enabled
            current_schedule["enabled"] = True
            schedule_to_update = current_schedule
            logger.debug(f"Используется существующее расписание, обновлено поле enabled")
        except APIRequestError as e:
            # Если расписание не найдено (404), создаем новое
            if e.status_code == 404:
                schedule_to_update = create_default_schedule()
                schedule_to_update["enabled"] = True
                logger.debug(f"Расписание не найдено, создано новое с enabled=True")
            else:
                raise
    
    logger.info(f"Включение автообновления для датасета {dataset_id} в workspace {workspace_id}")
    
    # Подготавливаем расписание для отправки (оставляем только разрешённые поля)
    schedule_to_update = _prepare_schedule_for_update(schedule_to_update)
    
    # Обёртываем в "value" как требует API Power BI
    body = {"value": schedule_to_update}
    
    url = f"{client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule"
    logger.debug(f"Тело запроса PATCH для включения автообновления: {body}")
    result = client.make_request(url, method="PATCH", body=body)
    
    logger.info(f"Автообновление успешно включено для датасета {dataset_id}")
    return result


def disable_auto_refresh(
    client: PowerBIClient,
    workspace_id: str,
    dataset_id: str
) -> Dict[str, Any]:
    """
    Отключает автоматическое обновление для датасета.

    Args:
        client: Клиент Power BI
        workspace_id: ID рабочей области
        dataset_id: ID датасета

    Returns:
        Результат операции

    Raises:
        APIRequestError: При ошибке запроса к API
    """
    schedule_to_update = None
    
    # Пытаемся получить текущее расписание
    try:
        current_schedule = client.get_refresh_schedule(workspace_id, dataset_id)
        # Очищаем от служебных полей
        current_schedule = _clean_schedule(current_schedule)
        # Обновляем только поле enabled
        current_schedule["enabled"] = False
        schedule_to_update = current_schedule
        logger.debug(f"Используется существующее расписание, обновлено поле enabled=False")
    except APIRequestError as e:
        # Если расписание не найдено (404), создаем новое с enabled=False
        if e.status_code == 404:
            schedule_to_update = create_default_schedule()
            schedule_to_update["enabled"] = False
            logger.debug(f"Расписание не найдено, создано новое с enabled=False")
        else:
            raise

    logger.info(f"Отключение автообновления для датасета {dataset_id} в workspace {workspace_id}")

    # Отправляем только поле enabled, чтобы не изменять другие настройки
    body = {"value": {"enabled": False}}
    
    url = f"{client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule"
    logger.debug(f"Тело запроса PATCH для отключения автообновления: {body}")
    result = client.make_request(url, method="PATCH", body=body)

    logger.info(f"Автообновление успешно отключено для датасета {dataset_id}")
    return result


def trigger_manual_refresh(
    client: PowerBIClient,
    workspace_id: str,
    dataset_id: str,
    notify_option: str = "NoNotification",
    refresh_type: str = "Full"
) -> Dict[str, Any]:
    """
    Запускает ручное обновление датасета.

    Args:
        client: Клиент Power BI
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
    # Константы типов обновлений и опций уведомлений (можно вынести в отдельный модуль)
    REFRESH_TYPES = {
        "Full", "ClearValues", "Calculate", "DataOnly",
        "Automatic", "Defragment"
    }
    NOTIFY_OPTIONS = {
        "NoNotification", "MailOnFailure", "MailOnCompletion"
    }
    
    if notify_option not in NOTIFY_OPTIONS:
        raise ValueError(f"Недопустимая опция уведомления: {notify_option}")
    
    if refresh_type not in REFRESH_TYPES:
        raise ValueError(f"Недопустимый тип обновления: {refresh_type}")
    
    body = {
        "notifyOption": notify_option
    }
    
    if refresh_type != "Full":
        body["type"] = refresh_type
    
    logger.info(
        f"Запуск ручного обновления для датасета {dataset_id} "
        f"(тип: {refresh_type}, уведомление: {notify_option})"
    )
    
    url = f"{client.POWER_BI_API_BASE}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
    result = client.make_request(url, method="POST", body=body)
    
    logger.info(f"Ручное обновление запущено для датасета {dataset_id}")
    return result