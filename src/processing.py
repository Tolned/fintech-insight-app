import re
from datetime import datetime


def calculate_totals(transactions: list) -> dict:
    """
    Вычисляет общие суммы успешных поступлений и расходов.

    Фильтрует транзакции со статусом 'EXECUTED', разделяет их на
    положительные (доходы) и отрицательные (расходы) потоки, после
    чего агрегирует и округляет итоговые значения до целых чисел.

    Args:
        transactions (list): Список транзакций (словарей).

    Returns:
        dict: Словарь с ключами 'income' (поступления) и 'expenses' (расходы),
              где значения округлены до целых чисел.
    """
    income = 0
    expenses = 0
    for t in transactions:
        if isinstance(t, dict) and t.get("state") == "EXECUTED":
            amount = float(t.get("amount", 0))
            if amount > 0:
                income += amount
            else:
                expenses += abs(amount)
    return {"income": round(income), "expenses": round(expenses)}


def get_welcome_message() -> str:
    """Возвращает приветствие в зависимости от текущего времени (ТЗ №1)."""
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        return "Доброе утро"
    elif 12 <= current_hour < 18:
        return "Добрый день"
    elif 18 <= current_hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def filter_and_sort_transactions(transactions: list) -> list:
    """
    Фильтрует список транзакций и возвращает топ-5 по величине суммы.

        Отсекает некорректные записи, оставляя только словари с заполненным
        полем 'amount'. Сортирует их по убыванию абсолютного значения (модуля)
        суммы, выводя самые крупные расходы и поступления в начало списка.

        Args:
            transactions (list): Исходный список транзакций.

        Returns:
            list: Список, содержащий ровно 5 (или меньше, если данных недостаточно)
                  наиболее крупных транзакций, отсортированных по убыванию.
    """
    valid = [t for t in transactions if isinstance(t, dict) and "amount" in t]
    # Сортируем по убыванию модуля суммы (максимальные траты и поступления наверх)
    return sorted(valid, key=lambda x: abs(float(x.get("amount", 0))), reverse=True)[:5]


def get_top_categories(transactions: list) -> dict:
    """Группирует топ-7 категорий расходов, остальное в 'Остальное' (ТЗ №6, №7)."""
    categories = {}
    for t in transactions:
        if not isinstance(t, dict) or t.get("state") != "EXECUTED":
            continue
        cat = t.get("category", "Остальное")
        # Исключаем переводы и наличные из общих категорий, если они выделены отдельно по ТЗ
        if cat in ["Переводы", "Наличные"]:
            continue
        amount = round(float(t.get("amount", 0)))
        if amount < 0:  # Расходы
            categories[cat] = categories.get(cat, 0) + abs(amount)

    # Сортируем и берем топ-7
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    top_7 = dict(sorted_cats[:7])

    # Агрегируем остальное
    others_sum = sum(val for _, val in sorted_cats[7:])
    if others_sum > 0:
        top_7["Остальное"] = others_sum
    return top_7


def search_transactions(transactions: list, query: str) -> list:
    """Поиск по подстроке, нечувствительный к регистру (ТЗ №9)."""
    query_lower = query.lower()
    results = []
    for t in transactions:
        if not isinstance(t, dict):
            continue
        desc = str(t.get("description", "")).lower()
        cat = str(t.get("category", "")).lower()
        if query_lower in desc or query_lower in cat:
            results.append(t)
    return results


def format_phone_number(text: str) -> str:
    """Шаблон маскирования разных форматов телефонов (ТЗ №10)."""
    digits = "".join(re.findall(r"\d", text))
    if len(digits) == 11:
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return text


def get_expenses_analytics(transactions: list) -> dict:
    """
    Группирует расходы по категориям, выделяя топ-7, переводы и наличные.

    Анализирует только успешные операции ('EXECUTED') с отрицательной суммой
    (расходы). Исключает 'Переводы' и 'Наличные' из общего списка, агрегируя
    их суммы в отдельные ключи. Из остальных категорий формирует топ-7 по
    убыванию трат, а все прочие расходы суммирует в категорию 'Остальное'.

    Args:
        transactions (list): Исходный список транзакций (словарей).

    Returns:
        dict: Словарь со следующей структурой:
              - 'categories' (dict): Топ-7 категорий и 'Остальное' с округленными суммами.
              - 'transfers' (int): Общая сумма расходов по категории 'Переводы'.
              - 'cash' (int): Общая сумма расходов по категории 'Наличные'.
    """
    categories = {}
    transfers_sum = 0
    cash_sum = 0

    for t in transactions:
        if not isinstance(t, dict) or t.get("state") != "EXECUTED":
            continue

        cat = t.get("category", "Остальное")
        amount = round(float(t.get("amount", 0)))

        if amount < 0:  # Считаем только расходы
            abs_amount = abs(amount)
            if cat == "Переводы":
                transfers_sum += abs_amount
            elif cat == "Наличные":
                cash_sum += abs_amount
            else:
                categories[cat] = categories.get(cat, 0) + abs_amount

    # Сортируем категории по убыванию и берем топ-7
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    top_7 = dict(sorted_cats[:7])

    # Считаем "Остальное"
    others_sum = sum(val for _, val in sorted_cats[7:])
    if others_sum > 0:
        top_7["Остальное"] = others_sum

    return {
        "categories": top_7,
        "transfers": transfers_sum,
        "cash": cash_sum
    }
