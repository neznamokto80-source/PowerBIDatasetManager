# План исправления проблемы с фильтрами после обновления данных

## Проблема
Фильтры не учитываются после обновления информации. Например, если выбран чекбокс "все кроме not use", он показывает корректно, но после нажатия кнопки "обновить информацию" показывает уже все данные без фильтрации.

## Анализ
1. Метод `refresh_data` вызывает `load_datasets`, который загружает датасеты из Power BI.
2. `load_datasets` сохраняет датасеты в `self.main_window.datasets` и напрямую обновляет таблицу и дерево датасетов, игнорируя текущие фильтры.
3. Фильтры применяются только при изменении состояния чекбоксов (через `apply_filters`), но не после загрузки новых данных.

## Решение
Модифицировать метод `load_datasets` в `src/operations/data_loading_ops.py`, чтобы после загрузки данных применялись текущие фильтры. Убрать прямое обновление таблицы и дерева, оставив эту задачу для `apply_filters`.

### Изменения в `src/operations/data_loading_ops.py`

#### 1. Метод `load_datasets` (строки 135-209)
Заменить блок кода после сохранения `self.main_window.datasets`:

**Было:**
```python
self.main_window.datasets = datasets
self.main_window.log_message(f"✓ Загружено датасетов: {len(datasets)}")

# Обновление дерева датасетов
self.main_window.dataset_tree.clear()
for ds in datasets:
    name = ds.get('name', 'Без имени')
    status = ds.get('status', 'unknown')
    refresh = ds.get('lastRefreshTime', 'никогда')
    item = QTreeWidgetItem([name, status, refresh])
    
    # Цветовое выделение для дерева - используем общую логику определения цвета
    background_color = ThemeColors.get_dataset_background_color(ds, self.main_window.current_theme)
    
    if background_color:
        brush = QBrush(background_color)
        for col in range(item.columnCount()):
            item.setBackground(col, brush)
    
    self.main_window.dataset_tree.addTopLevelItem(item)

# Обновление таблицы датасетов
self.update_dataset_table(datasets)

# Обновление статистики
self.update_stats(datasets)

self.main_window.status_bar.showMessage("Датасеты загружены", 3000)
```

**Стало:**
```python
self.main_window.datasets = datasets
self.main_window.log_message(f"✓ Загружено датасетов: {len(datasets)}")

# Обновление статистики (по всем датасетам)
self.update_stats(datasets)

# Применяем текущие фильтры для обновления таблицы и дерева
self.main_window.apply_filters()

self.main_window.status_bar.showMessage("Датасеты загружены", 3000)
```

#### 2. Метод `load_test_data` (строки 211-260)
Аналогичное изменение: убрать прямое обновление дерева и таблицы, добавить вызов `apply_filters`.

**Было:**
```python
self.main_window.datasets = datasets
self.main_window.log_message(f"✓ Загружено тестовых датасетов: {len(datasets)}")

# Обновление дерева датасетов
self.main_window.dataset_tree.clear()
for ds in datasets:
    name = ds.get('name', 'Без имени')
    status = ds.get('status', 'unknown')
    refresh = ds.get('lastRefreshTime', 'никогда')
    item = QTreeWidgetItem([name, status, refresh])
    
    # Цветовое выделение для дерева
    background_color = ThemeColors.get_dataset_background_color(ds, self.main_window.current_theme)
    if background_color:
        brush = QBrush(background_color)
        for col in range(item.columnCount()):
            item.setBackground(col, brush)
    
    self.main_window.dataset_tree.addTopLevelItem(item)

# Обновление таблицы датасетов
self.update_dataset_table(datasets)

# Обновление статистики
self.update_stats(datasets)

self.main_window.status_bar.showMessage("Тестовые данные загружены", 3000)
```

**Стало:**
```python
self.main_window.datasets = datasets
self.main_window.log_message(f"✓ Загружено тестовых датасетов: {len(datasets)}")

# Обновление статистики (по всем датасетам)
self.update_stats(datasets)

# Применяем текущие фильтры для обновления таблицы и дерева
self.main_window.apply_filters()

self.main_window.status_bar.showMessage("Тестовые данные загружены", 3000)
```

### 3. Проверка метода `apply_filters`
Убедиться, что метод `apply_filters` в `src/operations/data_filtering_ops.py` корректно работает с обновленными данными. Он должен:
- Фильтровать `self.main_window.datasets` на основе состояния чекбоксов.
- Обновлять таблицу через `update_dataset_table(filtered_datasets)`.
- Обновлять дерево датасетов (очищать и заполнять отфильтрованными данными).
- Обновлять комбобокс деталей (через `update_dataset_table`).

Метод уже выполняет эти действия, поэтому изменений не требуется.

### 4. Дополнительные соображения
- После применения изменений фильтры будут сохраняться при любом обновлении данных (ручное обновление, автообновление, смена рабочей области).
- Комбобокс деталей будет содержать только отфильтрованные датасеты, что согласуется с отображением в таблице.
- Статистика будет отображаться по всем датасетам (нефильтрованным), что логично, так как фильтры влияют только на отображение.

## Тестирование
1. Запустить приложение.
2. Подключиться к Power BI или загрузить тестовые данные.
3. Применить фильтр (например, "все кроме not_use").
4. Убедиться, что таблица и дерево показывают только отфильтрованные датасеты.
5. Нажать кнопку "Обновить" (или "Обновить данные").
6. Убедиться, что после обновления фильтр остаётся применённым, и отображаются только отфильтрованные датасеты.
7. Проверить другие фильтры (по ошибкам, по включенному обновлению и т.д.).

## Альтернативные сценарии
- Если фильтры не применены (все чекбоксы выключены), после обновления должны отображаться все датасеты.
- При смене рабочей области фильтры должны применяться к новому списку датасетов.
- При включении мониторинга (автообновление) фильтры должны сохраняться между циклами обновления.

## Примечания
- Изменения затрагивают только логику отображения, не влияя на загрузку данных или работу с API.
- План готов к реализации в режиме Code.