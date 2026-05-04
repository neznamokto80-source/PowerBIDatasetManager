#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест импортов после рефакторинга.
"""

import sys
import os

def test_imports():
    """Проверка импортов всех модулей."""
    modules = [
        'src.ui.methods.connection',
        'src.ui.methods.data_loading',
        'src.ui.methods.ui_state',
        'src.ui.methods.event_handlers',
        'src.ui.methods.filtering',
        'src.ui.methods.monitoring',
        'src.ui.methods.refresh_management',
        'src.ui.main_window'
    ]
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"[OK] Импорт {module_name}")
        except Exception as e:
            print(f"[ERROR] Ошибка импорта {module_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    return True

def test_class_definitions():
    """Проверка определения классов."""
    try:
        from src.ui.main_window import PowerBIMonitorUI
        print("[OK] Класс PowerBIMonitorUI определён")
        
        # Проверяем, что классы методов определены
        from src.ui.methods.connection import ConnectionMethods
        from src.ui.methods.data_loading import DataLoadingMethods
        from src.ui.methods.ui_state import UIStateMethods
        from src.ui.methods.event_handlers import EventHandlers
        from src.ui.methods.filtering import FilteringMethods
        from src.ui.methods.monitoring import MonitoringMethods
        from src.ui.methods.refresh_management import RefreshManagementMethods
        print("[OK] Все классы методов определены")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка определения классов: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Простой тест рефакторинга ===\n")
    
    tests_passed = 0
    tests_total = 2
    
    if test_imports():
        tests_passed += 1
    
    if test_class_definitions():
        tests_passed += 1
    
    print(f"\n=== Результаты: {tests_passed}/{tests_total} тестов пройдено ===")
    if tests_passed == tests_total:
        print("[OK] Рефакторинг успешен!")
        sys.exit(0)
    else:
        print("[ERROR] Рефакторинг требует доработки.")
        sys.exit(1)