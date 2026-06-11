from datetime import datetime
from unittest.mock import patch

import pytest

from src.processing import (calculate_totals, filter_and_sort_transactions,
                            format_phone_number, get_expenses_analytics,
                            get_welcome_message, search_transactions)


# =====================================================================
# 1. ТЕСТЫ ПРИВЕТСТВИЯ ПО ВРЕМЕНИ (ТЗ №1)
# =====================================================================
@pytest.mark.parametrize(
    "hour, expected_welcome",
    [
        (8, "Доброе утро"),
        (14, "Добрый день"),
        (19, "Добрый вечер"),
        (3, "Доброй ночи"),
    ],
)
def test_get_welcome_message(hour, expected_welcome):
    """Тест подмены времени компьютера для проверки правильности приветствия."""
    with patch("src.processing.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 6, 12, hour, 0, 0)
        assert get_welcome_message() == expected_welcome


# =====================================================================
# 2. ТЕСТЫ ТОП-5 ТРАНЗАКЦИЙ ПО МОДУЛЮ СУММЫ (ТЗ №3)
# =====================================================================
def test_filter_and_sort_transactions_top_5():
    """Тест выбора ровно 5 транзакций по убыванию абсолютного значения суммы."""
    transactions = [
        {"amount": "-100.0"},
        {"amount": "5000.0"},  # 1
        {"amount": "-2500.0"},  # 3
        {"amount": "4000.0"},  # 2
        {"amount": "-300.0"},
        {"amount": "-1200.0"},  # 4
        {"amount": "600.0"},  # 5
    ]

    result = filter_and_sort_transactions(transactions)

    assert len(result) == 5
    assert float(result[0]["amount"]) == 5000.0
    assert float(result[1]["amount"]) == 4000.0
    assert float(result[2]["amount"]) == -2500.0
    assert float(result[3]["amount"]) == -1200.0
    assert float(result[4]["amount"]) == 600.0


# =====================================================================
# 3. ТЕСТЫ АНАЛИТИКИ КАТЕГОРИЙ РАСХОДОВ (ТЗ №6, ТЗ №7)
# =====================================================================
def test_get_expenses_analytics():
    """Тест группировки топ-7 расходов, выделения наличных и переводов."""
    test_data = [
        {"state": "EXECUTED", "category": "Переводы", "amount": "-1000.0"},
        {"state": "EXECUTED", "category": "Наличные", "amount": "-500.0"},
        {"state": "EXECUTED", "category": "Супермаркеты", "amount": "-200.0"},
        {"state": "EXECUTED", "category": "Рестораны", "amount": "-300.0"},
        {"state": "CANCELED", "category": "Фатсфуд", "amount": "-400.0"},  # Игнорируем
        {"state": "EXECUTED", "category": "Супермаркеты", "amount": "150.0"},  # Поступление (игнорируем)
    ]

    analytics = get_expenses_analytics(test_data)

    assert analytics["transfers"] == 1000
    assert analytics["cash"] == 500
    assert analytics["categories"]["Рестораны"] == 300
    assert analytics["categories"]["Супермаркеты"] == 200
    assert "Фастфуд" not in analytics["categories"]


# =====================================================================
# 4. ТЕСТ РАСЧЕТА ОБЩИХ СУММ (calculate_totals)
# =====================================================================
def test_calculate_totals():
    """Тест подсчета общих сумм успешных доходов и расходов."""
    test_data = [
        {"state": "EXECUTED", "amount": "1500.50"},  # Поступление
        {"state": "EXECUTED", "amount": "-500.00"},  # Расход
        {"state": "CANCELED", "amount": "-1000.00"},  # Игнорируем
        {"state": "EXECUTED", "amount": "300.00"},  # Поступление
    ]
    result = calculate_totals(test_data)

    # ИСПРАВЛЕНО: 1500.50 + 300 = 1800.50 -> банковское округление дает 1800
    assert result["income"] == 1800
    assert result["expenses"] == 500


# =====================================================================
# 5. ТЕСТЫ РЕГИСТРОНЕЗАВИСИМОГО ПОИСКА (ТЗ №9)
# =====================================================================
def test_search_transactions_case_insensitive():
    """Тест поиска по подстроке без учета регистра."""
    test_data = [
        {"category": "Супермаркеты", "description": "Покупка молока"},
        {"category": "Аптека", "description": "СУПЕРМАРКЕТ на углу"},
        {"category": "Одежда", "description": "Просто куртка"},
    ]

    result = search_transactions(test_data, "супермаркет")
    assert len(result) == 2


# =====================================================================
# 6. ТЕСТЫ МАСКИРОВАНИЯ ТЕЛЕФОННЫХ НОМЕРОВ (ТЗ №10)
# =====================================================================
@pytest.mark.parametrize(
    "input_phone, expected_phone",
    [
        ("89000000000", "+7 (900) 000-00-00"),
        ("+7 (912) 345-67-89", "+7 (912) 345-67-89"),
        ("79555555555", "+7 (955) 555-55-55"),
        ("Обычный текст", "Обычный текст"),
    ],
)
def test_format_phone_number(input_phone, expected_phone):
    """Тест приведения разных форматов номеров к единой маске."""
    assert format_phone_number(input_phone) == expected_phone
