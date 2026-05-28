import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import xml.etree.ElementTree as ET

REPORT_SERVER = "http://noutdell/Reports"
REPORT_PATH = "/22"  # уточните путь, возможно "/22" или "/Папка/22"
NEW_USERNAME = "sql"
NEW_PASSWORD = "123456"

auth = HttpNegotiateAuth()
soap_url = f"{REPORT_SERVER}/ReportServer/ReportService2010.asmx"

# 1. Получить текущие источники данных
get_body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetItemDataSources xmlns="http://schemas.microsoft.com/sqlserver/reporting/2010/03/01/ReportServer">
      <ItemPath>{REPORT_PATH}</ItemPath>
    </GetItemDataSources>
  </soap:Body>
</soap:Envelope>'''

headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "http://schemas.microsoft.com/sqlserver/reporting/2010/03/01/ReportServer/GetItemDataSources"}
resp = requests.post(soap_url, data=get_body.encode('utf-8'), headers=headers, auth=auth)

if resp.status_code != 200:
    print("Ошибка получения источников:", resp.status_code)
    print(resp.text)
    exit(1)

# Парсим ответ
ns = {"rs": "http://schemas.microsoft.com/sqlserver/reporting/2010/03/01/ReportServer"}
root = ET.fromstring(resp.content)
data_sources = root.findall(".//rs:DataSource", ns)

if not data_sources:
    print("Источники данных не найдены.")
    exit(0)

for ds in data_sources:
    ds_name = ds.find("rs:Name", ns).text
    ds_def = ds.find("rs:DataSourceDefinition", ns)
    extension = ds_def.find("rs:Extension", ns).text
    conn_string = ds_def.find("rs:ConnectString", ns).text if ds_def.find("rs:ConnectString", ns) is not None else ""

    print(f"Обновляем источник: {ds_name}")

    # 2. Установить новые учётные данные
    set_body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SetItemDataSources xmlns="http://schemas.microsoft.com/sqlserver/reporting/2010/03/01/ReportServer">
      <ItemPath>{REPORT_PATH}</ItemPath>
      <DataSources>
        <DataSource>
          <Name>{ds_name}</Name>
          <DataSourceDefinition>
            <Extension>{extension}</Extension>
            <ConnectString>{conn_string}</ConnectString>
            <UseOriginalConnectString>false</UseOriginalConnectString>
            <OriginalConnectStringExpressionBased>false</OriginalConnectStringExpressionBased>
            <CredentialRetrieval>Store</CredentialRetrieval>
            <UserName>{NEW_USERNAME}</UserName>
            <Password>{NEW_PASSWORD}</Password>
            <WindowsCredentials>false</WindowsCredentials>
            <ImpersonateUser>false</ImpersonateUser>
            <Prompt>null</Prompt>
          </DataSourceDefinition>
        </DataSource>
      </DataSources>
    </SetItemDataSources>
  </soap:Body>
</soap:Envelope>'''

    headers2 = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "http://schemas.microsoft.com/sqlserver/reporting/2010/03/01/ReportServer/SetItemDataSources"}
    resp2 = requests.post(soap_url, data=set_body.encode('utf-8'), headers=headers2, auth=auth)
    if resp2.status_code in (200, 204):
        print(f"  Источник {ds_name} успешно обновлён.")
    else:
        print(f"  Ошибка обновления: {resp2.status_code}")
        print(resp2.text[:500])