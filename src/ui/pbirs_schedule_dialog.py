#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалог создания расписания обновления для отчёта Power BI Report Server (PBIRS).
Позволяет задать название, тип периодичности, дни недели и время запуска.
"""

from typing import Dict, Any, List, Optional

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

# Дни недели для PBIRS API
DAY_NAMES_API = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]
DAY_LABELS_RU = [
    "Воскресенье",
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
]


class PBIRSScheduleDialog(QDialog):
    """Диалог создания расписания обновления для отчёта PBIRS."""

    # Типы периодичности
    REC_DAILY = "daily"
    REC_WEEKLY = "weekly"

    def __init__(self, parent: Optional[QWidget], report_name: str):
        """
        Args:
            parent: Родительский виджет
            report_name: Имя отчёта для отображения в заголовке
        """
        super().__init__(parent)
        self.setWindowTitle(f"Создание расписания — {report_name}")
        self.setFixedSize(400, 400)

        self._day_checks: Dict[str, QCheckBox] = {}
        self._result_data: Optional[Dict[str, Any]] = None

        root = QVBoxLayout(self)

        # --- Название расписания ---
        name_label = QLabel("Название расписания:")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Например: Ежедневное обновление")
        root.addWidget(name_label)
        root.addWidget(self._name_edit)

        # --- Тип периодичности ---
        period_group = QGroupBox("Тип периодичности")
        period_layout = QVBoxLayout()
        self._rb_daily = QRadioButton("Ежедневно")
        self._rb_weekly = QRadioButton("Еженедельно")
        self._rb_weekly.setChecked(True)  # по умолчанию еженедельно
        period_layout.addWidget(self._rb_daily)
        period_layout.addWidget(self._rb_weekly)
        period_group.setLayout(period_layout)
        root.addWidget(period_group)

        # --- Дни недели (для еженедельной периодичности) ---
        self._days_group = QGroupBox("Дни недели")
        days_layout = QVBoxLayout()
        for api_name, ru in zip(DAY_NAMES_API, DAY_LABELS_RU):
            cb = QCheckBox(ru)
            cb.setChecked(api_name in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"))
            self._day_checks[api_name] = cb
            days_layout.addWidget(cb)
        self._days_group.setLayout(days_layout)
        root.addWidget(self._days_group)

        # --- Время ---
        time_group = QGroupBox("Время запуска")
        time_layout = QHBoxLayout()

        time_layout.addWidget(QLabel("Часы:"))
        self._hours_combo = QComboBox()
        self._hours_combo.addItems([f"{i:02d}" for i in range(24)])
        self._hours_combo.setCurrentText("09")
        time_layout.addWidget(self._hours_combo)

        time_layout.addWidget(QLabel("Минуты:"))
        self._minutes_combo = QComboBox()
        self._minutes_combo.addItems([f"{i:02d}" for i in range(0, 60, 5)])
        self._minutes_combo.setCurrentText("00")
        time_layout.addWidget(self._minutes_combo)

        time_group.setLayout(time_layout)
        root.addWidget(time_group)

        # --- Подсказка ---
        hint_label = QLabel(
            "Для более гибкой настройки расписания\n"
            "(например, ежемесячно, по несколько раз в день)\n"
            "используйте веб-интерфейс Power BI Report Server."
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(hint_label)

        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Создать расписание")
        create_btn.clicked.connect(self._on_create)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(create_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        root.addLayout(btn_layout)

        # --- Подключаем переключение видимости ---
        self._rb_daily.toggled.connect(self._on_period_type_changed)
        self._rb_weekly.toggled.connect(self._on_period_type_changed)

    def _on_period_type_changed(self):
        """Показывает/скрывает группу дней недели в зависимости от выбора."""
        self._days_group.setVisible(self._rb_weekly.isChecked())

    def _get_period_type(self) -> str:
        """Возвращает выбранный тип периодичности."""
        return self.REC_DAILY if self._rb_daily.isChecked() else self.REC_WEEKLY

    def _on_create(self):
        """Обработчик нажатия кнопки 'Создать расписание'."""
        # Проверка названия
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Создание расписания", "Введите название расписания.")
            self._name_edit.setFocus()
            return

        period_type = self._get_period_type()

        # Проверка дней для еженедельной периодичности
        selected_days: List[str] = []
        if period_type == self.REC_WEEKLY:
            selected_days = [n for n, cb in self._day_checks.items() if cb.isChecked()]
            if not selected_days:
                QMessageBox.warning(self, "Создание расписания", "Выберите хотя бы один день недели.")
                return

        hour = int(self._hours_combo.currentText())
        minute = int(self._minutes_combo.currentText())

        self._result_data = {
            "name": name,
            "period_type": period_type,
            "days": selected_days,
            "hour": hour,
            "minute": minute,
        }
        self.accept()

    def get_result(self) -> Optional[Dict[str, Any]]:
        """
        Возвращает данные расписания после успешного создания.

        Returns:
            Словарь с ключами:
                name (str), period_type (str),
                days (list[str]) — для weekly,
                hour (int), minute (int)
            или None, если диалог был отменён.
        """
        return self._result_data