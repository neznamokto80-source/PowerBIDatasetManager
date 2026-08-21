@echo off
:: Переключаем кодировку на Windows-1251 для поддержки кириллицы
chcp 1251 >nul
setlocal enabledelayedexpansion

:: === НАСТРОЙКИ ===
set "APP_NAME=main"
set "OUTPUT_NAME=PBI_DATA_MANAGER"
:: =================

title Компиляция: %APP_NAME% -> %OUTPUT_NAME%.exe

echo ========================================
echo    Исходник:  %APP_NAME%.py
echo    Выходной:  %OUTPUT_NAME%.exe
echo ========================================

:: 1. Установка PyInstaller при необходимости
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Установка PyInstaller...
    pip install pyinstaller
)

:: 2. Установка зависимостей (из pyproject.toml)
echo [PKG] Установка зависимостей...
python -m pip install -e .

:: 3. Очистка предыдущих сборок
echo [CLEAN] Очистка временных файлов...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%OUTPUT_NAME%.spec" del /q "%OUTPUT_NAME%.spec"

:: 4. Компиляция
echo [BUILD] Компиляция...
python -m PyInstaller --onefile ^
    --name "%OUTPUT_NAME%" ^
    --console ^
    --hidden-import PyQt5 ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import azure.identity ^
    --hidden-import msal ^
    --hidden-import requests ^
    --collect-all ^
    --add-data "src;src" ^
    --clean ^
    "%APP_NAME%.py"

:: 5. Если компиляция успешна – копируем и чистим
if exist "dist\%OUTPUT_NAME%.exe" (
    echo [OK] Копирование в текущую папку...
    copy "dist\%OUTPUT_NAME%.exe" . >nul
    echo [DEL] Удаление временных файлов...
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    if exist "%OUTPUT_NAME%.spec" del /q "%OUTPUT_NAME%.spec"
    echo.
    echo ========================================
    echo    ГОТОВО!
    echo    Файл: %CD%\%OUTPUT_NAME%.exe
    echo ========================================
) else (
    echo [FAIL] Ошибка: EXE не создан.
)

pause
