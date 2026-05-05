#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа приложения Power BI Dataset Monitor & Manager.
Запускает графический интерфейс на основе PyQt6.
"""

import sys
import os
import logging
import importlib.util

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("powerbi_monitor.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Добавляем текущую директорию в путь для импорта src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_dependency_manager():
    """Динамически загружает DependencyManager, избегая циклических импортов."""
    # Путь к модулю dependencies
    deps_path = os.path.join(os.path.dirname(__file__), 'src', 'core', 'dependencies.py')
    if not os.path.exists(deps_path):
        raise ImportError(f"Файл не найден: {deps_path}")
    
    # Динамическая загрузка модуля
    spec = importlib.util.spec_from_file_location("dependencies", deps_path)
    deps_module = importlib.util.module_from_spec(spec)
    sys.modules["dependencies"] = deps_module
    spec.loader.exec_module(deps_module)
    
    # Получаем класс DependencyManager
    if hasattr(deps_module, 'DependencyManager'):
        return deps_module.DependencyManager
    else:
        raise AttributeError("Класс DependencyManager не найден в модуле")

# Проверка и установка зависимостей перед импортом PyQt6
try:
    DependencyManager = load_dependency_manager()
    DependencyManager.ensure_dependencies()
except Exception as e:
    logging.error(f"Ошибка при проверке зависимостей: {e}")
    logging.error("Установите зависимости вручную: pip install -r requirements.txt")
    sys.exit(1)

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import PowerBIMonitorUI


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    
    # Настройка стиля
    app.setStyle("Fusion")
    
    # Создание и отображение главного окна
    window = PowerBIMonitorUI()
    window.show()
    
    # Запуск основного цикла приложения
    sys.exit(app.exec())


if __name__ == "__main__":
    main()