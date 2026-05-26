# Руководство по использованию Power BI Report Server

## Обзор

Приложение Power BI Dataset Monitor & Manager теперь поддерживает работу с двумя типами серверов:
1. **Power BI Service (облако)** - стандартное облачное решение Microsoft
2. **Power BI Report Server (локальный)** - локальный сервер отчетов для корпоративных сред

## Установка зависимостей

Для работы с Power BI Report Server требуется дополнительная библиотека:

```bash
pip install requests_ntlm2>=0.2.0
```

Все зависимости указаны в файле `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Подключение к Power BI Report Server

### Способ 1: Через интерфейс
1. Запустите приложение
2. Нажмите кнопку **"Подключить Power BI Report Server"** в верхней панели
3. Введите URL сервера (например: `http://PBIRSServer/Reports` или `http://localhost/Reports`)
4. Выберите метод аутентификации:
   - **Использовать текущего пользователя Windows** - для доменных сред
   - **Ввести логин и пароль** - для указания конкретных учетных данных

### Способ 2: Программно
```python
from src.core.powerbi_report_server_client import PowerBIReportServerClient
from src.core.refresh_manager_pbirs import PBIRSRefreshManager

# Создание клиента
client = PowerBIReportServerClient(
    server_url="http://PBIRSServer/Reports",
    username="DOMAIN\\username",  # опционально
    password="password"           # опционально
)

# Проверка подключения
if client.test_connection():
    print("Подключение успешно")
    
    # Получение отчетов
    reports = client.get_powerbi_reports()
    print(f"Найдено отчетов: {len(reports)}")
```

## Основные отличия от Power BI Service

### 1. Аутентификация
- **Power BI Service**: OAuth 2.0 через Azure AD
- **Power BI Report Server**: NTLM/Kerberos через Windows Authentication

### 2. API Endpoints
- **Power BI Service**: `https://api.powerbi.com/v1.0/myorg`
- **Power BI Report Server**: `http://сервер/Reports/api/v2.0`

### 3. Управление обновлениями
- **Power BI Service**: Refresh Schedules (расписания обновления)
- **Power BI Report Server**: Cache Refresh Plans (планы обновления кэша)

### 4. Терминология
- **Power BI Service**: Рабочие области (Workspaces) → Датасеты (Datasets)
- **Power BI Report Server**: Папки (Folders) → Отчеты (Reports) → Планы обновления кэша

## Основные функции PBIRS

### Получение отчетов
```python
reports = client.get_powerbi_reports()
for report in reports:
    print(f"ID: {report.get('Id')}, Name: {report.get('Name')}")
```

### Управление планами обновления кэша
```python
# Получение планов для отчета
plans = client.get_cache_refresh_plans(report_id)

# Создание плана
plan_data = {
    "Description": "Ежедневное обновление",
    "EventType": "TimedSubscription",
    "Schedule": {...}
}
client.create_cache_refresh_plan(report_id, plan_data)

# Запуск плана
client.execute_cache_refresh_plan(plan_id)
```

### Менеджер обновлений
```python
from src.core.refresh_manager_pbirs import PBIRSRefreshManager

manager = PBIRSRefreshManager(client)

# Включение/отключение плана
manager.enable_cache_refresh_plan(plan_id)
manager.disable_cache_refresh_plan(plan_id)

# Создание расписания
manager.create_cache_refresh_plan(
    report_id="report123",
    plan_name="Ежедневное обновление",
    days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    times=["08:00", "20:00"]
)
```

## Устранение неполадок

### Ошибка 401 (Unauthorized)
1. Проверьте правильность URL сервера
2. Убедитесь, что учетная запись имеет доступ к серверу
3. Попробуйте указать явные учетные данные (логин/пароль)

### Ошибка импорта `requests_ntlm2`
```bash
pip install requests_ntlm2
```

### Ошибка подключения
1. Проверьте доступность сервера: `ping PBIRSServer`
2. Проверьте правильность URL: должен заканчиваться на `/Reports`
3. Убедитесь, что сервер поддерживает API v2.0

## Конфигурация

### Переменные окружения (опционально)
```
PBIRS_SERVER_URL=http://localhost/Reports
PBIRS_USERNAME=DOMAIN\\user
PBIRS_PASSWORD=secret
```

### Файл конфигурации
Можно создать файл `.env` в корне проекта:
```
PBIRS_SERVER_URL=http://PBIRSServer/Reports
PBIRS_USE_CURRENT_USER=true
```

## Ограничения

1. **Только отчеты Power BI** - PBIRS также поддерживает SQL Server Reporting Services (SSRS), но текущая реализация работает только с отчетами Power BI
2. **Требуется Windows** - NTLM аутентификация оптимально работает в среде Windows
3. **API v2.0** - требуется Power BI Report Server с поддержкой API v2.0

## Дальнейшее развитие

1. **Поддержка SSRS отчетов** - расширение для работы с SQL Server Reporting Services
2. **Гибридный режим** - одновременная работа с облачным и локальным сервером
3. **Импорт/экспорт конфигураций** - миграция настроек между серверами
4. **Мониторинг в реальном времени** - отслеживание выполнения планов обновления