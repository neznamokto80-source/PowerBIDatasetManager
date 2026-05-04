#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль управления зависимостями проекта.
Автоматически проверяет и устанавливает необходимые пакеты.
"""

import subprocess
import sys
import os
from typing import List, Tuple


class DependencyManager:
    """Класс для управления зависимостями Python-пакетов."""
    
    # Список необходимых пакетов: (имя пакета для pip, импортируемое имя модуля)
    REQUIRED_PACKAGES = [
        ("azure-identity", "azure.identity"),
        ("requests", "requests"),
        ("python-dateutil", "dateutil"),
    ]
    
    @classmethod
    def ensure_dependencies(cls) -> None:
        """
        Проверяет наличие всех зависимостей и при необходимости устанавливает их.
        После установки перезапускает скрипт для применения изменений.
        """
        missing = cls._find_missing_packages()
        
        if not missing:
            print("✓ Все зависимости установлены.")
            return
        
        print(f"Обнаружены отсутствующие библиотеки ({len(missing)}):")
        for package, module_name in missing:
            print(f"  - {package} (модуль: {module_name})")
        
        print("\nУстановка недостающих пакетов...")
        cls._install_missing_packages(missing)
        
        # Перезапускаем скрипт, чтобы новые библиотеки гарантированно подхватились
        print("\nПерезапуск скрипта с установленными зависимостями...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    @classmethod
    def _find_missing_packages(cls) -> List[Tuple[str, str]]:
        """Находит отсутствующие пакеты."""
        missing = []
        for package, module_name in cls.REQUIRED_PACKAGES:
            try:
                __import__(module_name)
            except ImportError:
                missing.append((package, module_name))
        return missing
    
    @classmethod
    def _install_missing_packages(cls, missing: List[Tuple[str, str]]) -> None:
        """Устанавливает отсутствующие пакеты."""
        for package, _ in missing:
            print(f"  Устанавливаю {package}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--user", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"  ✓ {package} установлен.")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ Ошибка установки {package}: {e}")
                # Пробуем установить без --user
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", package],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"  ✓ {package} установлен (без --user).")
                except subprocess.CalledProcessError as e2:
                    print(f"  ✗ Критическая ошибка установки {package}: {e2}")
                    raise
    
    @classmethod
    def add_package(cls, package_name: str, module_name: str) -> None:
        """
        Добавляет пакет в список зависимостей.
        
        Args:
            package_name: Имя пакета для pip install
            module_name: Имя модуля для импорта
        """
        cls.REQUIRED_PACKAGES.append((package_name, module_name))
    
    @classmethod
    def get_required_packages(cls) -> List[Tuple[str, str]]:
        """Возвращает список требуемых пакетов."""
        return cls.REQUIRED_PACKAGES.copy()


def ensure_dependencies():
    """Функция-обертка для обратной совместимости."""
    DependencyManager.ensure_dependencies()


if __name__ == "__main__":
    # Тестирование модуля
    print("Тестирование модуля зависимостей...")
    print(f"Требуемые пакеты: {DependencyManager.get_required_packages()}")
    DependencyManager.ensure_dependencies()
    print("Тест завершен.")