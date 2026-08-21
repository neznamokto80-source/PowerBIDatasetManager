#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль управления зависимостями проекта.
Автоматически проверяет и устанавливает необходимые пакеты.
"""

import subprocess
import sys
import os
import logging
from typing import List, Tuple

# Настройка логирования
logger = logging.getLogger(__name__)


class DependencyManager:
    """Класс для управления зависимостями Python-пакетов."""
    
    # Список необходимых пакетов: (имя пакета для pip, импортируемое имя модуля)
    REQUIRED_PACKAGES = [
        ("azure-identity", "azure.identity"),
        ("azure-core", "azure.core"),
        ("msal", "msal"),
        ("requests", "requests"),
        ("python-dateutil", "dateutil"),
        ("PyQt5", "PyQt5"),
        ("requests_ntlm", "requests_ntlm"),
    ]
    
    @classmethod
    def ensure_dependencies(cls, auto_restart: bool = True) -> None:
        """
        Проверяет наличие всех зависимостей и при необходимости устанавливает их.
        
        Args:
            auto_restart: Автоматически перезапускать скрипт после установки
        """
        missing = cls._find_missing_packages()
        
        if not missing:
            logger.info("Все зависимости установлены.")
            return
        
        logger.warning(f"Обнаружены отсутствующие библиотеки ({len(missing)}):")
        for package, module_name in missing:
            logger.warning(f"  - {package} (модуль: {module_name})")
        
        logger.info("Установка недостающих пакетов...")
        cls._install_missing_packages(missing)
        
        if auto_restart:
            # Перезапускаем скрипт, чтобы новые библиотеки гарантированно подхватились
            logger.info("Перезапуск скрипта с установленными зависимостями...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
    
    @classmethod
    def _find_missing_packages(cls) -> List[Tuple[str, str]]:
        """Находит отсутствующие пакеты."""
        missing = []
        for package, module_name in cls.REQUIRED_PACKAGES:
            if not cls._is_module_available(module_name):
                missing.append((package, module_name))
        return missing
    
    @staticmethod
    def _is_module_available(module_name: str) -> bool:
        """Проверяет, доступен ли модуль для импорта."""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    @classmethod
    def _install_missing_packages(cls, missing: List[Tuple[str, str]]) -> None:
        """Устанавливает отсутствующие пакеты."""
        for package, module_name in missing:
            logger.info(f"Установка {package}...")
            success = cls._install_package(package)
            if success:
                logger.info(f"✓ {package} успешно установлен.")
            else:
                logger.error(f"✗ Не удалось установить {package}.")
                raise RuntimeError(f"Не удалось установить зависимость: {package}")
    
    @staticmethod
    def _install_package(package_name: str) -> bool:
        """Устанавливает пакет через pip."""
        install_options = [
            [sys.executable, "-m", "pip", "install", package_name],
            [sys.executable, "-m", "pip", "install", "--user", package_name],
        ]
        
        for cmd in install_options:
            try:
                subprocess.check_call(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            except subprocess.CalledProcessError:
                continue
        
        return False
    
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
    
    @classmethod
    def check_requirements_file(cls, requirements_path: str = "requirements.txt") -> bool:
        """
        Проверяет, соответствует ли файл requirements.txt текущим зависимостям.
        
        Args:
            requirements_path: Путь к файлу requirements.txt
            
        Returns:
            True если файл существует и содержит все зависимости
        """
        if not os.path.exists(requirements_path):
            logger.warning(f"Файл {requirements_path} не найден.")
            return False
        
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_packages = {pkg for pkg, _ in cls.REQUIRED_PACKAGES}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                # Извлекаем имя пакета (до == или >= и т.д.)
                pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                if pkg_name in required_packages:
                    required_packages.remove(pkg_name)
        
        return len(required_packages) == 0


def ensure_dependencies():
    """Функция-обертка для обратной совместимости."""
    DependencyManager.ensure_dependencies()


if __name__ == "__main__":
    # Тестирование модуля
    logging.basicConfig(level=logging.INFO)
    print("Тестирование модуля зависимостей...")
    print(f"Требуемые пакеты: {DependencyManager.get_required_packages()}")
    DependencyManager.ensure_dependencies(auto_restart=False)
    print("Тест завершен.")