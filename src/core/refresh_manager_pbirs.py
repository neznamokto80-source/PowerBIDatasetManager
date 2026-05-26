#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль управления обновлениями Power BI Report Server.
Включает функции для работы с планами обновления кэша (Cache Refresh Plans).
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from .powerbi_report_server_client import PowerBIReportServerClient

logger = logging.getLogger(__name__)


class PBIRSRefreshManager:
    """Менеджер для управления обновлениями отчетов Power BI Report Server."""
    
    # Константы дней недели для расписания
    DAYS_OF_WEEK = {
        "Sunday": 1,
        "Monday": 2,
        "Tuesday": 3,
        "Wednesday": 4,
        "Thursday": 5,
        "Friday": 6,
        "Saturday": 7,
        "Weekdays": 62,  # Понедельник-Пятница (2+4+8+16+32)
        "Weekend": 65,   # Суббота+Воскресенье (1+64)
        "Everyday": 127  # Все дни (1+2+4+8+16+32+64)
    }
    
    def __init__(self, client: PowerBIReportServerClient):
        """
        Инициализация менеджера обновлений PBIRS.

        Args:
            client: Клиент Power BI Report Server
        """
        self.client = client
        logger.debug("PBIRSRefreshManager инициализирован")
    
    def get_cache_refresh_plans(self, report_id: str) -> List[Dict[str, Any]]:
        """
        Получает список планов обновления кэша для отчета.
        
        Args:
            report_id: ID отчета
        
        Returns:
            Список планов обновления кэша
        """
        return self.client.get_cache_refresh_plans(report_id)
    
    def execute_cache_refresh_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Немедленно запускает план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
        
        Returns:
            Результат выполнения
        """
        return self.client.execute_cache_refresh_plan(plan_id)
    
    def create_cache_refresh_plan(
        self,
        report_id: str,
        plan_name: str,
        description: str = "",
        enabled: bool = True,
        days: List[str] = None,
        times: List[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает новый план обновления кэша для отчета.
        
        Args:
            report_id: ID отчета
            plan_name: Название плана
            description: Описание плана
            enabled: Включен ли план
            days: Список дней недели (например, ["Monday", "Wednesday", "Friday"])
            times: Список времени в формате "HH:mm" (например, ["08:00", "20:00"])
            start_date: Дата начала в формате "YYYY-MM-DD" (опционально)
            end_date: Дата окончания в формате "YYYY-MM-DD" (опционально)
        
        Returns:
            Созданный план
        """
        if days is None:
            days = ["Weekdays"]
        if times is None:
            times = ["08:00"]
        
        # Преобразуем дни в битовую маску
        days_mask = 0
        for day in days:
            if day in self.DAYS_OF_WEEK:
                days_mask |= self.DAYS_OF_WEEK[day]
            else:
                logger.warning(f"Неизвестный день недели: {day}")
        
        # Формируем данные плана
        plan_data = {
            "Description": description,
            "EventType": "TimedSubscription",
            "Schedule": {
                "Definition": {
                    "StartDateTime": start_date or datetime.now().strftime("%Y-%m-%dT00:00:00"),
                    "EndDate": end_date or "9999-12-31T23:59:59",
                    "Recurrence": {
                        "DailyRecurrence": {
                            "DaysInterval": 1
                        },
                        "WeeklyRecurrence": {
                            "DaysOfWeek": {
                                "Monday": "Monday" in days,
                                "Tuesday": "Tuesday" in days,
                                "Wednesday": "Wednesday" in days,
                                "Thursday": "Thursday" in days,
                                "Friday": "Friday" in days,
                                "Saturday": "Saturday" in days,
                                "Sunday": "Sunday" in days
                            },
                            "WeeksInterval": 1
                        },
                        "MonthlyRecurrence": None,
                        "MonthlyDOWRecurrence": None
                    }
                }
            },
            "Values": {
                "ParameterValues": []
            }
        }
        
        # Устанавливаем время выполнения
        if times:
            plan_data["Schedule"]["Definition"]["StartDateTime"] = \
                f"{datetime.now().strftime('%Y-%m-%d')}T{times[0]}:00"
        
        return self.client.create_cache_refresh_plan(report_id, plan_data)
    
    def update_cache_refresh_plan(
        self,
        plan_id: str,
        plan_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обновляет существующий план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
            plan_data: Обновленные данные плана
        
        Returns:
            Обновленный план
        """
        return self.client.update_cache_refresh_plan(plan_id, plan_data)
    
    def delete_cache_refresh_plan(self, plan_id: str) -> None:
        """
        Удаляет план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
        """
        self.client.delete_cache_refresh_plan(plan_id)
    
    def enable_cache_refresh_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Включает план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
        
        Returns:
            Обновленный план
        """
        # Для PBIRS включение/выключение обычно через обновление состояния
        plan_data = {
            "Enabled": True
        }
        return self.update_cache_refresh_plan(plan_id, plan_data)
    
    def disable_cache_refresh_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Отключает план обновления кэша.
        
        Args:
            plan_id: ID плана обновления кэша
        
        Returns:
            Обновленный план
        """
        plan_data = {
            "Enabled": False
        }
        return self.update_cache_refresh_plan(plan_id, plan_data)
    
    def get_report_with_plans(self, report_id: str) -> Dict[str, Any]:
        """
        Получает информацию об отчете вместе с его планами обновления.
        
        Args:
            report_id: ID отчета
        
        Returns:
            Информация об отчете и планах обновления
        """
        report_info = self.client.get_report_details(report_id)
        refresh_plans = self.get_cache_refresh_plans(report_id)
        
        return {
            "report": report_info,
            "refresh_plans": refresh_plans,
            "has_refresh_plans": len(refresh_plans) > 0,
            "enabled_refresh_plans": [p for p in refresh_plans if p.get("Enabled", False)]
        }
    
    def test_connection(self) -> bool:
        """
        Проверяет подключение к серверу.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        return self.client.test_connection()


if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    print("Тестирование модуля PBIRS Refresh Manager...")
    
    # Пример использования (нужно указать реальный URL сервера)
    # client = PowerBIReportServerClient("http://localhost/Reports")
    # manager = PBIRSRefreshManager(client)
    # 
    # if manager.test_connection():
    #     print("Подключение успешно")
    # else:
    #     print("Не удалось подключиться к серверу")
    
    print("Тест завершен (требуется реальный сервер для полного тестирования).")