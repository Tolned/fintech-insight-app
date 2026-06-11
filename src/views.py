import json
from pathlib import Path

from src.processing import (filter_and_sort_transactions, format_phone_number,
                            get_top_categories, get_welcome_message,
                            search_transactions)
from src.utils import get_cbr_currency_rates, read_transactions_json


def run_app() -> None:
    """Генерирует аналитический отчет и выводит актуальные курсы валют на экран."""
    welcome = get_welcome_message()
    print(f"=== {welcome}!\n")

    # Находим файл данных operations.json
    data_dir = Path(__file__).resolve().parent / ".." / "data"
    full_path = (data_dir / "operations.json").resolve()

    if not full_path.exists():
        full_path = (Path(__file__).resolve().parent / ".." / "operations.json").resolve()

    transactions = read_transactions_json(full_path)

    # 1. ЗАПРАШИВАЕМ КУРСЫ ВАЛЮТ ИЗ API
    live_currency_rates = get_cbr_currency_rates()

    # --- НОВЫЙ БЛОК: КРАСИВОЕ ОТОБРАЖЕНИЕ КУРСОВ В КОНСОЛИ ---
    print("┌────────────────────────────────────────┐")
    print("│      АКТУАЛЬНЫЙ КУРС ВАЛЮТ (ЦБ РФ)     │")
    print("├────────────────────────────────────────┤")
    for rate_info in live_currency_rates:
        currency = rate_info.get("currency")
        rate = rate_info.get("rate")
        print(f"│  1 {currency} = {rate:<29} руб. │")
    print("└────────────────────────────────────────┘\n")
    # -------------------------------------------------------

    print(f"Успешно загружено записей: {len(transactions)}\n")

    if not transactions:
        print("Нет данных для обработки.")
        return

    # Формируем итоговую структуру по ТЗ
    report = {
        "user_data": {
            "welcome": welcome,
            "cards": [{"type": "Visa Platinum", "number": "*4321", "balance": 245000.0}],
        },
        "top_transactions": filter_and_sort_transactions(transactions),
        "expenses": {
            "total_categories": get_top_categories(transactions),
        },
        "currency_rates": live_currency_rates,
        "stock_prices": [
            {"stock": "AAPL", "price": 182.40},
            {"stock": "GAZP", "price": 124.15},
        ],
    }

    print("--- 1. ОСНОВНОЙ JSON-ОТЧЕТ ПО ТЗ ---")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\n" + "=" * 50 + "\n")

    # Демонстрация дополнительных функций
    print("--- 2. ДЕМОНСТРАЦИЯ ДОПОЛНИТЕЛЬНЫХ ФУНКЦИЙ ---")
    search_results = search_transactions(transactions, "супермаркет")
    print(f"\n[Поиск] Результаты по запросу 'супермаркет' (найдено: {len(search_results)}):")
    for t in search_results[:1]:
        print(f" - Категория: {t.get('category')} | Описание: {t.get('description')} | Сумма: {t.get('amount')}")

    phone = "89000000000"
    print(f"\n[Маскирование] Телефон: {phone} -> {format_phone_number(phone)}")
