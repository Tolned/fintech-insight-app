import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

# Настройка логирования по стандарту PEP 8
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ==========================================
# 1. Сервис: Выгодные категории кешбэка
# ==========================================
def analyze_cashback_categories(
    data: List[Dict[str, Any]], year: int, month: int
) -> str:
    """Анализирует потенциальный заработок кешбэка по категориям за указанный месяц.

    Использует функциональную фильтрацию транзакций по заданному периоду.
    Округляет накопленный кешбэк по каждой категории до целых чисел.
    """
    logger.info(
        f"Старт анализа выгодности кешбэка за период {year}-{month:02d}"
    )

    if not isinstance(data, list):
        logger.warning("На вход подан некорректный тип данных (ожидался list)")
        return json.dumps({}, ensure_ascii=False)

        # Функциональная фильтрация транзакций по году, месяцу и наличию расходов

    def is_target_period(transaction_item: Dict[str, Any]) -> bool:
        try:
            date_str = transaction_item.get("date") or transaction_item.get("Дата операции")
            if not date_str:
                return False
            dt = datetime.fromisoformat(str(date_str).replace("Z", ""))

            # Уникальные имена: tx_amount и transaction_item не пересекаются с внешним scope
            tx_amount = float(transaction_item.get("amount") or transaction_item.get("Сумма операции") or 0)
            return dt.year == year and dt.month == month and tx_amount < 0
        except (ValueError, TypeError):
            return False

    target_transactions = list(filter(is_target_period, data))

    cashback_analysis: Dict[str, float] = {}

    for tx in target_transactions:
        category = tx.get("category") or tx.get("Категория") or "Остальное"
        cashback_val = tx.get("cashback") or tx.get("Кэшбэк") or 0.0

        try:
            # Если кешбэк не посчитан банком, закладываем базовую ставку 1% на расходы
            if not cashback_val:
                amount = float(
                    tx.get("amount") or tx.get("Сумма операции") or 0
                )
                cashback_val = abs(amount) * 0.01
            else:
                cashback_val = float(cashback_val)

            cashback_analysis[category] = (
                cashback_analysis.get(category, 0.0) + cashback_val
            )
        except (ValueError, TypeError):
            continue

    # Округляем итоговые суммы до целых чисел
    result = {k: round(v) for k, v in cashback_analysis.items()}

    logger.info("Анализ кешбэка успешно завершен")
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==========================================
# 2. Сервис: Инвесткопилка
# ==========================================
def investment_bank(
    month: str, transactions: List[Dict[str, Any]], limit: int
) -> float:
    """Рассчитывает сумму округления трат, отправляемую в Инвесткопилку."""
    logger.info(
        f"Старт расчета инвесткопилки за месяц {month} с порогом {limit}"
    )

    # Альтернативная проверка без квадратных скобок (защита от багов разметки)
    if limit != 10 and limit != 50 and limit != 100:
        logger.error(f"Недопустимый порог округления: {limit}")
        return 0.0

    if not isinstance(transactions, list):
        return 0.0

    # Фильтрация транзакций строго по указанному месяцу 'YYYY-MM' и только для расходов
    def is_valid_expense(tx: Dict[str, Any]) -> bool:
        try:
            date_str = tx.get("Дата операции") or tx.get("date")
            amount = float(tx.get("Сумма операции") or tx.get("amount") or 0)
            if not date_str or amount >= 0:
                return False
            return str(date_str).startswith(month)
        except (ValueError, TypeError):
            return False

    filtered_txs = filter(is_valid_expense, transactions)

    def calculate_round_up(tx: Dict[str, Any]) -> float:
        try:
            # Берем модуль суммы расхода
            amount = abs(
                float(tx.get("Сумма операции") or tx.get("amount") or 0)
            )
            if amount == 0:
                return 0.0

            # Вычисляем сумму, до которой нужно округлить операцию
            if amount % limit == 0:
                return 0.0
            rounded_amount = ((int(amount) // limit) + 1) * limit
            return round(rounded_amount - amount, 2)
        except (ValueError, TypeError):
            return 0.0

    # Функциональное преобразование (map) списка транзакций в список сумм округлений
    money_saved = sum(map(calculate_round_up, filtered_txs))

    logger.info(f"В инвесткопилку успешно отложено: {money_saved} ₽")
    return round(money_saved, 2)


# ==========================================
# 3. Сервис: Простой поиск
# ==========================================
def simple_search(transactions: List[Dict[str, Any]], query: str) -> str:
    """Осуществляет регистронезависимый поиск по подстроке."""
    logger.info(f"Запуск простого поиска по запросу: '{query}'")

    if not query or not isinstance(transactions, list):
        return json.dumps([], ensure_ascii=False)

    clean_query = str(query).lower().strip()

    # Фильтрация по совпадению подстроки в описании или категории
    matched = list(
        filter(
            lambda tx: clean_query in str(tx.get("description", "")).lower()
            or clean_query in str(tx.get("category", "")).lower()
            or clean_query in str(tx.get("Описание", "")).lower()
            or clean_query in str(tx.get("Категория", "")).lower(),
            transactions,
        )
    )

    logger.info(f"Простой поиск завершен. Найдено записей: {len(matched)}")
    return json.dumps(matched, ensure_ascii=False, indent=2)


# ==========================================
# 4. Сервис: Поиск по телефонным номерам
# ==========================================
def search_phone_numbers(transactions: List[Dict[str, Any]]) -> str:
    """Возвращает транзакции, содержащие мобильные номера в описании."""
    logger.info("Запуск поиска транзакций с номерами телефонов")

    if not isinstance(transactions, list):
        return json.dumps([], ensure_ascii=False)

    # Регулярное выражение для поиска различных форматов мобильных номеров РФ
    phone_pattern = re.compile(
        r"(\+7|8)\s?\(?\d{3}\)?\s?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
    )

    def has_phone(tx: Dict[str, Any]) -> bool:
        description = str(tx.get("description") or tx.get("Описание") or "")
        return bool(phone_pattern.search(description))

    matched_txs = list(filter(has_phone, transactions))

    logger.info(f"Поиск телефонов завершен. Найдено: {len(matched_txs)}")
    return json.dumps(matched_txs, ensure_ascii=False, indent=2)


# ==========================================
# 5. Сервис: Поиск переводов физлицам
# ==========================================
def search_personal_transfers(transactions: List[Dict[str, Any]]) -> str:
    """Находит переводы физлицам (Категория 'Переводы', в описании Имя Ф.)."""
    logger.info("Запуск поиска переводов физическим лицам")

    if not isinstance(transactions, list):
        return json.dumps([], ensure_ascii=False)

    # Шаблон: Имя на кириллице, пробел, заглавная буква фамилии и точка (Валерий А.)
    name_pattern = re.compile(r"[А-Я][а-я]+\s[А-Я]\.")

    def is_personal_transfer(tx: Dict[str, Any]) -> bool:
        category = str(tx.get("category") or tx.get("Категория") or "")
        description = str(tx.get("description") or tx.get("Описание") or "")

        if category.strip().lower() != "переводы":
            return False

        return bool(name_pattern.search(description))

    matched_transfers = list(filter(is_personal_transfer, transactions))

    logger.info(
        f"Поиск переводов завершен. Найдено совпадений: {len(matched_transfers)}"
    )
    return json.dumps(matched_transfers, ensure_ascii=False, indent=2)


if __name__ == "__main__":  # pragma: no cover
    # Тестовый набор транзакций по требованиям ТЗ
    test_data = [
        {
            "Дата операции": "2021-12-21",
            "Сумма операции": -1712.00,
            "Категория": "Супермаркеты",
            "Описание": "Покупка в магазине Лента",
            "Кэшбэк": 17.12
        },
        {
            "Дата операции": "2021-12-20",
            "Сумма операции": -5030.50,
            "Категория": "АЗС",
            "Описание": "Лукойл",
            "Кэшбэк": 251.50
        },
        {
            "Дата операции": "2021-12-16",
            "Сумма операции": -421.00,
            "Категория": "Различные товары",
            "Описание": "Ozon.ru"
        },
        {
            "Дата операции": "2021-12-15",
            "Сумма операции": -500.00,
            "Категория": "Связь",
            "Описание": "Я МТС +7 921 11-22-33"
        },
        {
            "Дата операции": "2021-12-14",
            "Сумма операции": -600.00,
            "Категория": "Связь",
            "Описание": "Тинькофф Мобайл 89955555555"
        },
        {
            "Дата операции": "2021-12-12",
            "Сумма операции": -1500.00,
            "Категория": "Переводы",
            "Описание": "Валерий А."
        }
    ]

    print("\n--- 1. ТЕСТ: Выгодные категории кешбэка (Декабрь 2021) ---")
    print(analyze_cashback_categories(test_data, year=2021, month=12))

    print("\n--- 2. ТЕСТ: Инвесткопилка (Порог 50 ₽) ---")
    saved_money = investment_bank(month="2021-12", transactions=test_data, limit=50)
    print(f"Отложено в копилку: {saved_money} ₽")

    print("\n--- 3. ТЕСТ: Простой поиск по подстроке (Запрос: 'лента') ---")
    print(simple_search(test_data, query="лЕНТа"))

    print("\n--- 4. ТЕСТ: Поиск по телефонным номерам ---")
    print(search_phone_numbers(test_data))

    print("\n--- 5. ТЕСТ: Поиск переводов физлицам ---")
    print(search_personal_transfers(test_data))
