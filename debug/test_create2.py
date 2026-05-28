import subprocess
import sys
import importlib
import json
from datetime import datetime, timedelta, timezone

# --- Проверка и установка библиотек (как в предыдущем примере) ---
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    importlib.import_module("requests")
except ImportError:
    install_package("requests")

try:
    importlib.import_module("requests_negotiate_sspi")
except ImportError:
    install_package("requests-negotiate-sspi")

try:
    importlib.import_module("win32api")
except ImportError:
    install_package("pywin32")
    install_package("pypiwin32")
    try:
        subprocess.check_call([sys.executable, "-m", "pywin32_postinstall", "-install"])
    except:
        print("⚠️ Запустите вручную: python -m pywin32_postinstall -install")

import requests
from requests_negotiate_sspi import HttpNegotiateAuth

# --- Настройки ---
report_server_url = "http://noutdell/Reports"
catalog_item_path = "/tets"          # путь к отчёту из полученных расписаний
description = "new_refresh"          # новое описание

# Формируем StartDateTime: завтра в 02:00 по местному времени (UTC+5)
# Определяем смещение вручную, если сервер использует +05:00
local_tz = timezone(timedelta(hours=5))
start_time = datetime.now(local_tz).replace(hour=2, minute=0, second=0, microsecond=0)
if start_time <= datetime.now(local_tz):
    start_time += timedelta(days=1)
start_datetime_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")  # без зоны, сервер сам добавит?
# В примере ответа было "2026-05-26T02:00:00+05:00" – значит можно передать с +05:00
start_datetime_with_tz = start_time.strftime("%Y-%m-%dT%H:%M:%S+05:00")

# --- Тело запроса (как у sql_refresh) ---
payload = {
    "CatalogItemPath": catalog_item_path,
    "EventType": "DataModelRefresh",
    "Description": description,
    "Schedule": {
        "Definition": {
            "StartDateTime": start_datetime_with_tz,  # завтра в 02:00 UTC+5
            "EndDateSpecified": False,
            "Recurrence": {
                "DailyRecurrence": {
                    "DaysInterval": 1
                }
            }
        }
    },
    "ParameterValues": []   # без параметров
}

# --- URL и аутентификация ---
base_api_url = f"{report_server_url}/api/v2.0"
url = f"{base_api_url}/CacheRefreshPlans"
auth = HttpNegotiateAuth()

headers = {"Content-Type": "application/json"}

# --- Отправка POST-запроса ---
try:
    response = requests.post(url, auth=auth, headers=headers, data=json.dumps(payload))
    if response.status_code == 201:   # Created
        print("✅ Расписание успешно создано.")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    else:
        print(f"❌ Ошибка при создании. Код: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"⚠️ Исключение: {e}")