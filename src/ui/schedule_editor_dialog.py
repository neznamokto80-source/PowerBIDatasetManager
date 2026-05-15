#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалог редактирования расписания обновления датасета Power BI (PATCH refreshSchedule).
"""

import re
from typing import Any, Dict, List, Optional, Set

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

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

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

DEFAULT_TIMEZONES = [
    "UTC",
    "Russian Standard Time",
    "Central Asia Standard Time",
    "Ekaterinburg Standard Time",
    "W. Europe Standard Time",
    "Central European Standard Time",
    "GMT Standard Time",
    "Eastern Standard Time",
    "Pacific Standard Time",
]


class ScheduleEditorDialog(QDialog):
    """Редактор полей refreshSchedule (дни, времена, пояс, уведомления, вкл/выкл)."""

    ACTION_CANCEL = 0
    ACTION_SAVE = 1
    ACTION_DELETE = 2

    def __init__(
        self,
        parent: Optional[QWidget],
        initial_schedule: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Расписание обновления датасета")
        self.resize(520, 480)
        self._result_action = self.ACTION_CANCEL

        sched: Dict[str, Any] = initial_schedule if isinstance(initial_schedule, dict) else {}
        if isinstance(sched.get("data"), dict):
            sched = sched["data"]

        self._day_checks: Dict[str, QCheckBox] = {}
        root = QVBoxLayout(self)

        days_group = QGroupBox("Дни недели")
        days_layout = QVBoxLayout()
        selected_days = sched.get("days") or []
        for api_name, ru in zip(DAY_NAMES_API, DAY_LABELS_RU):
            cb = QCheckBox(ru)
            cb.setChecked(api_name in selected_days)
            self._day_checks[api_name] = cb
            days_layout.addWidget(cb)
        days_group.setLayout(days_layout)
        root.addWidget(days_group)

        times_group = QGroupBox("Время срабатывания (локальное время выбранного пояса)")
        times_layout = QVBoxLayout()
        self._times_list = QListWidget()
        times = sched.get("times") or []
        for t in times:
            if isinstance(t, str) and t.strip():
                self._times_list.addItem(t.strip())
        if self._times_list.count() == 0:
            self._times_list.addItem("03:00")
        times_row = QHBoxLayout()
        # Выпадающие списки для часов и минут
        self._hours_combo = QComboBox()
        self._hours_combo.addItems([f"{i:02d}" for i in range(24)])  # 00-23
        self._minutes_combo = QComboBox()
        self._minutes_combo.addItems(["00", "30"])  # только 00 и 30
        # Установить значения по умолчанию 03:00
        self._hours_combo.setCurrentText("03")
        self._minutes_combo.setCurrentText("00")
        add_btn = QPushButton("Добавить время")
        add_btn.clicked.connect(self._add_time)
        rem_btn = QPushButton("Удалить выбранное")
        rem_btn.clicked.connect(self._remove_time)
        times_row.addWidget(QLabel("Часы:"))
        times_row.addWidget(self._hours_combo)
        times_row.addWidget(QLabel("Минуты:"))
        times_row.addWidget(self._minutes_combo)
        times_row.addWidget(add_btn)
        times_row.addWidget(rem_btn)
        times_layout.addWidget(self._times_list)
        times_layout.addLayout(times_row)
        times_group.setLayout(times_layout)
        root.addWidget(times_group)

        form_host = QWidget()
        form = QVBoxLayout(form_host)
        tz_row = QHBoxLayout()
        tz_row.addWidget(QLabel("Часовой пояс (Windows):"))
        self._tz_combo = QComboBox()
        self._tz_combo.setEditable(True)
        tz = (sched.get("localTimeZoneId") or "").strip() or "Central Asia Standard Time"
        tz_items = sorted(set(DEFAULT_TIMEZONES + ([tz] if tz else [])))
        self._tz_combo.addItems(tz_items)
        self._tz_combo.setCurrentText(tz)
        tz_row.addWidget(self._tz_combo, stretch=1)
        form.addLayout(tz_row)

        notify_row = QHBoxLayout()
        notify_row.addWidget(QLabel("Уведомления:"))
        self._notify_combo = QComboBox()
        for opt, label in (
            ("NoNotification", "Без уведомлений"),
            ("MailOnFailure", "Почта при ошибке"),
            ("MailOnCompletion", "Почта по завершении"),
        ):
            self._notify_combo.addItem(label, opt)
        nopt = sched.get("notifyOption") or "MailOnFailure"
        idx = max(0, self._notify_combo.findData(nopt))
        self._notify_combo.setCurrentIndex(idx)
        notify_row.addWidget(self._notify_combo, stretch=1)
        form.addLayout(notify_row)

        self._enabled_cb = QCheckBox("Расписание включено")
        self._enabled_cb.setChecked(bool(sched.get("enabled", True)))
        form.addWidget(self._enabled_cb)
        root.addWidget(form_host)

        hint = QLabel(
            "Дни и время задаются в выбранном часовом поясе (как в Power BI Service)."
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._on_save)
        del_btn = QPushButton("Удалить расписание")
        del_btn.setToolTip("Отключить запланированное обновление в Power BI")
        del_btn.clicked.connect(self._on_delete)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def action(self) -> int:
        return self._result_action

    def get_schedule_payload(self) -> Dict[str, Any]:
        days = [n for n, cb in self._day_checks.items() if cb.isChecked()]
        times: List[str] = []
        seen: Set[str] = set()
        for i in range(self._times_list.count()):
            text = self._times_list.item(i).text().strip()
            if text and text not in seen:
                seen.add(text)
                times.append(text)
        notify = self._notify_combo.currentData()
        if notify is None:
            notify = "MailOnFailure"
        return {
            "enabled": self._enabled_cb.isChecked(),
            "days": days,
            "times": times,
            "localTimeZoneId": self._tz_combo.currentText().strip(),
            "notifyOption": notify,
        }

    def _add_time(self) -> None:
        hours = self._hours_combo.currentText()
        minutes = self._minutes_combo.currentText()
        time_text = f"{hours}:{minutes}"
        self._times_list.addItem(time_text)
        # Сбросить на значения по умолчанию (03:00)
        self._hours_combo.setCurrentText("03")
        self._minutes_combo.setCurrentText("00")

    def _remove_time(self) -> None:
        row = self._times_list.currentRow()
        if row >= 0:
            self._times_list.takeItem(row)

    def _validate(self) -> bool:
        pl = self.get_schedule_payload()
        if pl["enabled"]:
            if not pl["days"]:
                QMessageBox.warning(self, "Проверка", "Выберите хотя бы один день недели.")
                return False
            if not pl["times"]:
                QMessageBox.warning(
                    self,
                    "Проверка",
                    "Добавьте хотя бы одно время или снимите флажок «Расписание включено».",
                )
                return False
            if not pl["localTimeZoneId"]:
                QMessageBox.warning(self, "Проверка", "Укажите часовой пояс.")
                return False
            for t in pl["times"]:
                if not TIME_PATTERN.match(t):
                    QMessageBox.warning(self, "Проверка", f"Некорректное время: {t}")
                    return False
        return True

    def _on_save(self) -> None:
        if not self._validate():
            return
        self._result_action = self.ACTION_SAVE
        self.accept()

    def _on_delete(self) -> None:
        reply = QMessageBox.question(
            self,
            "Удаление расписания",
            "Отключить запланированное обновление для этого датасета?\n"
            "(В Power BI будет выключено автообновление по расписанию.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._result_action = self.ACTION_DELETE
        self.accept()
