#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка standalone .exe приложения Power BI Dataset Monitor & Manager.

Использует PyInstaller:
  - предварительно очищает все артефакты предыдущей сборки (build/, dist/,
    *.spec, готовый .exe в корне проекта)
  - компилирует main.py в один файл (--onefile)
  - включает скрытые импорты PyQt5, azure.identity, msal, requests
  - добавляет каталог src как пакет данных
  - при необходимости устанавливает зависимости из pyproject.toml

Запуск:
    python build-exe.py
"""

import os
import shutil
import subprocess
import sys

APP_NAME = "main"
OUTPUT_NAME = "PBI_DATA_MANAGER"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd, description):
    """Выполняет команду и печатает статус."""
    print(f"\n[{description}] Выполнение: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode != 0:
        print(f"\n[ОШИБКА] Шаг «{description}» завершился с кодом {result.returncode}")
        sys.exit(result.returncode)
    return result


def clean_build_artifacts():
    """Удаляет все артефакты предыдущей сборки (build/, dist/, *.spec, готовый exe)."""
    print("\n[CLEAN] Очистка предыдущей сборки...")

    # Каталоги и файлы PyInstaller
    for path in ["build", "dist", f"{OUTPUT_NAME}.spec"]:
        full = os.path.join(ROOT_DIR, path)
        if os.path.isdir(full):
            shutil.rmtree(full, ignore_errors=True)
            print(f"[CLEAN] Удалён каталог {path}")
        elif os.path.isfile(full):
            os.remove(full)
            print(f"[CLEAN] Удалён файл {path}")

    # Ранее собранный exe в корне проекта
    prev_exe = os.path.join(ROOT_DIR, f"{OUTPUT_NAME}.exe")
    if os.path.isfile(prev_exe):
        os.remove(prev_exe)
        print(f"[CLEAN] Удалён ранее собранный {OUTPUT_NAME}.exe")

    print("[CLEAN] Готово.")


def ensure_pyinstaller():
    """Проверяет наличие PyInstaller и устанавливает при необходимости."""
    try:
        import PyInstaller  # noqa: F401
        print("[OK] PyInstaller уже установлен.")
    except ImportError:
        print("[!] PyInstaller не найден — установка...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"], "Установка PyInstaller")


def install_dependencies():
    """Устанавливает зависимости проекта из pyproject.toml (editable)."""
    run([sys.executable, "-m", "pip", "install", "-e", "."], "Установка зависимостей (pyproject.toml)")


def build_exe():
    """Запускает PyInstaller для сборки standalone exe."""
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name", OUTPUT_NAME,
        "--console",
        # Скрытые импорты PyQt5
        "--hidden-import", "PyQt5",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui",
        "--hidden-import", "PyQt5.QtWidgets",
        # Скрытые импорты сторонних библиотек
        "--hidden-import", "azure.identity",
        "--hidden-import", "msal",
        "--hidden-import", "requests",
        # Данные: каталог src
        "--add-data", f"src{os.pathsep}src",
        "--clean",
        os.path.join(ROOT_DIR, f"{APP_NAME}.py"),
    ]
    run(cmd, "Компиляция PyInstaller")

    exe_path = os.path.join(ROOT_DIR, "dist", f"{OUTPUT_NAME}.exe")
    if os.path.isfile(exe_path):
        dest = os.path.join(ROOT_DIR, f"{OUTPUT_NAME}.exe")
        shutil.copy2(exe_path, dest)
        print(f"\n[OK] Готово! Исполняемый файл: {dest}")

        # Очистка временных артефактов
        clean_build_artifacts()
    else:
        print("\n[ОШИБКА] Файл .exe не создан.")
        sys.exit(1)


def main():
    print("=" * 60)
    print(f"   Сборка: {APP_NAME}.py -> {OUTPUT_NAME}.exe")
    print("=" * 60)

    # Предварительная очистка предыдущей сборки
    clean_build_artifacts()

    ensure_pyinstaller()
    install_dependencies()
    build_exe()


if __name__ == "__main__":
    main()