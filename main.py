#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа приложения Power BI Dataset Monitor & Manager.
Запускает графический интерфейс на основе PyQt5 (тема Catppuccin).
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
        "PyQt5",
        "azure-identity",
        "azure-core",
        "msal",
        "requests",
        "python-dateutil",
    ]
    missing = []
    for package in required_packages:
        # Пробуем импортировать (для PyQt5 особый случай)
        if package == "PyQt5":
            try:
                __import__("PyQt5")
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

# Теперь можно импортировать PyQt5 и остальные модули
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import PowerBIMonitorUI
from src.ui.theme_colors import apply_theme_to_app
from src.ui.themes import DEFAULT_THEME_NAME


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    # Применяем тему по умолчанию (Catppuccin) до создания окна
    apply_theme_to_app(DEFAULT_THEME_NAME)
    window = PowerBIMonitorUI()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()