#!/usr/bin/env python3
"""
Модуль для управления прогресс-баром в приложении Power BI Dataset Monitor & Manager.
Предоставляет удобный интерфейс для показа/скрытия прогресс-бара с различными текстами.
"""

from typing import Optional


class ProgressManager:
    """Менеджер для управления прогресс-баром."""
    
    def __init__(self, main_window):
        """
        Инициализирует менеджер прогресс-бара.
        
        Args:
            main_window: Главное окно приложения, содержащее progress_bar
        """
        self.main_window = main_window
    
    def show(self, text: Optional[str] = None, indeterminate: bool = True):
        """
        Показывает прогресс-бар.
        
        Args:
            text: Текст для отображения в прогресс-баре. Если None, используется текст по умолчанию.
            indeterminate: Если True, прогресс-бар будет неопределенным (анимированным).
                          Если False, будет отображаться конкретный прогресс (0-100).
        """
        if not hasattr(self.main_window, 'progress_bar'):
            return
        
        progress_bar = self.main_window.progress_bar
        
        # Показываем прогресс-бар
        progress_bar.setVisible(True)
        
        # Устанавливаем режим прогресса
        if indeterminate:
            progress_bar.setRange(0, 0)  # Неопределенный прогресс
        else:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
        
        # Устанавливаем текст
        if text:
            progress_bar.setFormat(text)
        else:
            progress_bar.setFormat("Загрузка...")
    
    def hide(self):
        """Скрывает прогресс-бар."""
        if hasattr(self.main_window, 'progress_bar'):
            self.main_window.progress_bar.setVisible(False)
    
    def update(self, value: int, maximum: int = 100, text: Optional[str] = None):
        """
        Обновляет прогресс-бар с конкретным значением.
        
        Args:
            value: Текущее значение прогресса (0-100)
            maximum: Максимальное значение (по умолчанию 100)
            text: Текст для отображения (опционально)
        """
        if not hasattr(self.main_window, 'progress_bar'):
            return
        
        progress_bar = self.main_window.progress_bar
        
        # Устанавливаем диапазон и значение
        progress_bar.setRange(0, maximum)
        progress_bar.setValue(value)
        
        # Устанавливаем текст, если передан
        if text:
            progress_bar.setFormat(text)
    
    def set_indeterminate(self, indeterminate: bool = True):
        """
        Устанавливает режим неопределенного прогресса.
        
        Args:
            indeterminate: Если True, прогресс-бар будет неопределенным.
        """
        if not hasattr(self.main_window, 'progress_bar'):
            return
        
        if indeterminate:
            self.main_window.progress_bar.setRange(0, 0)
        else:
            self.main_window.progress_bar.setRange(0, 100)
    
    def is_visible(self) -> bool:
        """Проверяет, виден ли прогресс-бар."""
        if hasattr(self.main_window, 'progress_bar'):
            return self.main_window.progress_bar.isVisible()
        return False
    
    def with_progress(self, text: Optional[str] = None, indeterminate: bool = True):
        """
        Контекстный менеджер для автоматического показа/скрытия прогресс-бара.
        
        Пример использования:
            with progress_manager.with_progress("Загрузка данных..."):
                # Код, выполняемый во время показа прогресс-бара
                load_data()
        
        Args:
            text: Текст для отображения
            indeterminate: Режим неопределенного прогресса
        """
        return ProgressContext(self, text, indeterminate)


class ProgressContext:
    """Контекстный менеджер для прогресс-бара."""
    
    def __init__(self, manager: ProgressManager, text: Optional[str], indeterminate: bool):
        self.manager = manager
        self.text = text
        self.indeterminate = indeterminate
    
    def __enter__(self):
        self.manager.show(self.text, self.indeterminate)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.hide()
        return False  # Не подавляем исключения