#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль интеграции UI с бизнес-логикой.
Предоставляет классы для получения данных для отображения статистики.
"""

import logging
from typing import Dict, Any, List, Optional
from src.core.powerbi_client import PowerBIClient, parse_utc_to_local
from src.core.refresh_manager import RefreshManager

logger = logging.getLogger(__name__)


class UIIntegration:
    """Интеграция UI с клиентом Power BI и менеджером обновлений."""
    
    def __init__(self, client: PowerBIClient, refresh_manager: RefreshManager):
        """
        Инициализация интеграции.
        
        Args:
            client: Клиент Power BI
            refresh_manager: Менеджер обновлений
        """
        self.client = client
        self.refresh_manager = refresh_manager
        logger.debug("UIIntegration инициализирован")
    
    def get_datasets_stats(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Возвращает статистику по датасетам.
        
        Args:
            workspace_id: Опциональный ID рабочей области для фильтрации
        
        Returns:
            Словарь со статистикой
        """
        logger.debug("Получение статистики датасетов")
        
        try:
            if workspace_id:
                datasets = self.client.get_datasets_in_workspace(workspace_id)
            else:
                # Получаем датасеты из всех рабочих областей
                workspaces = self.client.get_workspaces()
                datasets = []
                for workspace in workspaces:
                    ws_id = workspace.get('id')
                    if ws_id:
                        try:
                            datasets.extend(self.client.get_datasets_in_workspace(ws_id))
                        except Exception as e:
                            logger.warning(f"Ошибка получения датасетов из workspace {ws_id}: {e}")
                            continue
            
            total_datasets = len(datasets)
            
            # Подсчет датасетов с включенным обновлением (упрощенно)
            enabled_refresh = 0
            failed_refresh = 0
            
            for dataset in datasets:
                # Проверяем, есть ли информация о расписании
                if dataset.get('isRefreshable', False):
                    enabled_refresh += 1
                # Проверяем статус последнего обновления (если есть)
                last_refresh = dataset.get('lastRefresh', {})
                if last_refresh and last_refresh.get('status') == 'Failed':
                    failed_refresh += 1
            
            stats = {
                'total_datasets': total_datasets,
                'enabled_refresh': enabled_refresh,
                'failed_refresh': failed_refresh,
                'successful_refresh': total_datasets - failed_refresh,
                'refresh_coverage': (enabled_refresh / total_datasets * 100) if total_datasets > 0 else 0
            }
            
            logger.info(f"Статистика датасетов: всего {total_datasets}, с обновлением {enabled_refresh}")
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики датасетов: {e}")
            # Возвращаем заглушку в случае ошибки
            return {
                'total_datasets': 0,
                'enabled_refresh': 0,
                'failed_refresh': 0,
                'successful_refresh': 0,
                'refresh_coverage': 0
            }
    
    def get_dataset_list(self, workspace_id: Optional[str] = None, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Возвращает список датасетов с возможностью отслеживать прогресс.
        
        Args:
            workspace_id: ID рабочей области (если None, возвращает все датасеты)
            progress_callback: функция, принимающая (current, total, message)
        
        Returns:
            Список датасетов с дополнительной информацией
        """
        logger.debug(f"Получение списка датасетов для workspace: {workspace_id}")
        
        try:
            if workspace_id:
                datasets = self.client.get_datasets_in_workspace(workspace_id)
                # Добавляем workspace_id в каждый датасет
                for ds in datasets:
                    ds['workspace_id'] = workspace_id
            else:
                # Получаем датасеты из всех рабочих областей
                workspaces = self.client.get_workspaces()
                datasets = []
                for workspace in workspaces:
                    ws_id = workspace.get('id')
                    if ws_id:
                        try:
                            ws_datasets = self.client.get_datasets_in_workspace(ws_id)
                            for ds in ws_datasets:
                                ds['workspace_name'] = workspace.get('name', 'Unknown')
                                ds['workspace_id'] = ws_id
                            datasets.extend(ws_datasets)
                        except Exception as e:
                            logger.warning(f"Ошибка получения датасетов из workspace {ws_id}: {e}")
                            continue
            
            # Обогащаем данные информацией о последнем обновлении и расписании
            enriched_datasets = []
            total = len(datasets)
            for idx, dataset in enumerate(datasets):
                if progress_callback:
                    progress_callback(idx + 1, total, f"Обработка {dataset.get('name', '...')}")
                
                enriched = dataset.copy()
                dataset_id = dataset.get('id')
                current_workspace_id = dataset.get('workspace_id') or workspace_id
                
                # Добавляем workspace_id и workspace_name, если отсутствуют
                if current_workspace_id and 'workspace_id' not in enriched:
                    enriched['workspace_id'] = current_workspace_id
                    # Получаем имя рабочей области из списка workspace (если доступно)
                    # Пока оставим пустым, позже можно заполнить
                
                if dataset_id and current_workspace_id:
                    try:
                        last_refresh = self.client.get_last_refresh(current_workspace_id, dataset_id)
                        if last_refresh:
                            enriched['last_refresh'] = last_refresh
                            enriched['last_refresh_status'] = last_refresh.get('status', 'Unknown')
                            start_time = last_refresh.get('startTime', '')
                            enriched['last_refresh_time'] = start_time
                            # Добавляем совместимые поля для UI с форматированием
                            if start_time:
                                try:
                                    formatted_time = parse_utc_to_local(start_time)
                                except Exception:
                                    formatted_time = start_time
                                enriched['lastRefreshTime'] = formatted_time
                            else:
                                enriched['lastRefreshTime'] = 'никогда'
                    except Exception as e:
                        logger.debug(f"Не удалось получить последнее обновление для датасета {dataset_id}: {e}")
                    
                    try:
                        schedule = self.client.get_refresh_schedule(current_workspace_id, dataset_id)
                        if schedule:
                            enriched['refresh_schedule'] = schedule
                            # Извлекаем следующее запланированное время
                            next_refresh = schedule.get('nextScheduleTime')
                            if next_refresh:
                                try:
                                    formatted_next = parse_utc_to_local(next_refresh)
                                except Exception:
                                    formatted_next = next_refresh
                                enriched['nextRefreshTime'] = formatted_next
                    except Exception as e:
                        logger.debug(f"Не удалось получить расписание для датасета {dataset_id}: {e}")
                
                # Устанавливаем значения по умолчанию, если поля отсутствуют
                enriched.setdefault('lastRefreshTime', 'никогда')
                enriched.setdefault('nextRefreshTime', 'не запланировано')
                # Используем статус последнего обновления, если есть
                if 'last_refresh_status' in enriched and enriched['last_refresh_status']:
                    enriched['status'] = enriched['last_refresh_status']
                else:
                    enriched.setdefault('status', 'unknown')
                enriched.setdefault('isRefreshable', False)
                
                enriched_datasets.append(enriched)
            
            logger.debug(f"Получено {len(enriched_datasets)} датасетов")
            return enriched_datasets
            
        except Exception as e:
            logger.error(f"Ошибка получения списка датасетов: {e}")
            return []
    
    def get_refresh_history(self, dataset_id: str, workspace_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Возвращает историю обновлений датасета.
        
        Args:
            dataset_id: ID датасета
            workspace_id: ID рабочей области
            limit: Максимальное количество записей
        
        Returns:
            Список обновлений с дополнительной информацией
        """
        logger.debug(f"Получение истории обновлений для датасета {dataset_id}")
        
        if not self.refresh_manager:
            logger.warning("RefreshManager не инициализирован")
            return []
        
        try:
            history = self.refresh_manager.get_refresh_history(workspace_id, dataset_id, limit)
            logger.debug(f"Получено {len(history)} записей истории обновлений")
            return history
        except Exception as e:
            logger.error(f"Ошибка получения истории обновлений: {e}")
            return []


class UIDataProvider:
    """Провайдер данных для UI, использует интеграцию."""
    
    def __init__(self, integration: UIIntegration):
        """
        Инициализация провайдера данных.
        
        Args:
            integration: Экземпляр UIIntegration
        """
        self.integration = integration
        logger.debug("UIDataProvider инициализирован")
    
    def get_stats_data(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Возвращает данные статистики для отображения.
        
        Args:
            workspace_id: Опциональный ID рабочей области
        
        Returns:
            Словарь со статистикой
        """
        return self.integration.get_datasets_stats(workspace_id)
    
    def get_dataset_data(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Возвращает данные датасетов.
        
        Args:
            workspace_id: Опциональный ID рабочей области
        
        Returns:
            Список датасетов
        """
        return self.integration.get_dataset_list(workspace_id)
    
    def get_refresh_data(self, dataset_id: str, workspace_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Возвращает данные истории обновлений.
        
        Args:
            dataset_id: ID датасета
            workspace_id: ID рабочей области
            limit: Максимальное количество записей
        
        Returns:
            Список обновлений
        """
        return self.integration.get_refresh_history(dataset_id, workspace_id, limit)
    
    def get_workspace_data(self) -> List[Dict[str, Any]]:
        """
        Возвращает список рабочих областей.
        
        Returns:
            Список рабочих областей
        """
        try:
            return self.integration.client.get_workspaces()
        except Exception as e:
            logger.error(f"Ошибка получения рабочих областей: {e}")
            return []