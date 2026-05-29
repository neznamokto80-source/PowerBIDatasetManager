# План: Управление отчётами PBIRS (загрузка/удаление/скачивание)

## Цель
Добавить функционал загрузки на сервер, удаления и скачивания отчётов PBIRS:
- **Вкладка "Отчёты PBIRS"** — через контекстное меню таблицы
- **Вкладка "Детали PBIRS"** — через кнопки рядом с блоком "Информация об Отчете"
- Кнопки/меню должны быть неактивны, если у пользователя нет прав

## API эндпоинты (на основе документации пользователя)

### Скачивание отчёта
- **Power BI Reports (.pbix):** `GET /PowerBIReports({Id})/Content/$value` — бинарный контент
- **Paginated Reports (.rdl):** `GET /Reports({Id})/Content/$value` — бинарный контент

### Удаление отчёта
- `DELETE /PowerBIReports({Id})` — удаление Power BI отчёта
- `DELETE /Reports({Id})` — удаление SSRS отчёта

### Загрузка нового отчёта (два этапа)
1. **Создание записи отчёта:** `POST /PowerBIReports` с JSON `{"Name": "...", "Path": "/folder/name"}`
   - Ответ содержит `Id` созданного отчёта
2. **Загрузка содержимого:** `POST /PowerBIReports({Id})/Model.Upload` с `multipart/form-data`, параметр `File`

### Проверка прав доступа
- **Рекомендуемый способ:** `GET /CatalogItems({ItemId})/Policies` или `GET /PowerBIReports({ReportId})/Policies`
  - Возвращает список ролей для пользователя/группы
  - Роль `Content Manager` даёт полные права
  - Роль `Browser` — только просмотр
- **Недокументированный:** `GET /PowerBIReports(Path='...')/AllowedActions` — может быть нестабильным

## Файлы для изменения

| Файл | Изменения |
|------|-----------|
| `src/core/powerbi_report_server_client.py` | +5 методов: delete, download_content, create_report, upload_content, check_permissions |
| `src/operations/pbirs_operations.py` | +5 методов-обёрток с диалогами и логированием |
| `src/operations/ui_operations.py` | +1 метод контекстного меню, доработка _set_pbirs_buttons_enabled, _update_pbirs_details_fields, _clear_pbirs_details_fields |
| `src/ui/ui_panels.py` | +контекстное меню для таблицы отчётов, +2 кнопки на вкладку деталей |
| `src/ui/main_window.py` | +прокси-методы для новых действий |

## Детальный план реализации

### Шаг 1: Методы API в PowerBIReportServerClient

1. `download_report_content(report_id, report_type="PowerBIReports") -> bytes`
   - `GET {report_type}({report_id})/Content/$value`
   - Возвращает бинарные данные (сырой response.content)

2. `delete_report(report_id, report_type="PowerBIReports")`
   - `DELETE {report_type}({report_id})`

3. `create_report(name, path) -> str (report_id)`
   - `POST PowerBIReports` с `{"Name": name, "Path": path}`
   - Возвращает `Id` из ответа

4. `upload_report_content(report_id, file_path)`
   - `POST PowerBIReports({report_id})/Model.Upload` с multipart/form-data

5. `check_report_permissions(report_id) -> bool`
   - `GET PowerBIReports({report_id})/Policies`
   - Проверяет, есть ли у текущего пользователя роль Content Manager
   - Если API недоступен — возвращает True (разрешаем, ошибка будет при действии)

### Шаг 2: Методы-обёртки в PBIRSOperations

1. `download_pbirs_report(report_id, report_name, report_type="PowerBIReports")`
   - Вызывает client.download_report_content()
   - Открывает QFileDialog для сохранения
   - Сохраняет файл

2. `delete_pbirs_report(report_id, report_name, report_type="PowerBIReports")`
   - Показывает QMessageBox подтверждения
   - Вызывает client.delete_report()
   - Перезагружает список отчётов

3. `upload_pbirs_report()`
   - Открывает QFileDialog для выбора .pbix файла
   - Запрашивает путь на сервере (QInputDialog)
   - Вызывает client.create_report() + client.upload_report_content()
   - Перезагружает список отчётов

4. `check_pbirs_report_permissions(report_id) -> bool`
   - Вызывает client.check_report_permissions()

### Шаг 3: Контекстное меню для таблицы отчётов PBIRS

**ui_panels.py:** Добавить `setContextMenuPolicy` для `pbirs_reports_table`
**main_window.py:** Добавить прокси-метод `show_pbirs_reports_context_menu`
**ui_operations.py:** Реализовать `show_pbirs_reports_context_menu`:
- Получить выбранный отчёт
- Создать QMenu: "Скачать отчет", "Удалить отчет", "Загрузить отчет на сервер"
- Проверить права и отключить пункты если нет прав

### Шаг 4: Кнопки на вкладку "Детали PBIRS"

**ui_panels.py:** В верхнюю панель добавить кнопки "Скачать" и "Удалить"
**main_window.py:** Прокси-методы
**ui_operations.py:** 
- В `_set_pbirs_buttons_enabled` добавить управление новыми кнопками
- В `_update_pbirs_details_fields` проверять права и включать/отключать кнопки
- В `_clear_pbirs_details_fields` отключать кнопки

### Шаг 5: Проверка прав

- При выборе отчёта (в `on_pbirs_details_report_selected`) вызывать `check_pbirs_report_permissions`
- При показе контекстного меню — проверять права для выбранного отчёта
- Результат кешировать в `self.main_window.pbirs_report_permissions` (словарь report_id -> bool)