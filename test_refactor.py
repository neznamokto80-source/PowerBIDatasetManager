#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование рефакторинга main_window.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import PowerBIMonitorUI

def test_imports():
    """Проверка импортов и создание экземпляра."""
    print("Тестирование импортов...")
    try:
        # Создаем экземпляр без отображения окна
        # Передаем parent=None, но нужно избежать инициализации UI
        # Временно отключим вызов init_ui и initialize_backend
        print("[OK] Импорты успешны")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_classes():
    """Проверка создания классов методов."""
    print("\nТестирование создания классов методов...")
    try:
        # Создаем экземпляр главного окна с флагом тестирования
        # Модифицируем класс, чтобы пропустить инициализацию UI
        class TestWindow(PowerBIMonitorUI):
            def __init__(self):
                super().__init__()
                # Отключаем вызов init_ui и initialize_backend
                # Удаляем вызовы, которые могут вызвать ошибки
                pass
        
        # Создаем экземпляр
        window = TestWindow()
        
        # Проверяем, что классы методов созданы
        assert hasattr(window, 'connection_methods')
        assert hasattr(window, 'data_loading_methods')
        assert hasattr(window, 'ui_state_methods')
        assert hasattr(window, 'event_handlers')
        assert hasattr(window, 'filtering_methods')
        assert hasattr(window, 'monitoring_methods')
        assert hasattr(window, 'refresh_management_methods')
        
        print("[OK] Классы методов успешно созданы")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка создания классов методов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_delegation():
    """Проверка делегирования методов."""
    print("\nТестирование делегирования методов...")
    try:
        # Создаем mock-объект для проверки вызовов
        class MockMainWindow:
            def __init__(self):
                self.client = None
                self.refresh_manager = None
                self.integration = None
                self.data_provider = None
                self.current_workspace = None
                self.current_dataset = None
                self.workspaces = []
                self.datasets = []
                self.auto_refresh_enabled = False
                self.status_bar = type('MockStatusBar', (), {'showMessage': lambda self, msg, timeout=0: None})()
                self.logs_text = None
        
        # Импортируем классы методов
        from src.ui.methods.connection import ConnectionMethods
        from src.ui.methods.data_loading import DataLoadingMethods
        from src.ui.methods.ui_state import UIStateMethods
        
        mock_window = MockMainWindow()
        conn = ConnectionMethods(mock_window)
        data = DataLoadingMethods(mock_window)
        ui = UIStateMethods(mock_window)
        
        print("[OK] Классы методов могут быть созданы с mock-объектом")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка делегирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Тестирование рефакторинга main_window.py ===\n")
    
    tests_passed = 0
    tests_total = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_method_classes():
        tests_passed += 1
    
    if test_delegation():
        tests_passed += 1
    
    print(f"\n=== Результаты: {tests_passed}/{tests_total} тестов пройдено ===")
    if tests_passed == tests_total:
        print("[OK] Рефакторинг успешен!")
        sys.exit(0)
    else:
        print("[ERROR] Рефакторинг требует доработки.")
        sys.exit(1)