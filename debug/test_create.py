import subprocess
import sys
import importlib

# --- Функция для установки недостающих библиотек ---
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# --- Проверяем и устанавливаем requests (если нет) ---
try:
    importlib.import_module("requests")
    print("✅ requests уже установлен")
except ImportError:
    print("📦 Устанавливаю requests...")
    install_package("requests")

# --- Проверяем и устанавливаем requests-negotiate-sspi ---
try:
    importlib.import_module("requests_negotiate_sspi")
    print("✅ requests_negotiate_sspi уже установлен")
except ImportError:
    print("📦 Устанавливаю requests-negotiate-sspi...")
    install_package("requests-negotiate-sspi")

# --- Проверяем и устанавливаем pywin32 и pypiwin32 ---
try:
    importlib.import_module("win32api")
    print("✅ pywin32 уже установлен")
except ImportError:
    print("📦 Устанавливаю pywin32...")
    install_package("pywin32")
    print("📦 Устанавливаю pypiwin32...")
    install_package("pypiwin32")

    # --- Запускаем скрипт пост-установки для pywin32 ---
    # Это критически важный шаг для правильной регистрации библиотек в системе[reference:2].
    print("🔧 Запускаю скрипт завершения установки pywin32...")
    try:
        # Команда для запуска скрипта завершения установки от имени администратора.
        # В среде разработки, возможно, потребуется запустить терминал с правами администратора.
        subprocess.check_call([sys.executable, "-m", "pywin32_postinstall", "-install"])
        print("✅ pywin32 успешно настроен.")
    except Exception as e:
        print(f"⚠️ Не удалось автоматически запустить скрипт завершения установки: {e}")
        print("Пожалуйста, запустите вручную от имени администратора: python -m pywin32_postinstall -install")

# --- Импортируем библиотеки ---
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import json

# --- Настройки подключения ---
report_server_url = "http://noutdell/Reports"   # URL портала PBIRS
report_id = "a5730c22-5987-465c-af80-57c9b328ea08"

base_api_url = f"{report_server_url}/api/v2.0"
url = f"{base_api_url}/PowerBIReports({report_id})/CacheRefreshPlans"

# --- Аутентификация через текущего пользователя Windows ---
auth = HttpNegotiateAuth()

print(f"🔍 Запрашиваю расписания для отчёта {report_id}...")

try:
    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        print("✅ Расписания успешно получены.")
        data = response.json()
        print(json.dumps(data, indent=4, ensure_ascii=False))
    else:
        print(f"❌ Ошибка при получении расписаний. Код: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("⚠️ Не удалось подключиться к серверу. Проверьте URL и доступность сети.")
except Exception as e:
    print(f"⚠️ Произошла ошибка: {e}")