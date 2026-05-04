#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной скрипт мониторинга и управления Power BI датасетами.
Модульная архитектура с поддержкой управления обновлениями.
"""

import sys
import os
from typing import List, Dict, Any, Optional

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем модули
from modules.dependencies import DependencyManager
from modules.powerbi_client import PowerBIClient, parse_utc_to_local
from modules.refresh_manager import RefreshManager, create_default_schedule


class PowerBIMonitor:
    """Основной класс для мониторинга и управления Power BI."""
    
    def __init__(self):
        """Инициализация мониторинга Power BI."""
        self.client = None
        self.refresh_manager = None
    
    def initialize(self):
        """Инициализация зависимостей и клиентов."""
        # Проверяем и устанавливаем зависимости
        DependencyManager.ensure_dependencies()
        
        # Создаем клиент и менеджер
        self.client = PowerBIClient()
        self.refresh_manager = RefreshManager(self.client)
        
        # Аутентификация
        self.client.authenticate()
        print("✓ Система инициализирована и аутентифицирована.")
    
    def show_menu(self):
        """Отображает главное меню."""
        print("\n" + "="*60)
        print("POWER BI DATASET MONITOR & MANAGER")
        print("="*60)
        print("1. Просмотр информации о датасетах")
        print("2. Включить автоматическое обновление для датасета")
        print("3. Отключить автоматическое обновление для датасета")
        print("4. Запустить ручное обновление датасета")
        print("5. Просмотр истории обновлений")
        print("6. Пакетное управление обновлениями")
        print("7. Выход")
        print("="*60)
    
    def get_workspace_interactive(self) -> Optional[Dict[str, Any]]:
        """
        Интерактивный выбор рабочей области.
        
        Returns:
            Информация о выбранной рабочей области или None
        """
        try:
            workspaces = self.client.get_workspaces()
            
            if not workspaces:
                print("Рабочие области не найдены.")
                return None
            
            print("\nДоступные рабочие области:")
            for i, ws in enumerate(workspaces, 1):
                print(f"{i}. {ws.get('name')} (ID: {ws.get('id')})")
            
            choice = input("\nВыберите номер рабочей области (или введите имя): ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(workspaces):
                    return workspaces[idx]
                else:
                    print("Неверный номер.")
                    return None
            else:
                # Поиск по имени
                for ws in workspaces:
                    if ws.get('name', '').lower() == choice.lower():
                        return ws
                print(f"Рабочая область '{choice}' не найдена.")
                return None
                
        except Exception as e:
            print(f"Ошибка получения рабочих областей: {e}")
            return None
    
    def get_dataset_interactive(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        Интерактивный выбор датасета.
        
        Args:
            workspace_id: ID рабочей области
        
        Returns:
            Информация о выбранном датасете или None
        """
        try:
            datasets = self.client.get_datasets_in_workspace(workspace_id)
            
            if not datasets:
                print("Датасеты не найдены.")
                return None
            
            print("\nДоступные датасеты:")
            for i, ds in enumerate(datasets, 1):
                ds_name = ds.get('name', 'Без имени')
                ds_id_short = ds.get('id', '')[:8] + '...'
                print(f"{i}. {ds_name} (ID: {ds_id_short})")
            
            choice = input("\nВыберите номер датасета: ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(datasets):
                    return datasets[idx]
                else:
                    print("Неверный номер.")
                    return None
            else:
                print("Введите номер.")
                return None
                
        except Exception as e:
            print(f"Ошибка получения датасетов: {e}")
            return None
    
    def view_datasets_info(self):
        """Просмотр информации о датасетах в рабочей области."""
        workspace = self.get_workspace_interactive()
        if not workspace:
            return
        
        workspace_id = workspace["id"]
        workspace_name = workspace["name"]
        
        print(f"\nРабочая область: {workspace_name}")
        print("="*60)
        
        try:
            datasets = self.client.get_datasets_in_workspace(workspace_id)
            
            if not datasets:
                print("Датасеты не найдены.")
                return
            
            print(f"Найдено датасетов: {len(datasets)}\n")
            
            # Собираем информацию по каждому датасету
            results = []
            for ds in datasets:
                ds_id = ds["id"]
                ds_name = ds["name"]
                
                try:
                    # Расписание
                    schedule = self.client.get_refresh_schedule(workspace_id, ds_id)
                    enabled = schedule.get("enabled", False)
                except Exception:
                    enabled = False
                
                try:
                    # Последнее обновление
                    last = self.client.get_last_refresh(workspace_id, ds_id)
                    if last:
                        end_time_utc = last.get("endTime")
                        status = last.get("status", "Unknown")
                        last_refresh = parse_utc_to_local(end_time_utc) if end_time_utc else "—"
                        last_status = status
                    else:
                        last_refresh = "—"
                        last_status = "Нет обновлений"
                except Exception:
                    last_refresh = "—"
                    last_status = "Ошибка получения"
                
                results.append({
                    "ID": ds_id,
                    "Name": ds_name,
                    "Enabled": enabled,
                    "Last_refresh": last_refresh,
                    "Last_status": last_status
                })
            
            # Вывод таблицы
            print("-" * 120)
            print(f"{'ID':<38} {'Name':<40} {'Enabled':<8} {'Last refresh':<20} {'Status':<15}")
            print("-" * 120)
            for row in results:
                print(f"{row['ID']:<38} {row['Name']:<40} {str(row['Enabled']):<8} {row['Last_refresh']:<20} {row['Last_status']:<15}")
            print("-" * 120)
            
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def enable_auto_refresh_interactive(self):
        """Интерактивное включение автоматического обновления."""
        workspace = self.get_workspace_interactive()
        if not workspace:
            return
        
        workspace_id = workspace["id"]
        dataset = self.get_dataset_interactive(workspace_id)
        if not dataset:
            return
        
        dataset_id = dataset["id"]
        dataset_name = dataset["name"]
        
        print(f"\nВключение автоматического обновления для датасета: {dataset_name}")
        
        # Настройки расписания
        print("\nНастройки расписания:")
        print("1. Ежедневно в 3:00 (по умолчанию)")
        print("2. Ежедневно в указанное время")
        print("3. В определенные дни недели")
        
        choice = input("Выберите вариант (1-3, по умолчанию 1): ").strip()
        
        if choice == "2":
            time_input = input("Введите время в формате HH:MM (например, 02:30): ").strip()
            times = [time_input] if time_input else ["03:00"]
            schedule = create_default_schedule(times=times)
        elif choice == "3":
            days_input = input("Введите дни через запятую (например, Monday,Wednesday,Friday): ").strip()
            days = [d.strip() for d in days_input.split(",")] if days_input else None
            time_input = input("Введите время в формате HH:MM (например, 02:30): ").strip()
            times = [time_input] if time_input else ["03:00"]
            schedule = create_default_schedule(days=days, times=times)
        else:
            schedule = None  # Используется расписание по умолчанию
        
        try:
            result = self.refresh_manager.enable_auto_refresh(workspace_id, dataset_id, schedule)
            print(f"✓ Автоматическое обновление включено для датасета '{dataset_name}'")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def disable_auto_refresh_interactive(self):
        """Интерактивное отключение автоматического обновления."""
        workspace = self.get_workspace_interactive()
        if not workspace:
            return
        
        workspace_id = workspace["id"]
        dataset = self.get_dataset_interactive(workspace_id)
        if not dataset:
            return
        
        dataset_id = dataset["id"]
        dataset_name = dataset["name"]
        
        print(f"\nОтключение автоматического обновления для датасета: {dataset_name}")
        
        confirm = input("Вы уверены? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Операция отменена.")
            return
        
        try:
            result = self.refresh_manager.disable_auto_refresh(workspace_id, dataset_id)
            print(f"✓ Автоматическое обновление отключено для датасета '{dataset_name}'")
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def trigger_manual_refresh_interactive(self):
        """Интерактивный запуск ручного обновления."""
        workspace = self.get_workspace_interactive()
        if not workspace:
            return
        
        workspace_id = workspace["id"]
        dataset = self.get_dataset_interactive(workspace_id)
        if not dataset:
            return
        
        dataset_id = dataset["id"]
        dataset_name = dataset["name"]
        
        print(f"\nЗапуск ручного обновления для датасета: {dataset_name}")
        
        print("\nТип обновления:")
        print("1. Полное (Full) - по умолчанию")
        print("2. Только данные (DataOnly)")
        print("3. Очистка значений (ClearValues)")
        
        type_choice = input("Выберите тип (1-3, по умолчанию 1): ").strip()
        
        refresh_type = "Full"
        if type_choice == "2":
            refresh_type = "DataOnly"
        elif type_choice == "3":
            refresh_type = "ClearValues"
        
        confirm = input(f"Запустить {refresh_type} обновление? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Операция отменена.")
            return
        
        try:
            result = self.refresh_manager.trigger_manual_refresh(
                workspace_id, dataset_id, refresh_type=refresh_type
            )
            print(f"✓ Ручное обновление запущено для датасета '{dataset_name}'")
            print(f"  ID обновления: {result.get('id', 'неизвестно')}")
            
            # Спросить о мониторинге статуса
            monitor = input("Мониторить статус обновления? (y/N): ").strip().lower()
            if monitor == 'y' and 'id' in result:
                refresh_id = result['id']
                print(f"Мониторинг статуса обновления {refresh_id}...")
                try:
                    final_status = self.refresh_manager.wait_for_refresh_completion(
                        workspace_id, dataset_id, refresh_id, poll_interval=5, timeout=300
                    )
                    print(f"✓ Обновление завершено со статусом: {final_status.get('status')}")
                except TimeoutError:
                    print("⚠ Обновление не завершилось за отведенное время.")
                    
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    def view_refresh_history(self):
        """Просмотр истории обновлений."""
        workspace = self.get_workspace_interactive()
        if not workspace:
            return
        
        workspace_id = workspace["id"]
        dataset = self.get_dataset_interactive(workspace_id)
        if not dataset:
            return
        
        dataset_id = dataset["id"]
        dataset_name = dataset["name"]
        
        print(f"\nИстория обновлений для датасета: {dataset_name}")
        
        try:
            limit_input = input("Количество записей (по умолчанию 10): ").strip()
            limit = int(limit_input) if limit_input.isdigit() else 10
            
            history = self.refresh_manager.get_refresh_history(workspace_id, dataset_id, limit)
            
            if not history:
                print("История обновлений пуста.")
                return
            
            print(f"\nНайдено записей: {len(history)}")
            print("-" * 100)
            print(f"{'Дата начала':<20} {'Дата окончания':<20} {'Статус':<15} {'Длительность':<15} {'ID':<30}")
            print("-" * 100)
            
            for refresh in history:
                start_time = refresh.get('startTimeLocal', '—')
                end_time = refresh.get('endTimeLocal', '—')
                status = refresh.get('status', 'Unknown')
                duration = refresh.get('durationFormatted', '—')
                refresh_id = refresh.get('id', '')[:28] + '...' if len(refresh.get('id', '')) > 28 else refresh.get('id', '')
                
                print(f"{start_time:<20} {end_time:<20} {status:<15} {duration:<15} {refresh_id:<30}")
            
            print("-" * 100)
            
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def batch_management(self):
        """Пакетное управление обновлениями."""
        workspace = self.get_workspace_interactive()
        if not workspace:
            return
        
        workspace_id = workspace["id"]
        
        print("\nПакетное управление обновлениями")
        print("1. Включить обновление для всех датасетов")
        print("2. Отключить обновление для всех датасетов")
        print("3. Выбрать датасеты для управления")
        
        choice = input("Выберите действие (1-3): ").strip()
        
        try:
            datasets = self.client.get_datasets_in_workspace(workspace_id)
            
            if not datasets:
                print("Датасеты не найдены.")
                return
            
            dataset_ids = [ds["id"] for ds in datasets]
            dataset_names = [ds["name"] for ds in datasets]
            
            if choice == "1":
                print(f"\nВключение автоматического обновления для {len(dataset_ids)} датасетов...")
                confirm = input("Вы уверены? (y/N): ").strip().lower()
                if confirm == 'y':
                    results = self.refresh_manager.batch_enable_refresh(workspace_id, dataset_ids)
                    self._print_batch_results(results)
                    
            elif choice == "2":
                print(f"\nОтключение автоматического обновления для {len(dataset_ids)} датасетов...")
                confirm = input("Вы уверены? (y/N): ").strip().lower()
                if confirm == 'y':
                    results = self.refresh_manager.batch_disable_refresh(workspace_id, dataset_ids)
                    self._print_batch_results(results)
                    
            elif choice == "3":
                print("\nВыберите датасеты для управления (введите номера через запятую):")
                for i, name in enumerate(dataset_names, 1):
                    print(f"{i}. {name}")
                
                selection = input("Номера датасетов: ").strip()
                selected_indices = []
                for part in selection.split(','):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part) - 1
                        if 0 <= idx < len(datasets):
                            selected_indices.append(idx)
                
                if not selected_indices:
                    print("Не выбрано ни одного датасета.")
                    return
                
                selected_ids = [dataset_ids[i] for i in selected_indices]
                selected_names = [dataset_names[i] for i in selected_indices]
                
                print(f"\nВыбрано датасетов: {len(selected_ids)}")
                for name in selected_names:
                    print(f"  - {name}")
                
                print("\nДействие:")
                print("1. Включить обновление")
                print("2. Отключить обновление")
                
                action = input("Выберите действие (1-2): ").strip()
                
                if action == "1":
                    results = self.refresh_manager.batch_enable_refresh(workspace_id, selected_ids)
                    self._print_batch_results(results)
                elif action == "2":
                    results = self.refresh_manager.batch_disable_refresh(workspace_id, selected_ids)
                    self._print_batch_results(results)
                else:
                    print("Неверный выбор.")
                    
            else:
                print("Неверный выбор.")
                
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def _print_batch_results(self, results: Dict[str, List[Dict[str, Any]]]):
        """Выводит результаты пакетной операции."""
        success_count = len(results.get("success", []))
        failed_count = len(results.get("failed", []))
        
        print(f"\nРезультаты:")
        print(f"  Успешно: {success_count}")
        print(f"  Неудачно: {failed_count}")
        
        if failed_count > 0:
            print("\nОшибки:")
            for failure in results["failed"]:
                print(f"  - {failure['dataset_id']}: {failure['error']}")
    
    def run(self):
        """Основной цикл выполнения программы."""
        try:
            self.initialize()
            
            while True:
                self.show_menu()
                choice = input("\nВыберите действие (1-7): ").strip()
                
                if choice == "1":
                    self.view_datasets_info()
                elif choice == "2":
                    self.enable_auto_refresh_interactive()
                elif choice == "3":
                    self.disable_auto_refresh_interactive()
                elif choice == "4":
                    self.trigger_manual_refresh_interactive()
                elif choice == "5":
                    self.view_refresh_history()
                elif choice == "6":
                    self.batch_management()
                elif choice == "7":
                    print("\nВыход из программы.")
                    break
                else:
                    print("Неверный выбор. Попробуйте снова.")
                
                input("\nНажмите Enter для продолжения...")
                
        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем.")
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Точка входа в программу."""
    print("Power BI Dataset Monitor & Manager")
    print("Версия 2.0 - Модульная архитектура\n")
    
    monitor = PowerBIMonitor()
    monitor.run()


if __name__ == "__main__":
    main()