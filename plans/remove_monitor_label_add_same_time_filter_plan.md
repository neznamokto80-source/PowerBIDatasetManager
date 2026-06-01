# План: Убрать надпись "Мониторинг (периодичность опроса)" и добавить фильтр "Одинаковое время обновления"

## Часть 1: Убрать надпись "Мониторинг (периодичность опроса)"

### Суть изменений
- Убрать строку "Мониторинг не активен / Мониторинг активен" (label `monitor_status`)
- Логику цвета при запуске/остановке мониторинга перенести в заголовок группы

### Файлы изменений

#### 1. `src/ui/ui_panels.py`

**1.1 Удалить `monitor_status` label (строки 127-128)**
```python
# Было:
self.main.monitor_status = create_label("Мониторинг не активен")
monitor_layout.addWidget(self.main.monitor_status)

# Стало: удалить обе строки
```

#### 2. `src/ui/main_window.py`

**2.1 Изменить метод `_update_monitor_group_title()` (строки 933-942)**

Перенести логику отображения статуса мониторинга в заголовок группы:
```python
def _update_monitor_group_title(self):
    """Обновляет заголовок группы мониторинга при смене периодичности."""
    if hasattr(self, 'monitor_group'):
        interval_sec = self.get_monitor_interval() // 1000
        if getattr(self, 'auto_refresh_enabled', False):
            self.monitor_group.setTitle(f"Мониторинг активен (периодичность опроса {interval_sec} сек)")
            self.monitor_group.setStyleSheet("QGroupBox { color: green; font-weight: bold; }")
        else:
            self.monitor_group.setTitle(f"Мониторинг не активен (периодичность опроса {interval_sec} сек)")
            self.monitor_group.setStyleSheet("QGroupBox { color: black; font-weight: normal; }")

    # Если мониторинг активен — перезапускаем таймер с новым интервалом
    if getattr(self, 'auto_refresh_enabled', False) and hasattr(self, 'update_timer'):
        self.update_timer.setInterval(self.get_monitor_interval())
        self.main_window.log_message(f"Интервал мониторинга изменён на {self.get_monitor_interval() // 1000} сек")
```

#### 3. `src/operations/data_filtering_ops.py`

**3.1 В `start_monitoring()` (строки 352-354) — заменить установку `monitor_status` на вызов `_update_monitor_group_title()`**
```python
# Было:
self.main_window.monitor_status.setText("Мониторинг активен")
self.main_window.monitor_status.setStyleSheet("color: green; font-weight: bold;")

# Стало:
self.main_window._update_monitor_group_title()
```

**3.2 В `stop_monitoring()` (строки 379-381) — заменить установку `monitor_status` на вызов `_update_monitor_group_title()`**
```python
# Было:
self.main_window.monitor_status.setText("Мониторинг не активен")
self.main_window.monitor_status.setStyleSheet("color: black; font-weight: normal;")

# Стало:
self.main_window._update_monitor_group_title()
```

---

## Часть 2: Добавить фильтр "Одинаковое время обновления"

### Суть изменений
- Новый чекбокс в левой панели в группе PBIRS-фильтров
- Логика: показывать отчёты, у которых хотя бы 1 источник данных совпадает с другим отчётом И время следующего обновления совпадает
- Фильтр работает как AND к остальным фильтрам (применяется ПОСЛЕ OR-фильтров)
- "Не запланировано" не считается совпадением

### Файлы изменений

#### 1. `src/ui/ui_panels.py`

**1.1 Добавить чекбокс после строки 116 (после `filter_pbirs_in_progress`)**
```python
self.main.filter_pbirs_same_time = create_check_box("Одинаковое время обновления")
self.main.filter_pbirs_same_time.stateChanged.connect(lambda state, cb=self.main.filter_pbirs_same_time: self.main.apply_filters())
filter_layout.addWidget(self.main.filter_pbirs_same_time)
```

**1.2 В `_set_pbirs_filters_visible()` — добавить видимость для нового чекбокса**

В секцию видимости PBIRS-фильтров (после строки 862):
```python
if hasattr(self.main, 'filter_pbirs_same_time'):
    self.main.filter_pbirs_same_time.setVisible(visible)
```

В секцию сброса PBIRS-фильтров (после строки 907):
```python
if hasattr(self.main, 'filter_pbirs_same_time'):
    self.main.filter_pbirs_same_time.blockSignals(True)
    self.main.filter_pbirs_same_time.setChecked(False)
    self.main.filter_pbirs_same_time.blockSignals(False)
```

#### 2. `src/operations/data_filtering_ops.py`

**2.1 Добавить метод `_filter_same_time_reports()`**

```python
def _filter_same_time_reports(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Фильтрует отчёты: оставляет только те, у которых хотя бы 1 источник данных (ConnectionString)
    совпадает с другим отчётом И время следующего обновления совпадает.
    "Не запланировано" не считается совпадением.
    """
    if not reports:
        return []

    # Строим индекс: (ConnectionString, NextRunDisplay) -> список отчётов
    # Нормализуем ConnectionString: берём первую часть до точки с запятой
    from collections import defaultdict
    index = defaultdict(list)

    for report in reports:
        next_run = report.get('NextRunDisplay', '')
        if next_run == "Не запланировано":
            continue

        data_sources = report.get('DataSourcesList', [])
        conn_strings = set()
        for ds in data_sources:
            if ds is None:
                continue
            conn_str = ds.get('ConnectionString', '')
            if conn_str:
                # Нормализуем: берём первую часть до ;
                if ';' in conn_str:
                    conn_str = conn_str.split(';')[0]
                conn_strings.add(conn_str)

        if not conn_strings:
            continue

        for conn_str in conn_strings:
            key = (conn_str, next_run)
            index[key].append(report)

    # Собираем отчёты, у которых есть хотя бы один "дубликат" по ключу
    result = []
    seen_ids = set()

    for key, rep_list in index.items():
        if len(rep_list) >= 2:
            for rep in rep_list:
                rep_id = rep.get('Id', '')
                if rep_id not in seen_ids:
                    seen_ids.add(rep_id)
                    result.append(rep)

    return result
```

**2.2 В `_apply_pbirs_filters()` — добавить применение same_time фильтра после OR-фильтров**

После строки 265 (после формирования `filtered_reports` через OR-логику), перед обновлением таблиц:
```python
# Фильтр "Одинаковое время обновления" (AND — применяется после OR-фильтров)
if hasattr(self.main_window, 'filter_pbirs_same_time') and self.main_window.filter_pbirs_same_time.isChecked():
    filtered_reports = self._filter_same_time_reports(filtered_reports)
```

### Примечание
- `_filter_same_time_reports` использует `from collections import defaultdict` — нужно проверить, есть ли уже этот импорт в `data_filtering_ops.py`. Если нет — добавить.
- `List` и `Dict` из `typing` — проверить наличие импорта.