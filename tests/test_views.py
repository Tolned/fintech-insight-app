from unittest.mock import patch

import pytest

from src.views import run_app


@pytest.fixture
def mock_transactions():
    """Фикстура с тестовыми транзакциями."""
    return [
        {
            "date": "2026-06-11T20:00:00",
            "amount": "-500.00",
            "category": "Супермаркеты",
            "description": "Покупка продуктов",
            "state": "EXECUTED"
        },
        {
            "date": "2026-06-10T12:00:00",
            "amount": "-1500.00",
            "category": "Одежда",
            "description": "Куртка купленная в супермаркет",
            "state": "EXECUTED"
        }
    ]


@pytest.fixture
def mock_currency_rates():
    """Фикстура с тестовыми курсами валют."""
    return [
        {"currency": "USD", "rate": 89.45},
        {"currency": "EUR", "rate": 96.12}
    ]


@patch("src.views.read_transactions_json")
@patch("src.views.get_cbr_currency_rates")
@patch("src.views.Path.exists")
def test_run_app_success(mock_exists, mock_get_rates, mock_read_json, mock_transactions, mock_currency_rates, capsys):
    """Тест успешного выполнения run_app с выводом отчета."""
    # Настраиваем моки внешней среды
    mock_exists.return_value = True
    mock_read_json.return_value = mock_transactions
    mock_get_rates.return_value = mock_currency_rates

    # Запускаем тестируемую функцию
    run_app()

    # Перехватываем всё, что функция напечатала в консоль
    captured = capsys.readouterr()

    # Проверяем наличие ключевых элементов ТЗ в консольном выводе
    assert "=== Запуск аналитического виджета ===" in captured.out or "===" in captured.out
    assert "АКТУАЛЬНЫЙ КУРС ВАЛЮТ (ЦБ РФ)" in captured.out
    assert "1 USD = 89.45" in captured.out
    assert "Успешно загружено записей: 2" in captured.out
    assert "--- 1. ОСНОВНОЙ JSON-ОТЧЕТ ПО ТЗ ---" in captured.out
    assert "--- 2. ДЕМОНСТРАЦИЯ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ ---" in captured.out

    # Проверяем, что отработал внутренний демонстрационный поиск
    assert "[Поиск] Результаты по запросу 'супермаркет'" in captured.out


@patch("src.views.read_transactions_json")
@patch("src.views.get_cbr_currency_rates")
@patch("src.views.Path.exists")
def test_run_app_empty_transactions(mock_exists, mock_get_rates, mock_read_json, mock_currency_rates, capsys):
    """Тест поведения run_app, когда файл пустой или транзакции отсутствуют."""
    mock_exists.return_value = True
    mock_read_json.return_value = []
    mock_get_rates.return_value = mock_currency_rates

    run_app()

    captured = capsys.readouterr()

    assert "Успешно загружено записей: 0" in captured.out
    assert "Нет данных для обработки." in captured.out
    # Проверяем, что основной отчет не вывелся, так как сработал return
    assert "--- 1. ОСНОВНОЙ JSON-ОТЧЕТ ПО ТЗ ---" not in captured.out


@patch("src.views.read_transactions_json")
@patch("src.views.get_cbr_currency_rates")
@patch("src.views.Path.exists")
def test_run_app_file_not_found_fallback(mock_exists, mock_get_rates, mock_read_json):
    """Тест логики поиска файла: если в data/ файла нет, ищет его в корне проекта."""
    # Первые вызовы exists() для папки data вернут False, а для корня — True
    mock_exists.side_effect = [False, True]
    mock_read_json.return_value = []
    mock_get_rates.return_value = []

    run_app()

    # Проверяем, что read_transactions_json вызвался один раз, несмотря на отсутствие в data/
    mock_read_json.assert_called_once()
