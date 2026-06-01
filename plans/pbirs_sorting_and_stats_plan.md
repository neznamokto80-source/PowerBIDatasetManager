# План: Сортировка колонок и блок статистики для PBIRS

## 1. Сортировка по двойному клику на заголовки колонок

### Где вносить изменения

**Файлы:**
- [`src/ui/ui_panels.py`](src/ui/ui_panels.py) — создание таблиц `pbirs_reports_table` и `pbirs_sources_table`
- [`src/ui/main_window.py`](src/ui/main_window.py) — методы `update_pbirs_reports_table()` и `update_pbirs_sources_table()`

### Механизм сортировки

Используем встроенный механизм `QTableWidget.sortItems()` через сигнал `QHeaderView.sectionDoubleClicked`.

**Логика:**
1. Подключаем сигнал `sectionDoubleClicked` от `horizontalHeader()` каждой таблицы к единому обработчику.
2. Обработчик хранит состояние сортировки для каждой таблицы в словаре `_sort_states`:
   - `{table_id: {'column': int, 'order': Qt.SortOrder}}`
3. При двойном клике:
   - Если колонка та же — инвертируем порядок сортировки.
   - Если колонка другая — сортируем по возрастанию.
4. Вызываем `table.sortItems(column, order)`.

### Изменения в `ui_panels.py`

**В `create_pbirs_reports_tab()`:**
- После создания таблицы добавить:
  ```python
  self.main.pbirs_reports_table.horizontalHeader().sectionDoubleClicked.connect(
      lambda col: self.main.sort_pbirs_table('reports', col)
  )
  ```

**В `create_pbirs_sources_tab()`:**
- После создания таблицы добавить:
  ```python
  self.main.pbirs_sources_table.horizontalHeader().sectionDoubleClicked.connect(
      lambda col: self.main.sort_pbirs_table('sources', col)
  )
  ```

### Изменения в `main_window.py`

Добавить:
- Атрибут `self._pbirs_sort_states = {}` в `__init__` (или в `_init_method_classes`).
- Метод `sort_pbirs_table(table_key: str, column: int)`:
  ```python
  def sort_pbirs_table(self, table_key: str, column: int):
      table_map = {
          'reports': self.pbirs_reports_table,
          'sources': self.pbirs_sources_table,
      }
      table = table_map.get(table_key)
      if not table:
          return
      
      state = self._pbirs_sort_states.get(table_key, {})
      prev_col = state.get('column')
      prev_order = state.get('order', Qt.SortOrder.AscendingOrder)
      
      if prev_col == column:
          new_order = Qt.SortOrder.DescendingOrder if prev_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
      else:
          new_order = Qt.SortOrder.AscendingOrder
      
      self._pbirs_sort_states[table_key] = {'column': column, 'order': new_order}
      table.sortItems(column, new_order)
  ```

---

## 2. Блок статистики PBIRS рядом с вкладками

### Где вносить изменения

**Файлы:**
- [`src/ui/ui_panels.py`](src/ui/ui_panels.py) — метод `create_center_panel()`, где создаётся `tab_widget`
- [`src/ui/main_window.py`](src/ui/main_window.py) — метод `update_pbirs_reports_table()` и `_apply_pbirs_filters()`
- [`src/operations/data_filtering_ops.py`](src/operations/data_filtering_ops.py) — метод `_apply_pbirs_filters()`

### Концепция

Блок статистики размещается **внутри центральной панели, над `tab_widget`**, на одном уровне с вкладками, но правее. Для этого:

1. Создаём `QWidget` (stats_bar) с `QHBoxLayout`.
2. Слева размещаем `tab_widget` (как и сейчас).
3. Справа размещаем stats_bar с тремя `QLabel`:
   - "Всего: N"
   - "С ошибками: N"
   - "Общий размер: N МБ"
4. Stats_bar виден только в режиме `server`.

**Альтернативный подход (проще):** Используем `QTabWidget.setCornerWidget()` — это стандартный механизм Qt для размещения виджета в углу области вкладок (справа от заголовков вкладок). Это идеально подходит для нашей задачи.

### Изменения в `ui_panels.py`

**В `create_center_panel()`:**
- После создания `tab_widget` и добавления всех вкладок:
  ```python
  # Создаём виджет статистики PBIRS (справа от вкладок)
  self.main.pbirs_stats_widget = QWidget()
  stats_layout = QHBoxLayout(self.main.pbirs_stats_widget)
  stats_layout.setContentsMargins(5, 0, 5, 0)
  
  self.main.pbirs_stats_total = QLabel("Всего: 0")
  self.main.pbirs_stats_errors = QLabel("С ошибками: 0")
  self.main.pbirs_stats_size = QLabel("Общий размер: 0 МБ")
  
  for label in [self.main.pbirs_stats_total, self.main.pbirs_stats_errors, self.main.pbirs_stats_size]:
      label.setStyleSheet("font-weight: bold; padding: 2px 8px;")
      stats_layout.addWidget(label)
  
  self.main.tab_widget.setCornerWidget(self.main.pbirs_stats_widget, Qt.Corner.TopRightCorner)
  self.main.pbirs_stats_widget.setVisible(False)  # По умолчанию скрыт
  ```

### Изменения в `main_window.py`

**В `update_tabs_visibility()`:**
- Добавить управление видимостью stats_widget:
  ```python
  if hasattr(self, 'pbirs_stats_widget'):
      self.pbirs_stats_widget.setVisible(self.current_mode == 'server')
  ```

**Новый метод `update_pbirs_stats()`:**
```python
def update_pbirs_stats(self, reports):
    """Обновляет статистику PBIRS на основе отфильтрованных данных."""
    if not hasattr(self, 'pbirs_stats_total'):
        return
    
    total = len(reports)
    
    # Считаем отчёты с ошибками
    errors = 0
    total_size_mb = 0.0
    for report in reports:
        # Проверка статуса ошибки
        last_status = report.get('LastStatus', '')
        if last_status and ('error' in last_status.lower() or 'failed' in last_status.lower() or 'ошибк' in last_status.lower()):
            errors += 1
        
        # Суммируем размер
        size_str = report.get('SizeDisplay', '0 МБ')
        try:
            size_val = float(size_str.replace(' МБ', '').replace(',', '.').strip())
            total_size_mb += size_val
        except (ValueError, AttributeError):
            pass
    
    self.pbirs_stats_total.setText(f"Всего: {total}")
    self.pbirs_stats_errors.setText(f"С ошибками: {errors}")
    self.pbirs_stats_size.setText(f"Общий размер: {total_size_mb:.1f} МБ")
```

### Где вызывать `update_pbirs_stats()`

1. **В `update_pbirs_reports_table()`** — в конце метода, после фильтрации и заполнения таблицы, вызвать `self.update_pbirs_stats(filtered_reports)`.
2. **В `_apply_pbirs_filters()`** (`data_filtering_ops.py`) — после применения фильтров и обновления таблиц, вызвать `self.main_window.update_pbirs_stats(filtered_reports)`.

---

## 3. Сводка изменений по файлам

| Файл | Изменения |
|------|-----------|
| `src/ui/ui_panels.py` | 1. Добавить `sectionDoubleClicked` для таблиц reports и sources<br>2. Добавить `pbirs_stats_widget` как corner widget в `tab_widget` |
| `src/ui/main_window.py` | 1. Добавить атрибут `_pbirs_sort_states`<br>2. Добавить метод `sort_pbirs_table()`<br>3. Добавить метод `update_pbirs_stats()`<br>4. Обновить `update_tabs_visibility()` для stats_widget<br>5. Вызывать `update_pbirs_stats()` в `update_pbirs_reports_table()` |
| `src/operations/data_filtering_ops.py` | 1. Вызывать `self.main_window.update_pbirs_stats(filtered_reports)` в `_apply_pbirs_filters()` |

---

## 4. Mermaid-диаграмма потока данных

```mermaid
flowchart TD
    A[Пользователь применяет фильтры] --> B{data_filtering_ops._apply_pbirs_filters}
    B --> C[Фильтрация отчетов]
    C --> D[main_window.update_pbirs_reports_table filtered_reports]
    D --> E[Заполнение таблицы]
    D --> F[main_window.update_pbirs_stats filtered_reports]
    F --> G[Обновление stats_total]
    F --> H[Обновление stats_errors]
    F --> I[Обновление stats_size]
    
    J[Пользователь двойной клик на заголовке] --> K[sectionDoubleClicked signal]
    K --> L[main_window.sort_pbirs_table table_key, column]
    L --> M{Проверка: та же колонка?}
    M -->|Да| N[Инвертировать порядок]
    M -->|Нет| O[Сортировка по возрастанию]
    N --> P[table.sortItems column, order]
    O --> P