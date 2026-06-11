import json
from unittest.mock import MagicMock, patch

import requests

from src.utils import get_cbr_currency_rates, read_transactions_json

# =====================================================================
# ТЕСТЫ ДЛЯ ФУНКЦИИ ЧТЕНИЯ JSON (read_transactions_json)
# =====================================================================

def test_read_transactions_json_success(tmp_path):
    """Тест успешного чтения корректного JSON-файла (списка словарей)."""
    # Создаем временный тестовый файл на диске
    test_data = [{"id": 1, "amount": -100}, {"id": 2, "amount": 250}]
    file_path = tmp_path / "test_operations.json"
    file_path.write_text(json.dumps(test_data), encoding="utf-8")

    result = read_transactions_json(file_path)
    assert result == test_data
    assert len(result) == 2


def test_read_transactions_json_nested_dict(tmp_path):
    """Тест чтения JSON, если список транзакций обернут в словарь (ТЗ Skypro)."""
    test_data = {"operations": [{"id": 1, "amount": -100}]}
    file_path = tmp_path / "test_nested.json"
    file_path.write_text(json.dumps(test_data), encoding="utf-8")

    result = read_transactions_json(file_path)
    assert result == [{"id": 1, "amount": -100}]


def test_read_transactions_json_file_not_found():
    """Тест поведения функции, если файл физически отсутствует на диске."""
    # Передаем заведомо несуществующий путь
    result = read_transactions_json("non_existent_file_12345.json")
    assert result == []


def test_read_transactions_json_invalid_format(tmp_path):
    """Тест обработки файла с битым или некорректным синтаксисом JSON."""
    file_path = tmp_path / "broken.json"
    file_path.write_text("{broken json...", encoding="utf-8")

    result = read_transactions_json(file_path)
    assert result == []


# =====================================================================
# ТЕСТЫ ДЛЯ КАСКАДА КУРСОВ ВАЛЮТ (get_cbr_currency_rates)
# =====================================================================

@patch("src.utils.requests.get")
def test_get_currency_rates_nbrb_success(mock_get):
    """Тест успешного получения курсов из первого шлюза (Национальный банк Беларуси)."""
    # Создаем фейковые ответы для трех последовательных запросов (USD, EUR, RUB)
    mock_response_usd = MagicMock()
    mock_response_usd.json.return_value = {"Cur_OfficialRate": 3.2}  # 3.2 BYN за 1 USD

    mock_response_eur = MagicMock()
    mock_response_eur.json.return_value = {"Cur_OfficialRate": 3.5}  # 3.5 BYN за 1 EUR

    mock_response_rub = MagicMock()
    mock_response_rub.json.return_value = {"Cur_OfficialRate": 3.4}  # 3.4 BYN за 100 RUB

    # Передаем подготовленные моки в side_effect (они отработают по очереди)
    mock_get.side_effect = [mock_response_usd, mock_response_eur, mock_response_rub]

    rates = get_cbr_currency_rates()

    # Математический пересчет: rub_per_byn = 3.4 / 100 = 0.034. usd = 3.2 * 0.034 = 0.11
    # (в реальном коде логика пропорции)
    assert len(rates) == 2
    assert rates[0]["currency"] == "USD"
    assert rates[1]["currency"] == "EUR"
    assert isinstance(rates[0]["rate"], float)


@patch("src.utils.requests.get")
def test_get_currency_rates_all_apis_failed(mock_get):
    """Тест: если абсолютно все три интернет-шлюза лежат, возвращаются константы (ТЗ №8)."""
    # Заставляем каждый вызов requests.get выкидывать сетевую ошибку
    mock_get.side_effect = [
        requests.RequestException("NBRB Down"),
        requests.RequestException("AwesomeAPI Down"),
        requests.RequestException("exchangerate Down")
    ]

    rates = get_cbr_currency_rates()

    # Проверяем, что вернулись наши жестко зашитые дефолтные значения (fallback_rates)
    assert rates == [
        {"currency": "USD", "rate": 89.45},
        {"currency": "EUR", "rate": 96.12}
    ]
