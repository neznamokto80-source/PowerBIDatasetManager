# План работ: перевод на PyQt5 + стиль Catppuccin (как в D:\git\BO\gui) + pyproject.toml

> Задача: перевести приложение Power BI Dataset Monitor & Manager с PyQt6 на **PyQt5**,
> применить цветовую гамму/шрифты **Catppuccin** как в проекте `D:\git\BO\gui`
> (сохранив текущую структуру интерфейса: сплиттер + табы),
> и заменить `requirements.txt` на `pyproject.toml`.

Легенда:
- [x] — выполнено
- [-] — в процессе
- [ ] — ожидает выполнения

---

## 1. Темы оформления (Catppuccin)

- [x] **1.1** Создать `src/ui/themes.py` — CSS-темы DARK_THEME / LIGHT_THEME
  (Catppuccin Mocha / Latte), THEMES, LOG_COLORS, адаптировать под виджеты проекта
  (QTreeWidget, QListWidget, QSpinBox, QDialog, QProgressBar, QMessageBox,
  QInputDialog, QSplitter, таблицы, прокрутки).

- [x] **1.2** Переписать `src/ui/theme_colors.py` — применение CSS-темы через
  `setStyleSheet` вместо QPalette; функции `get_active_theme` / `apply_theme_to_app`;
  сохранить методы подсветки строк таблиц (error / disabled / not_scheduled).

## 2. Фабрики и панели UI

- [x] **2.1** `src/ui/widgets/factories.py` — PyQt5, Qt enums,
  `QHeaderView.Interactive`, стили кнопок primary/secondary/danger.

- [x] **2.2** `src/ui/ui_toolbars.py` — PyQt5, кнопки в стиле BO.

- [x] **2.3** `src/ui/ui_panels.py` — PyQt5, все Qt enums
  (Qt.AlignCenter, Qt.TopRightCorner, QHeaderView без ResizeMode, и т.д.).

- [x] **2.4** `src/ui/ui_components.py` — PyQt5 (импорты QWidget/QVBoxLayout/QLabel).

## 3. Главное окно и диалоги

- [x] **3.1** `src/ui/main_window.py` — PyQt5, Qt enums, применение темы в init_ui.
  Структуру сплиттер+табы **сохранить**.

- [ ] **3.2** Диалоги `schedule_editor_dialog.py`, `pbirs_schedule_dialog.py`,
  `dataset_details_dialog.py` — PyQt5 + стиль BO.

## 4. Логирование

- [ ] **4.1** `src/utils/log_handler.py` — PyQt5 + цветовая кодировка уровней
  логов (LOG_COLORS как в BO).

## 5. Операции и ядро

- [x] **5.1** `src/operations/*.py` (ui_operations, pbirs_operations,
  refresh_operations, data_loading_ops, data_filtering_ops) — PyQt5
  (Qt.ItemDataRole→Qt.UserRole, Qt.AlignmentFlag→Qt.AlignCenter, QAction→QtWidgets).

- [x] **5.2** `src/core/connection.py`, `src/core/connection_pbirs.py`,
  `src/core/dependencies.py` — PyQt5.

## 6. Точка входа и зависимости

- [x] **6.1** `main.py` — PyQt5, ensure_dependencies (PyQt5), применение темы.

- [x] **6.2** Создать `pyproject.toml` (замена `requirements.txt`), удалить
  `requirements.txt`.

- [x] **6.3** Создать `build-exe.py` — сборка .exe через PyInstaller
  с предварительной очисткой предыдущей сборки (build/, dist/, *.spec, exe).

## 7. Проверка

- [x] **7.1** Запустить и проверить приложение: старт, переключение тем, диалоги,
  логи.