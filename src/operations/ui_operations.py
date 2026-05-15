#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Операции пользовательского интерфейса: управление состоянием, обработчики событий, справка.
Объединяет функционал из ui_state.py, event_handlers.py и help_methods.py.
"""

import logging
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidgetItem,
    QMenu, QFormLayout, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from ..ui.dataset_details_dialog import DatasetDetailsDialog

logger = logging.getLogger(__name__)


class UIOperations:
    """Операции пользовательского интерфейса."""
    
    def __init__(self, main_window):
        """
        Инициализирует операции UI.
        
        Args:
            main_window: Экземпляр главного окна (PowerBIMonitorUI)
        """
        self.main_window = main_window
    
    # ========== Методы управления состоянием UI (из UIStateMethods) ==========
    
    def update_ui_for_disconnected_state(self):
        """Обновляет UI для состояния 'не подключено'."""
        # Очищаем все данные
        self.main_window.workspace_combo.clear()
        self.main_window.workspace_combo.addItem("-- Не подключено --")
        self.main_window.workspace_combo.setEnabled(False)
        
        self.main_window.dataset_tree.clear()
        self.main_window.dataset_tree.setHeaderLabels(["Название", "Статус", "Обновление"])
        
        # Очищаем таблицу
        self.main_window.dataset_table.setRowCount(0)
        
        # Обновляем статистику
        self.main_window.total_datasets_label.setText("Всего датасетов: --")
        self.main_window.enabled_refresh_label.setText("С обновлением: --")
        self.main_window.failed_refresh_label.setText("С ошибками: --")
        self.main_window.last_update_label.setText("Последнее обновление: --")
        
        # Обновляем детали
        self.main_window.detail_name.setText("-")
        self.main_window.detail_id.setText("-")
        self.main_window.detail_workspace.setText("-")
        self.main_window.detail_refresh_status.setText("-")
        self.main_window.detail_last_refresh.setText("-")
        self.main_window.detail_next_refresh.setText("-")
        self.main_window.detail_schedule.setText("-")
        
        # Отключаем кнопки управления
        self.main_window.enable_btn.setEnabled(False)
        self.main_window.disable_btn.setEnabled(False)
        self.main_window.manual_refresh_btn.setEnabled(False)
        if hasattr(self.main_window, 'edit_schedule_btn'):
            self.main_window.edit_schedule_btn.setEnabled(False)
        
        # Отключаем фильтры
        self.main_window.filter_enabled.setEnabled(False)
        self.main_window.filter_recent.setEnabled(False)
        self.main_window.filter_errors.setEnabled(False)
        self.main_window.filter_except_not_use.setEnabled(False)
        self.main_window.filter_in_progress.setEnabled(False)
        
        # Отключаем мониторинг
        self.main_window.start_monitor_btn.setEnabled(False)
        self.main_window.stop_monitor_btn.setEnabled(False)
        
        # Обновляем кнопку подключения
        if hasattr(self.main_window, 'connect_btn'):
            self.main_window.connect_btn.setText("Подключить")
            self.main_window.connect_btn.setEnabled(True)
    
    def update_ui_for_connected_state(self):
        """Обновляет UI для состояния 'подключено'."""
        # Включаем комбобокс рабочих областей
        self.main_window.workspace_combo.setEnabled(True)
        self.main_window.workspace_combo.clear()
        if self.main_window.workspaces:
            for ws in self.main_window.workspaces:
                name = ws.get('name', 'Без имени')
                self.main_window.workspace_combo.addItem(name, ws.get('id'))
        else:
            self.main_window.workspace_combo.addItem("Нет рабочих областей")
        
        # Включаем фильтры
        self.main_window.filter_enabled.setEnabled(True)
        self.main_window.filter_recent.setEnabled(True)
        self.main_window.filter_errors.setEnabled(True)
        self.main_window.filter_except_not_use.setEnabled(True)
        self.main_window.filter_in_progress.setEnabled(True)
        
        # Включаем кнопки управления (позже, когда выбран датасет)
        self.main_window.enable_btn.setEnabled(False)
        self.main_window.disable_btn.setEnabled(False)
        self.main_window.manual_refresh_btn.setEnabled(False)
        if hasattr(self.main_window, 'edit_schedule_btn'):
            self.main_window.edit_schedule_btn.setEnabled(False)
        self.main_window.start_monitor_btn.setEnabled(True)
        self.main_window.stop_monitor_btn.setEnabled(False)
        
        # Обновляем статус
        self.main_window.status_bar.showMessage("Подключено", 3000)
        self.main_window.log_message("UI обновлен для состояния 'подключено'")
    
    def log_message(self, message: str):
        """Добавляет сообщение в лог через стандартный логгер."""
        # Логируем через стандартный логгер - обработчик QTextEditLogHandler
        # сам добавит запись в UI с правильным форматом
        logger.info(message)
    
    # ========== Обработчики событий (из EventHandlers) ==========
    
    def on_workspace_selected(self, index):
        """Обработчик выбора рабочей области."""
        if index < 0 or not self.main_window.workspaces:
            return
        
        workspace_id = self.main_window.workspace_combo.itemData(index)
        if workspace_id:
            self.main_window.current_workspace = workspace_id
            self.main_window.log_message(
                f"Выбрана рабочая область: {self.main_window.workspace_combo.itemText(index)}"
            )
            self.main_window.load_datasets()
    
    def on_dataset_selected(self, item, column):
        """Обработчик выбора датасета."""
        if not item:
            return
        
        # Получаем имя датасета из выбранного элемента
        dataset_name = item.text(0) if isinstance(item, QTreeWidgetItem) else item.text()
        
        # Ищем датасет в списке
        dataset = None
        for ds in self.main_window.datasets:
            if ds.get('name') == dataset_name:
                dataset = ds
                break
        
        if dataset:
            self.main_window.current_dataset = dataset  # сохраняем объект датасета
            self.main_window.update_dataset_details(dataset)
            self.main_window.log_message(f"Выбран датасет: {dataset_name}")
            
            # Включаем кнопки управления
            self.main_window.enable_btn.setEnabled(True)
            self.main_window.disable_btn.setEnabled(True)
            self.main_window.manual_refresh_btn.setEnabled(True)
            if hasattr(self.main_window, 'edit_schedule_btn'):
                self.main_window.edit_schedule_btn.setEnabled(True)
        else:
            self.main_window.log_message(f"Датасет {dataset_name} не найден в списке")
    
    def on_dataset_double_clicked(self, item):
        """Обработчик двойного клика по датасету."""
        if not item:
            return
        
        # Определяем, является ли элемент ячейкой таблицы или элементом дерева
        dataset = None
        if isinstance(item, QTreeWidgetItem):
            # Элемент дерева
            dataset_name = item.text(0)
            for ds in self.main_window.datasets:
                if ds.get('name') == dataset_name:
                    dataset = ds
                    break
        else:
            # Ячейка таблицы QTableWidgetItem
            table = item.tableWidget()
            row = item.row()
            # Получаем ID датасета из колонки 2
            id_item = table.item(row, 2)
            if id_item:
                dataset_id = id_item.text()
                for ds in self.main_window.datasets:
                    if ds.get('id') == dataset_id:
                        dataset = ds
                        break
        
        if dataset:
            # Сохраняем текущий датасет и рабочую область для кнопок
            previous_dataset = self.main_window.current_dataset
            previous_workspace = self.main_window.current_workspace
            self.main_window.current_dataset = dataset
            self.main_window.current_workspace = dataset.get('workspaceId', previous_workspace)
            
            # Получаем данные расписания из датасета (поле refresh_schedule)
            schedule_data = dataset.get('refresh_schedule')
            if not isinstance(schedule_data, dict):
                schedule_data = None
            
            # Создаем диалог
            dialog = DatasetDetailsDialog(
                parent=self.main_window,
                dataset=dataset,
                main_window=self.main_window,
                initial_schedule=schedule_data
            )
            
            # Восстановление предыдущего состояния после закрытия диалога
            def restore_state():
                self.main_window.current_dataset = previous_dataset
                self.main_window.current_workspace = previous_workspace
            dialog.finished.connect(lambda _: restore_state())
            
            dialog.exec()
            
            self.main_window.log_message(f"Открыты детали датасета: {dataset.get('name', 'Неизвестно')}")
    
    def get_selected_datasets(self, table):
        """
        Возвращает список выбранных датасетов из таблицы.
        
        Args:
            table: QTableWidget (dataset_table)
            
        Returns:
            Список объектов датасетов (словарей)
        """
        selected_datasets = []
        if not table or not hasattr(self.main_window, 'datasets'):
            return selected_datasets
        
        # Получаем выбранные строки
        selected_rows = set()
        for item in table.selectedItems():
            selected_rows.add(item.row())
        
        # Для каждой выбранной строки находим датасет
        for row in selected_rows:
            if row < 0 or row >= table.rowCount():
                continue
            # Получаем ID датасета из колонки 2 (ID датасета)
            id_item = table.item(row, 2)
            if id_item:
                dataset_id = id_item.text()
                # Ищем датасет в общем списке
                for ds in self.main_window.datasets:
                    if ds.get('id') == dataset_id:
                        selected_datasets.append(ds)
                        break
        
        return selected_datasets
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы датасетов."""
        # Определяем, откуда вызвано меню (таблица или дерево)
        sender = self.main_window.sender()
        
        menu = QMenu(self.main_window)
        
        # Общие действия
        refresh_action = QAction("Обновить информацию", self.main_window)
        refresh_action.triggered.connect(self.main_window.refresh_data)
        
        details_action = QAction("Показать детали", self.main_window)
        details_action.triggered.connect(lambda: self.on_dataset_double_clicked(
            sender.currentItem() if hasattr(sender, 'currentItem') else None
        ))
        
        # Определяем выбранные датасеты (для таблицы)
        selected_datasets = []
        if sender == self.main_window.dataset_table:
            selected_datasets = self.get_selected_datasets(sender)
        
        # Если выбрано несколько датасетов
        if len(selected_datasets) > 1:
            count = len(selected_datasets)
            enable_action = QAction(f"Включить автообновление для выбранных ({count})", self.main_window)
            enable_action.triggered.connect(lambda: self.main_window.enable_auto_refresh_selected(selected_datasets))
            
            disable_action = QAction(f"Отключить автообновление для выбранных ({count})", self.main_window)
            disable_action.triggered.connect(lambda: self.main_window.disable_auto_refresh_selected(selected_datasets))
            
            manual_refresh_action = QAction(f"Запустить обновление для выбранных ({count})", self.main_window)
            manual_refresh_action.triggered.connect(lambda: self.main_window.trigger_manual_refresh_selected(selected_datasets))
            
            menu.addAction(refresh_action)
            menu.addSeparator()
            menu.addAction(details_action)
            menu.addSeparator()
            menu.addAction(enable_action)
            menu.addAction(disable_action)
            menu.addAction(manual_refresh_action)
        
        # Одиночный выбор (дерево или таблица с одним выбранным)
        else:
            # Пытаемся определить выбранный датасет
            target_dataset = None
            target_workspace = None
            
            # Если есть selected_datasets с одним элементом
            if len(selected_datasets) == 1:
                target_dataset = selected_datasets[0]
                target_workspace = target_dataset.get('workspaceId', self.main_window.current_workspace)
            elif hasattr(sender, 'currentItem') and sender.currentItem():
                # Получаем датасет из currentItem (для дерева)
                item = sender.currentItem()
                dataset_name = item.text(0) if isinstance(item, QTreeWidgetItem) else item.text()
                for ds in self.main_window.datasets:
                    if ds.get('name') == dataset_name:
                        target_dataset = ds
                        target_workspace = ds.get('workspaceId', self.main_window.current_workspace)
                        break
            
            if target_dataset:
                # Сохраняем текущие значения, чтобы восстановить после действий?
                # Вместо этого временно установим current_dataset и current_workspace
                # через замыкание
                def make_enable_closure(dataset, workspace):
                    def closure():
                        self.main_window.current_dataset = dataset
                        self.main_window.current_workspace = workspace
                        self.main_window.enable_auto_refresh()
                    return closure
                
                def make_disable_closure(dataset, workspace):
                    def closure():
                        self.main_window.current_dataset = dataset
                        self.main_window.current_workspace = workspace
                        self.main_window.disable_auto_refresh()
                    return closure
                
                def make_manual_closure(dataset, workspace):
                    def closure():
                        self.main_window.current_dataset = dataset
                        self.main_window.current_workspace = workspace
                        self.main_window.trigger_manual_refresh()
                    return closure
                
                enable_action = QAction("Включить автообновление", self.main_window)
                enable_action.triggered.connect(make_enable_closure(target_dataset, target_workspace))
                
                disable_action = QAction("Отключить автообновление", self.main_window)
                disable_action.triggered.connect(make_disable_closure(target_dataset, target_workspace))
                
                manual_refresh_action = QAction("Запустить обновление вручную", self.main_window)
                manual_refresh_action.triggered.connect(make_manual_closure(target_dataset, target_workspace))
                
                menu.addAction(refresh_action)
                menu.addSeparator()
                menu.addAction(details_action)
                menu.addSeparator()
                menu.addAction(enable_action)
                menu.addAction(disable_action)
                menu.addAction(manual_refresh_action)
            else:
                # Нет выбранного датасета, показываем только общие действия
                menu.addAction(refresh_action)
                menu.addAction(details_action)
        
        menu.exec(sender.mapToGlobal(position))
    
    # ========== Методы справки (из HelpMethods) ==========
    
    def show_help(self):
        """Показывает диалог справки с подробным описанием."""
        help_text = self._get_help_text()

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Справка - Power BI Dataset Monitor & Manager")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(help_text)
        text_edit.setStyleSheet("QTextEdit { font-family: 'Segoe UI', 'Arial'; font-size: 10pt; }")

        layout.addWidget(text_edit)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

    def _get_help_text(self) -> str:
        """Возвращает HTML-текст справки."""
        return """
        <h1>Power BI Dataset Monitor & Manager</h1>
        <p><b>Версия:</b> 1.0.0</p>
        <p>Приложение для мониторинга и управления датасетами Microsoft Power BI.</p>

        <h2>1. Общее описание</h2>
        <p>С помощью этого приложения вы можете:</p>
        <ul>
            <li>подключаться к Power BI через интерактивную аутентификацию (Azure CLI или браузер);</li>
            <li>просматривать список рабочих областей и датасетов;</li>
            <li>видеть статус последнего обновления, расписание автоматического обновления, следующее запланированное обновление;</li>
            <li>включать / отключать автоматическое обновление для одного или нескольких датасетов;</li>
            <li>запускать ручное обновление датасета;</li>
            <li>фильтровать датасеты по различным критериям;</li>
            <li>запускать автоматический мониторинг с периодическим опросом (30 секунд);</li>
            <li>просматривать логи работы приложения.</li>
        </ul>

        <h2>2. Подключение к Power BI</h2>
        <ol>
            <li>Нажмите кнопку <b>«Подключить»</b> в левой панели.</li>
            <li>Приложение попытается получить токен через Azure CLI (если он настроен) или откроет браузер для интерактивного входа.</li>
            <li>После успешной аутентификации левая панель разблокируется, загрузятся рабочие области. Активной станет первая рабочая область, автоматически начнётся загрузка датасетов.</li>
        </ol>
        <p><b>Примечание:</b> Если Azure CLI не используется, будет предложен браузерный вход. Выполните вход в свою учётную запись Power BI.</p>

        <h2>3. Интерфейс приложения</h2>
        <h3>Главное окно</h3>
        <ul>
            <li><b>Левая панель</b> – навигация и управление: кнопка «Подключить», выбор рабочей области, дерево датасетов, фильтры, блок мониторинга.</li>
            <li><b>Центральная панель</b> – вкладки «Обзор» и «Детали»:
                <ul>
                    <li>«Обзор»: статистика, таблица датасетов, прогресс-бар.</li>
                    <li>«Детали»: подробная информация о выбранном датасете и кнопки управления.</li>
                </ul>
            </li>
            <li><b>Нижняя панель</b> – область логов (текст с автоформатированием, есть кнопка «Очистить логи»).</li>
        </ul>

        <h3>Кнопки управления датасетов (вкладка «Детали»)</h3>
        <ul>
            <li><b>Включить обновление</b> – активирует автоматическое обновление датасета по существующему или стандартному расписанию (ежедневно в 03:00 по UTC+6, что соответствует 02:00 по Екатеринбургу UTC+5).</li>
            <li><b>Отключить обновление</b> – выключает автоматическое обновление.</li>
            <li><b>Запустить обновление</b> – инициирует ручное обновление (полное, Full).</li>
        </ul>

        <h3>Новые элементы интерфейса (май 2026)</h3>
        <p>Вкладка «Детали» была оптимизирована для лучшего использования пространства:</p>
        <ul>
            <li><b>Фильтр выбора датасета</b> – выпадающий список для быстрого выбора датасета без перехода в таблицу.</li>
            <li><b>Информация о датасете в два столбца</b> – основные сведения слева, дополнительные справа, разделены вертикальной линией.</li>
            <li><b>Управление расписанием</b> – постоянно видимый блок с днями недели в две колонки и списком времени срабатывания в две колонки по 6 строк.</li>
            <li><b>Добавление нового времени</b> – панель справа от списка: поля для ввода часов и минут, кнопки «Добавить время» и «Удалить выбранное».</li>
            <li><b>Панель логов внизу окна</b> – логи теперь отображаются в нижней части интерфейса, а не в отдельной вкладке, что обеспечивает постоянную видимость.</li>
            <li><b>Кнопки «Справка» и «Тестовые данные»</b> перенесены в правую часть панели инструментов для более удобного доступа.</li>
        </ul>

        <h2>4. Детальная информация о датасете</h2>
        <ul>
            <li><b>Двойной клик</b> по строке в таблице или щелчок по элементу в дереве откроет диалоговое окно с полной информацией (ID, расписание, история последних обновлений, детали последнего обновления).</li>
            <li>Во вкладке «Детали» при выборе датасета отображается краткая сводка и доступны три кнопки управления.</li>
        </ul>

        <h2>5. Фильтрация датасетов</h2>
        <p>Чекбоксы в левой панели позволяют отфильтровать таблицу и дерево:</p>
        <ul>
            <li><b>Только с включенным обновлением</b> – показывать датасеты, у которых автообновление активно.</li>
            <li><b>Только с выключенным обновлением</b> – датасеты, где расписание выключено.</li>
            <li><b>С ошибками при обновлении</b> – датасеты, последнее обновление которых завершилось с ошибкой.</li>
            <li><b>Все кроме not_use</b> – исключает датасеты, в имени которых встречается подстрока «not_use».</li>
            <li><b>В процессе обновления</b> – датасеты со статусом InProgress или Refreshing.</li>
        </ul>
        <p>Фильтры применяются <b>одновременно</b> (логическое «И»).</p>

        <h2>6. Пакетные операции (контекстное меню)</h2>
        <p>Правый клик по таблице датасетов открывает контекстное меню. При выделении нескольких строк доступны:</p>
        <ul>
            <li>Включить автообновление для выбранных</li>
            <li>Отключить автообновление для выбранных</li>
            <li>Запустить обновление для выбранных</li>
            <li>Обновить информацию</li>
            <li>Показать детали</li>
        </ul>

        <h2>7. Мониторинг в реальном времени</h2>
        <p>Блок «Мониторинг (периодичность опроса 30 сек)»:</p>
        <ul>
            <li><b>Запустить мониторинг</b> – включает таймер, который каждые 30 секунд автоматически вызывает обновление данных.</li>
            <li><b>Остановить мониторинг</b> – выключает таймер.</li>
        </ul>
        <p>Мониторинг не запускается автоматически при старте приложения.</p>

        <h2>8. Логирование</h2>
        <p>Все действия записываются в нижнюю панель логов и в файл <code>powerbi_monitor.log</code> в папке с программой.</p>

        <h2>9. Устранение возможных проблем</h2>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
            <tr><th>Проблема</th><th>Возможное решение</th></tr>
            <tr><td>Ошибка аутентификации «Не удалось получить токен»</td><td>Убедитесь, что вы выполнили вход в Power BI Desktop или через <code>az login</code>. При интерактивной аутентификации разрешите доступ приложению.</td></tr>
            <tr><td>Нет рабочих областей в списке</td><td>Проверьте, есть ли у вас доступ хотя бы к одной рабочей области. Для бесплатного аккаунта Power BI рабочие области могут не отображаться.</td></tr>
            <tr><td>Не удаётся включить автообновление – ошибка 403</td><td>У вас недостаточно прав на изменение расписания датасета. Требуется роль администратора или участника с правами на редактирование.</td></tr>
            <tr><td>Расписание отображается некорректно (не те времена)</td><td>Приложение конвертирует время из UTC+6 (Central Asia Standard Time) в UTC+5 (Екатеринбург). Если ваш часовой пояс отличается, измените значения <code>from_offset</code> и <code>to_offset</code> в коде.</td></tr>
        </table>

        <h2>10. Контакты разработчика</h2>
        <p>По вопросам доработки или сообщениям об ошибках обращайтесь @BDV_80".</p>

        <p><i>Версия приложения: 1.0.0</i><br><i>Дата составления справки: Май 2026</i></p>
        """