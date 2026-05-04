#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа приложения Power BI Dataset Monitor & Manager.
Запускает графический интерфейс на основе PyQt6.
"""

import sys
import os
import logging

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