#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа приложения Power BI Dataset Monitor & Manager.
Запускает графический интерфейс на основе PyQt6.
"""

import sys
import os
import subprocess
import logging

# Настройка логирования (в файл и в консоль, если консоль есть)
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


def ensure_dependencies():
    """Проверяет и устанавливает необходимые пакеты без перезапуска процесса."""
    required_packages = [
        "PyQt6",
        "azure-identity",
        "azure-core",
        "msal",
        "requests",
        "python-dateutil",
    ]
    missing = []
    for package in required_packages:
        # Пробуем импортировать (для PyQt6 особый случай)
        if package == "PyQt6":
            try:
                __import__("PyQt6")
            except ImportError:
                missing.append(package)
        else:
            # Для остальных используем имя модуля, которое может отличаться
            module_map = {
                "azure-identity": "azure.identity",
                "azure-core": "azure.core",
                "msal": "msal",
                "requests": "requests",
                "python-dateutil": "dateutil",
            }
            module_name = module_map.get(package, package)
            try:
                __import__(module_name)
            except ImportError:
                missing.append(package)

    if not missing:
        logging.info("Все зависимости уже установлены.")
        return True

    logging.warning(f"Отсутствуют пакеты: {missing}. Установка...")
    try:
        for pkg in missing:
            logging.info(f"Установка {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        logging.info("Все пакеты установлены успешно.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка установки пакетов: {e}")
        return False


# Проверка зависимостей
if not ensure_dependencies():
    logging.error("Не удалось установить необходимые пакеты. Завершение.")
    # Пауза на случай запуска двойным кликом (чтобы увидеть ошибку)
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Теперь можно импортировать PyQt6 и остальные модули
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import PowerBIMonitorUI


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PowerBIMonitorUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()