import json
from unittest.mock import patch

import pytest

from src.reports import analyze_cashback_categories


@pytest.fixture
def mock_report_data():
    """Фикстура с разнородными транзакциями для проверки фильтрации по датам."""
    return [
        {
            "date": "2026-06-15T12:00:00",
            "category": "Супермаркеты",
            "amount": "-1000.00",
            "cashback": "50.0"
        },
        {
            "date": "2026-06-16T18:30:00",
            "category": "Рестораны",
            "amount": "-2000.00",
            # Поле cashback отсутствует — должен сработать расчет 1% от 2000 = 20
        },
        {
            "date": "2026-06-17T09:00:00",
            "category": "Супермаркеты",
            "amount": "500.00",  # Поступление (доход) — должно быть проигнорировано
            "cashback": "0"
        },
        {
            "date": "2026-05-01T10:00:00",  # Другой месяц (май) — должен быть проигнорирован
            "category": "Фастфуд",
            "amount": "-500.00",
            "cashback": "25.0"
        },
        {
            "Дата операции": "2026-06-18 14:00:00",  # Проверка поддержки альтернативного ключа даты
            "Категория": "Такси",
            "Сумма операции": "-350.50",
            "Кэшбэк": "15.0"
        },
        {
            "date": "invalid-date-format",  # Битый формат даты — должен безопасно пропуститься
            "category": "Кино",
            "amount": "-300.00"
        }
    ]


def test_analyze_cashback_categories_success(mock_report_data):
    """Тест успешного анализа кешбэка за конкретный месяц с расчетом базовой ставки."""
    # Запускаем анализ за июнь (06) 2026 года
    json_result = analyze_cashback_categories(mock_report_data, 2026, 6)

    # Функция возвращает JSON-строку, преобразуем её обратно в словарь для проверки
    result_dict = json.loads(json_result)

    # Проверяем результаты:
    # 1. Супермаркеты: только расход на -1000 с кешбэком 50 (доход игнорируется) -> 50
    assert result_dict["Супермаркеты"] == 50

    # 2. Рестораны: расход -2000, кешбэка нет -> 1% от 2000 = 20
    assert result_dict["Рестораны"] == 20

    # 3. Такси: расход -350.50 с кешбэком 15 -> 15 (округляется до целого)
    assert result_dict["Такси"] == 15

    # Проверяем, что майский расход не попал в отчет
    assert "Фастфуд" not in result_dict
    assert "Кино" not in result_dict


def test_analyze_cashback_categories_invalid_input():
    """Тест поведения функции при передаче некорректного типа данных вместо списка."""
    # Передаем строку вместо списка словарей
    json_result = analyze_cashback_categories("not a list", 2026, 6)

    result_dict = json.loads(json_result)
    assert result_dict == {}


@patch("src.reports.logger")  # <-- ИСПРАВЛЕНО: теперь указываем точный модуль src.reports
def test_analyze_cashback_categories_logging(mock_logger, mock_report_data):
    """Тест проверки вызовов логгера (INFO и WARNING) в процессе анализа."""
    analyze_cashback_categories(mock_report_data, 2026, 6)

    # Проверяем, что логгер зафиксировал старт и успешное завершение работы
    assert mock_logger.info.call_count >= 2

    # Проверяем логирование некорректного ввода
    analyze_cashback_categories(None, 2026, 6)
    mock_logger.warning.assert_called_with("На вход подан некорректный тип данных (ожидался list)")


def test_analyze_cashback_categories_empty_list():
    """Тест возврата пустого JSON, если за указанный период нет транзакций."""
    json_result = analyze_cashback_categories([], 2026, 6)
    assert json.loads(json_result) == {}
