import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import json
from urllib.parse import quote

# ===================== НАСТРОЙКИ =====================
REPORT_SERVER_URL = "http://noutdell/Reports"
REPORT_NAME = "22"

# Формируем корректный URL с $expand=DataSources и $filter по имени
filter_str = f"Name eq '{REPORT_NAME}'"
encoded_filter = quote(filter_str, safe='')
url = (f"{REPORT_SERVER_URL}/api/v2.0/PowerBIReports"
       f"?$expand=DataSources"
       f"&$filter={encoded_filter}")

auth = HttpNegotiateAuth()

print(f"Запрос: {url}\n")
response = requests.get(url, auth=auth)

if response.status_code != 200:
    print(f"Ошибка: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
reports = data.get('value', [])
if not reports:
    print(f"Отчёт с именем '{REPORT_NAME}' не найден.")
    exit(0)

for report in reports:
    print(f"Отчёт: {report.get('Name')} (ID: {report.get('Id')})")
    datasources = report.get('DataSources', [])
    if not datasources:
        print("  Нет источников данных.\n")
        continue

    for ds in datasources:
        print(f"  Источник данных: {ds.get('Name', 'Без имени')} (ID: {ds.get('Id')})")
        
        # Интересующие поля из корня источника
        fields = [
            "IsConnectionStringOverridden",
            "CredentialRetrieval",
            "CredentialsByUser",
            "CredentialsInServer",
            "IsReference",
            "DataSourceSubType",
            "ConnectionString",
            "Type",
            "CreatedBy",
            "ModifiedBy",
            "ModifiedDate",
            "CreatedDate"
        ]
        for f in fields:
            value = ds.get(f)
            if value is not None:
                print(f"    {f}: {value}")
        
        # Вложенный объект DataModelDataSource (приходит без expand)
        dmd = ds.get('DataModelDataSource', {})
        if dmd:
            print("    DataModelDataSource:")
            for key in ['Type', 'Kind', 'AuthType', 'SupportedAuthTypes', 'Username',
                        'Secret', 'ModelConnectionName', 'EnableEncryptConnection',
                        'IsDataSourceSupportEncryption']:
                val = dmd.get(key)
                if val is not None:
                    print(f"      {key}: {val}")
        print("")
    print("---\n")