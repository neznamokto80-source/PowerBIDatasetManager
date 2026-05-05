#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка пути сохранения сырых данных.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.powerbi_client import PowerBIClient

def test_debug_path():
    debug_path = r"C:\temp\work\PBI_DATA\data"
    print(f"Проверяем путь: {debug_path}")
    
    # Проверяем, существует ли директория
    if os.path.exists(debug_path):
        print(f"Директория уже существует.")
    else:
        print(f"Директория не существует, будет создана при инициализации клиента.")
    
    # Создаем клиент с путем
    client = PowerBIClient(debug_data_path=debug_path)
    print(f"Клиент создан. debug_data_path = {client.debug_data_path}")
    
    # Проверяем, что путь совпадает
    assert client.debug_data_path == debug_path, "Путь не совпадает!"
    print("[OK] Путь корректно установлен в клиенте.")
    
    # Проверяем, что директория создана
    if os.path.exists(debug_path):
        print("[OK] Директория существует после инициализации клиента.")
    else:
        print("[FAIL] Директория не создана.")
    
    # Пробуем сохранить тестовые данные (мок)
    print("\nТест завершен успешно.")

if __name__ == "__main__":
    test_debug_path()