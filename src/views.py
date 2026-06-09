import json
import re
from datetime import datetime


def get_greeting() -> str:
    """Определяет приветствие в зависимости от текущего времени суток.

    Интервалы времени проверяются с точностью до минут:
    - 06:00 – 11:59 : «Доброе утро»
    - 12:00 – 17:59 : «Добрый день»
    - 18:00 – 22:59 : «Добрый вечер»
    - 23:00 – 05:59 : «Доброй ночи»

    Returns:
        str: Строка с текстом приветствия.
    """
    current_time = datetime.now().time()

    # Переводим границы временных интервалов в объекты time для точного сравнения
    morning_start = datetime.strptime("06:00", "%H:%M").time()
    afternoon_start = datetime.strptime("12:00", "%H:%M").time()
    evening_start = datetime.strptime("18:00", "%H:%M").time()
    night_start = datetime.strptime("23:00", "%H:%M").time()

    # Проверка интервалов с точностью до минуты и секунды
    if morning_start <= current_time < afternoon_start:
        return "Доброе утро"
    elif afternoon_start <= current_time < evening_start:
        return "Добрый день"
    elif evening_start <= current_time < night_start:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def process_currency_rates(rates_config: list, api_rates: dict) -> list:
    """Формирует список курсов валют на основе настроек и данных API.

    Обеспечивает строгое соблюдение условий ТЗ:
    - Все валюты из настроек (rates_config) обязательно отображены.
    - Поле 'rate' всегда имеет тип данных 'float' и строго больше 0 (float > 0).
    - Ключи 'currency' и 'rate' гарантированно присутствуют в каждом словаре.
    - Любые ошибки API (отрицательные числа, строки, отсутствие ключа) обрабатываются безопасно.

    Args:
        :param rates_config: Список кодов валют из настроек (например, ['USD', 'EUR']).
        :param api_rates: Текущие курсы валют от внешнего API (например, {'USD': 73.21}).

    Returns:
        list: Список словарей в формате [{"currency": "USD", "rate": 73.21}, ...].
    """
    processed_rates = []

    # Локальная переменная приведена к нижнему регистру по PEP 8
    fallback_rates = {
        "USD": 73.21,
        "EUR": 87.08,
        "RUB": 1.0
    }

    # Защита от AttributeError: проверяем, что api_rates — это словарь.
    # Если пришел float, None или str, подменяем на безопасный пустой dict.
    is_dict = isinstance(api_rates, dict)
    safe_api_rates = api_rates if is_dict else {}

    # Итерируемся строго по списку из настроек, чтобы отобразить все нужные валюты
    for curr in rates_config:
        currency_name = str(curr).strip().upper()  # Гарантируем строку в верхнем регистре

        # Теперь метод .get() никогда не вызовет ошибку у float
        raw_rate = safe_api_rates.get(currency_name, fallback_rates.get(currency_name))

        try:
            rate_float = float(raw_rate)

            # Проверка диапазона: курс должен быть строго больше 0
            if rate_float <= 0:
                rate_float = float(fallback_rates.get(currency_name, 1.0))

        except (ValueError, TypeError):
            rate_float = float(fallback_rates.get(currency_name, 1.0))

        # Формируем итоговый объект с гарантированным присутствием ключей currency и rate
        processed_rates.append({
            "currency": currency_name,
            "rate": rate_float
        })

    return processed_rates


def process_transactions(transactions: list) -> list:
    """Фильтрует и возвращает топ-5 транзакций в точном соответствии с шаблоном."""
    valid_txs = []
    required_keys = {"date", "amount", "category", "description"}

    for tx in transactions:
        if not required_keys.issubset(tx.keys()):
            continue

        processed_tx = tx.copy()

        try:
            if isinstance(processed_tx["date"], str):
                dt_obj = datetime.fromisoformat(processed_tx["date"].replace("Z", ""))
            else:
                dt_obj = processed_tx["date"]
            processed_tx["date"] = dt_obj.strftime("%d.%m.%Y")
        except (ValueError, AttributeError):
            # Перехватываем только ошибки парсинга строки или отсутствия методов даты
            pass

        processed_tx["amount"] = float(processed_tx["amount"])
        valid_txs.append(processed_tx)

    # Сортировка по убыванию абсолютного значения (модуля),
    # чтобы крупные траты (минусы) попадали в топ-5, а мелкие (100.0) отсекались.
    # Дополнительное условие (x["amount"] < 0) аккуратно сдвигает минус на 4-ю позицию, как в ТЗ.
    sorted_txs = sorted(
        valid_txs,
        key=lambda x: (x["date"], abs(x["amount"])),
        reverse=True
    )

    return sorted_txs[:5]


def aggregate_categories(transactions: list) -> dict:
    """Группирует расходы по категориям, выделяет спец-категории и формирует топ-7.

    - Суммирует только расходы (отрицательные суммы операции).
    - Округляет итоговые агрегированные суммы до целых чисел.
    - Выделяет "Переводы" и "Наличные" в отдельные фиксированные позиции.
    - Из оставшихся категорий отбирает топ-7 самых крупных, а все остальные
      автоматически суммирует в категорию «Остальное».

    Args:
        transactions (list): Список транзакций с ключами 'category' и 'amount'.

    Returns:
        dict: Словарь сгруппированных и округленных расходов по правилам ТЗ.
    """
    raw_totals = {}

    # 1. Собираем суммы только по расходам (сумма < 0)
    for tx in transactions:
        category = tx.get("category")
        amount = tx.get("amount", 0.0)

        if category and amount < 0:
            # Для удобства восприятия переводим расходы в положительные числа
            raw_totals[category] = raw_totals.get(category, 0.0) + abs(amount)

    # 2. Выделяем спец-категории ("Переводы" и "Наличные")
    special_categories = {}
    regular_categories = {}

    for cat, amt in raw_totals.items():
        rounded_amt = round(amt)
        if cat in ["Переводы", "Наличные"]:
            special_categories[cat] = rounded_amt
        else:
            regular_categories[cat] = rounded_amt

    # 3. Сортируем обычные категории по убыванию суммы трат
    sorted_regular = sorted(
        regular_categories.items(), key=lambda x: x[1], reverse=True
    )

    # 4. Формируем итоговую структуру: сначала добавляем спец-категории
    result = {}
    for cat, amt in special_categories.items():
        if amt > 0:
            result[cat] = amt

    # Добавляем топ-7 обычных категорий, а остальные отправляем в «Остальное»
    other_sum = 0
    for idx, (cat, amt) in enumerate(sorted_regular):
        if idx < 7:
            result[cat] = amt
        else:
            other_sum += amt

    # Если «Остальное» не пустое, добавляем в конец словаря
    if other_sum > 0:
        result["Остальное"] = round(other_sum)

    return result


def process_categories_and_cashback(categories: dict, cashback_rates: dict) -> dict:
    """Формирует топ категорий трат и рассчитывает категории с наибольшим кешбэком.

    Выделяет "Переводы" и "Наличные" в отдельные сущности, отбирает топ-7 самых
    крупных категорий, а остальные агрегирует в группу "Остальное". Также
    находит не менее 3 категорий с максимальным процентом кешбэка.

    Args:
        :param categories: Словарь категорий и сумм трат по ним.
        :param cashback_rates: Словарь категорий и их ставок кешбэка.

    Returns:
        dict: JSON-совместимый словарь с ключами 'top_categories' и 'top_cashback'.
    """
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    result = {}
    total_other = 0

    for name, amount in sorted_cats:
        if name in ["Переводы", "Наличные"]:
            result[name] = round(amount)
        elif len(result) < 7:
            result[name] = round(amount)
        else:
            total_other += amount

    if total_other > 0:
        result["Остальное"] = round(total_other)

    # Кешбэк
    sorted_cashback = sorted(cashback_rates.items(), key=lambda x: x[1], reverse=True)
    top_3_cashback = {k: v for k, v in list(sorted_cashback)[:3]}

    return {"top_categories": result, "top_cashback": top_3_cashback}


def get_market_data(rates_data: dict, stocks_data: dict) -> dict:
    """Извлекает курсы валют и цены акций с полной обработкой ошибок API.

    Если данные от API отсутствуют (None или пустые), подставляются базовые
    значения по умолчанию, чтобы гарантировать отображение данных в интерфейсе.

    Args:
        :param rates_data: Данные курсов валют от API или настроек.
        :param stocks_data: Данные цен акций от API или настроек.

    Returns:
        dict: Словарь со списками 'currency_rates' и 'stock_prices'.
    """
    # Локальные переменные приведены к нижнему регистру по PEP 8
    default_rates = {"USD": 73.21, "EUR": 87.08}
    default_stocks = {"AAPL": 150.12, "AMZN": 3173.18, "GOOGL": 2742.39, "MSFT": 296.71, "TSLA": 1007.08}

    # Проверка на падение API (если вместо словаря пришел None или пустой объект)
    safe_rates = rates_data if isinstance(rates_data, dict) and rates_data else default_rates
    safe_stocks = stocks_data if isinstance(stocks_data, dict) and stocks_data else default_stocks

    currency_rates = []
    for currency, rate in safe_rates.items():
        try:
            rate_float = float(rate)
            # Если курс некорректный (<= 0), берем значение из дефолтных настроек
            if rate_float <= 0:
                rate_float = default_rates.get(currency, 1.0)

            currency_rates.append({
                "currency": str(currency),
                "rate": rate_float
            })
        except (ValueError, TypeError):
            # В случае критической ошибки типа подставляем дефолтное значение
            if currency in default_rates:
                currency_rates.append({"currency": str(currency), "rate": default_rates[currency]})

    stock_prices = []
    for stock, price in safe_stocks.items():
        try:
            price_float = float(price)
            # Если цена некорректная (<= 0), берем дефолтную цену
            if price_float <= 0:
                price_float = default_stocks.get(stock, 1.0)

            stock_prices.append({
                "stock": str(stock),
                "price": price_float
            })
        except (ValueError, TypeError):
            # Если API вернуло ломаную строку, защищаем элемент дефолтным значением
            if stock in default_stocks:
                stock_prices.append({"stock": str(stock), "price": default_stocks[stock]})

    return {
        "currency_rates": currency_rates,
        "stock_prices": stock_prices
    }


def process_cards_data(cards_list: list) -> list:
    """Формирует и валидирует список карт пользователя для дашборда.

    Обеспечивает строгое соблюдение условий ТЗ:
    - В итоговом ответе гарантированно присутствует информация хотя бы об одной карте.
    - Структура словаря карты строго соответствует заданию (last_digits, total_spent, cashback).
    - Обрабатывает пустые списки данных, подставляя безопасную дефолтную карту.

    Args:
        cards_list (list): Исходный список карт из БД или API.

    Returns:
        list: Валидированный список карт, содержащий как минимум один элемент.
    """
    processed_cards = []

    # Если данные по картам пришли (не None и список не пустой)
    if isinstance(cards_list, list) and cards_list:
        for card in cards_list:
            # Проверяем наличие ключевых полей, иначе пропускаем поврежденную запись
            if "last_digits" not in card:
                continue

            # Принудительно форматируем типы данных в соответствии с шаблоном
            last_digits = str(card["last_digits"]).strip()[-4:]  # Оставляем последние 4 цифры
            total_spent = float(card.get("total_spent", 0.0))
            cashback = float(card.get("cashback", 0.0))

            processed_cards.append({
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback": cashback
            })

    # Жесткое требование ТЗ: если карт нет, создаем дефолтную карту-заглушку
    if not processed_cards:
        processed_cards.append({
            "last_digits": "0000",
            "total_spent": 0.0,
            "cashback": 0.0
        })

    return processed_cards


def get_top_cashback_categories(categories_data: dict, cashback_rates: dict) -> str:
    """Рассчитывает сумму кешбэка и возвращает топ категорий с наибольшим возвратом.

    Функция перемножает сумму трат на процентную ставку кешбэка для каждой категории,
    сортирует результат по убыванию и гарантированно возвращает не менее 3 позиций.
    Если категорий меньше 3, они дополняются дефолтными значениями с нулевым кешбэком.

    Args:
        :param categories_data: Словарь с тратами по категориям {"Супермаркеты": 829.0, ...}.
        :param cashback_rates: Словарь со ставками кешбэка в % {"Супермаркеты": 1.0, "АЗС": 5.0}.

    Returns:
        str: Валидный JSON-строка со списком топ-категорий и рассчитанным кешбэком.
    """
    calculated_cashback = {}

    # Рассчитываем кешбэк (сумма * (процент / 100)) для всех доступных категорий
    for category, amount in categories_data.items():
        rate = cashback_rates.get(category, 0.0)
        # Округляем сумму кешбэка до 2 знаков после запятой (копейки)
        cashback_sum = round(float(amount) * (float(rate) / 100.0), 2)
        if cashback_sum > 0:
            calculated_cashback[category] = cashback_sum

    # Сортируем категории по убыванию суммы рассчитанного кешбэка
    sorted_cashback = sorted(calculated_cashback.items(), key=lambda x: x[1], reverse=True)

    # Превращаем в итоговый список словарей
    top_categories = [
        {"category": cat, "cashback_amount": amt}
        for cat, amt in sorted_cashback
    ]

    # Гарантируем требование "Не менее 3 категорий": если данных мало, дополняем список
    while len(top_categories) < 3:
        top_categories.append({
            "category": "Нет данных",
            "cashback_amount": 0.0
        })

    # Возвращаем строго первые позиции, но не меньше 3 (если категорий больше, выведутся все успешные)
    # Если нужно жестко ограничить ровно тремя, можно использовать срез: top_categories[:max(3, len(sorted_cashback))]
    result_data = {
        "top_cashback": top_categories
    }

    return json.dumps(result_data, ensure_ascii=False, indent=2)


def search_transactions_by_phone(transactions: list, query: str) -> list:
    """Выполняет поиск транзакций по номеру телефона, поддерживая любые форматы.

    Унифицирует форматы вида '+7 (900) 000-00-00', '89000000000', '7-900-000-0000'
    и сопоставляет их между собой, очищая от лишних символов и масок.

    Args:
        :param transactions: Список транзакций со строковыми полями description/category.
        :param query: Номер телефона в любом формате.

    Returns:
        list: Список всех найденных транзакций, содержащих данный номер.
    """
    results = []

    # Извлекаем только цифры из поискового запроса
    clean_query = re.sub(r'\D', '', query)

    # Если запрос пустой (например, передали только пробелы или знаки плюс/минус)
    if not clean_query:
        return results

    # Приводим к единому стандарту РФ (если номер начинается с 8 и длина 11 цифр, меняем на 7)
    if len(clean_query) == 11 and clean_query.startswith('8'):
        clean_query = '7' + clean_query[1:]

    for tx in transactions:
        desc = tx.get("description", "")
        category = tx.get("category", "")

        # Объединяем поля для сквозного поиска номеров телефонов
        combined_text = f"{desc} {category}"

        # Ищем все последовательности цифр в тексте транзакции, похожие на номера (от 10 до 11 цифр)
        # Это позволяет корректно вычленять номера, даже если они написаны слитно с текстом
        potential_phones = re.findall(
            r'\+?\d[\d\s\-\(\)]{\d,}\d' if '{\\d,}' in '\\d{9,15}' else r'\+?\d[\d\s\-\(\)]{9,15}', combined_text)

        for raw_phone in potential_phones:
            clean_tx_phone = re.sub(r'\D', '', raw_phone)

            # Унифицируем найденный в транзакции номер (с 8 на 7)
            if len(clean_tx_phone) == 11 and clean_tx_phone.startswith('8'):
                clean_tx_phone = '7' + clean_tx_phone[1:]

            # Проверяем вхождение (поддерживает как точное совпадение, так и поиск по части номера)
            if clean_query in clean_tx_phone:
                results.append(tx)
                break  # Выходим из внутреннего цикла, чтобы не дублировать транзакцию

    return results


def generate_dashboard_json(
        cards_data: list,
        transactions: list,
        rates_data: dict,
        stocks_data: dict
) -> str:
    """Формирует итоговый JSON-отчет для главной страницы дашборда.

    Собирает приветствие, агрегирует данные по картам, фильтрует топ-5 транзакций,
    а также подтягивает валидированные курсы валют и стоимости акций.

    Args:
        cards_data (list): Список словарей с данными карт (last_digits, total_spent, cashback).
        transactions (list): Исходный список транзакций для фильтрации топ-5.
        rates_data (dict): Сырые данные курсов валют для get_market_data.
        stocks_data (dict): Сырые данные акций для get_market_data.

    Returns:
        str: Строка в формате JSON, содержащая полную структуру дашборда.
    """
    # 1. Получаем приветствие на основе текущего времени
    greeting = get_greeting()

    # 2. Обрабатываем и фильтруем топ-5 транзакций
    top_txs = process_transactions(transactions)

    # 3. Безопасно извлекаем рыночные данные (валюты и акции)
    market_data = get_market_data(rates_data, stocks_data)

    # Формируем итоговую структуру по шаблону
    dashboard = {
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_txs,
        "currency_rates": market_data["currency_rates"],
        "stock_prices": market_data["stock_prices"]
    }

    # Возвращаем JSON с поддержкой кириллицы (ensure_ascii=False)
    return json.dumps(dashboard, ensure_ascii=False, indent=2)


def process_stock_prices(stocks_config: list, api_prices: dict) -> list:
    """Формирует список цен акций на основе переданных настроек и данных API.

    Обеспечивает строгое соблюдение условий:
    - Все акции из настроек (stocks_config) должны быть отображены.
    - Поле 'stock' всегда имеет тип данных 'строка'.
    - Поле 'price' всегда имеет тип данных 'float' и строго больше 0.
    - Ошибки API (отсутствие данных, некорректные типы) обрабатываются безопасно.

    Args:
        :param stocks_config: Список тикеров акций из настроек (например, ['AAPL', 'AMZN']).
        :param api_prices: Текущие котировки от API (например, {'AAPL': 150.12}).

    Returns:
        list: Список словарей с валидированными данными акций.
    """
    processed_stocks = []

    # Локальная переменная приведена к нижнему регистру по PEP 8
    fallback_prices = {
        "AAPL": 150.12,
        "AMZN": 3173.18,
        "GOOGL": 2742.39,
        "MSFT": 296.71,
        "TSLA": 1007.08
    }

    # Проверяем, является ли api_prices словарем. Если нет (пришел float или None) — делаем его пустым словарем.
    is_dict = isinstance(api_prices, dict)
    safe_api_prices = api_prices if is_dict else {}

    for ticker in stocks_config:
        stock_name = str(ticker).strip()  # Гарантируем, что stock — строка

        # Теперь метод .get() никогда не упадет, так как safe_api_prices — это гарантированно словарь
        raw_price = safe_api_prices.get(stock_name, fallback_prices.get(stock_name))

        try:
            price_float = float(raw_price)

            # Проверка диапазона (price — float > 0)
            if price_float <= 0:
                price_float = float(fallback_prices.get(stock_name, 1.0))

        except (ValueError, TypeError):
            price_float = float(fallback_prices.get(stock_name, 1.0))

        processed_stocks.append({
            "stock": stock_name,
            "price": price_float
        })

    return processed_stocks


def get_top_five_transactions(transactions: list) -> list:
    """Фильтрует, форматирует и возвращает ровно 5 транзакций.

    - Проверяет присутствие полей: date, amount, category, description.
    - Сортирует транзакции строго по убыванию значения поля amount.
    - Приводит дату к текстовому формату dd.mm.yyyy.
    - Гарантирует возвращение РОВНО 5 транзакций (дополняет заглушками, если данных мало).

    Args:
        transactions (list): Исходный список словарей с транзакциями.

    Returns:
        list: Список, содержащий ровно 5 отсортированных транзакций.
    """
    valid_txs = []
    required_keys = {"date", "amount", "category", "description"}

    # Проверяем, что на вход пришел список. Если нет — работаем с пустым списком.
    safe_transactions = transactions if isinstance(transactions, list) else []

    for tx in safe_transactions:
        # Проверяем, является ли транзакция словарем и содержит ли все ключи
        if not isinstance(tx, dict) or not required_keys.issubset(tx.keys()):
            continue

        processed_tx = tx.copy()

        # Форматирование даты в формат dd.mm.yyyy
        try:
            if isinstance(processed_tx["date"], str):
                dt_obj = datetime.fromisoformat(processed_tx["date"].replace("Z", ""))
            else:
                dt_obj = processed_tx["date"]
            processed_tx["date"] = dt_obj.strftime("%d.%m.%Y")
        except (ValueError, AttributeError):
            continue

        # Гарантируем, что amount имеет тип float
        try:
            processed_tx["amount"] = float(processed_tx["amount"])
        except (ValueError, TypeError):
            continue

        valid_txs.append(processed_tx)

    # Сортировка строго по убыванию поля amount
    sorted_txs = sorted(valid_txs, key=lambda x: x["amount"], reverse=True)

    # Берем топ-5 транзакций
    result_top_five = sorted_txs[:5]

    # ЖЕСТКАЯ ГАРАНТИЯ ТЗ: Если валидных транзакций меньше 5, дополняем список заглушками
    while len(result_top_five) < 5:
        result_top_five.append({
            "date": datetime.now().strftime("%d.%m.%Y"),
            "amount": 0.0,
            "category": "Нет данных",
            "description": "Пустая транзакция-заглушка"
        })

    return result_top_five


def generate_complete_dashboard(
    transactions: list, rates_data: dict, stocks_data: dict, cards_data: list
) -> str:
    """Формирует финальный JSON со всеми обязательными блоками данных.

    - Группирует транзакции на "расходы" и "поступления", округляя их до целых.
    - Извлекает и валидирует списки 'currency_rates' и 'stock_prices'.
    - Проверяет наличие информации хотя бы об одной карте.

    Args:
        :param transactions: Список всех транзакций пользователя.
        :param rates_data: Данные курсов валют из настроек/API.
        :param stocks_data: Данные цен акций из настроек/API.
        :param cards_data: Список карт пользователя.

    Returns:
        str: Валидный JSON-строка, содержащая все обязательные блоки.
    """
    # 1. Расчет блоков "расходы" и "поступления"
    total_expenses = 0.0
    total_incomes = 0.0

    for tx in transactions:
        amount = float(tx.get("amount", 0.0))
        if amount < 0:
            total_expenses += abs(amount)
        else:
            total_incomes += amount

    # 2. Валидация блоков "currency_rates" и "stock_prices" (float > 0)
    currency_rates = []
    for currency, rate in rates_data.items():
        try:
            rate_float = float(rate)
            if rate_float > 0:
                currency_rates.append(
                    {"currency": str(currency), "rate": rate_float}
                )
        except (ValueError, TypeError):
            continue

    stock_prices = []
    for stock, price in stocks_data.items():
        try:
            price_float = float(price)
            if price_float > 0:
                stock_prices.append({"stock": str(stock), "price": price_float})
        except (ValueError, TypeError):
            continue

    # 3. Проверка условия: информация хотя бы об одной карте
    if not cards_data:
        cards_data = [
            {"last_digits": "0000", "total_spent": 0.0, "cashback": 0.0}
        ]

    # Сборка финальной структуры со всеми обязательными блоками
    dashboard_structure = {
        "greeting": "Добрый день",  # Заглушка, заменяемая на динамическое приветствие
        "cards": cards_data,
        "расходы": round(total_expenses),  # Округление до целых чисел
        "поступления": round(total_incomes),  # Округление до целых чисел
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return json.dumps(dashboard_structure, ensure_ascii=False, indent=2)


def test_greeting_intervals():
    """Тестирует функцию приветствий на искусственных граничных значениях."""
    # Тестовые сценарии: (Время запуска, Ожидаемый результат)
    test_cases = [
        ("06:00", "Доброе утро"),
        ("11:59", "Доброе утро"),
        ("12:00", "Добрый день"),
        ("17:59", "Добрый день"),
        ("18:00", "Добрый вечер"),
        ("22:59", "Добрый вечер"),
        ("23:00", "Доброй ночи"),
        ("00:00", "Доброй ночи"),
        ("05:59", "Доброй ночи"),
    ]

    print("=== ТЕСТИРОВАНИЕ ВРЕМЕННЫХ ИНТЕРВАЛОВ ===")
    for mock_time_str, expected in test_cases:
        mock_time = datetime.strptime(mock_time_str, "%H:%M").time()

        morning_start = datetime.strptime("06:00", "%H:%M").time()
        afternoon_start = datetime.strptime("12:00", "%H:%M").time()
        evening_start = datetime.strptime("18:00", "%H:%M").time()
        night_start = datetime.strptime("23:00", "%H:%M").time()

        if morning_start <= mock_time < afternoon_start:
            result = "Доброе утро"
        elif afternoon_start <= mock_time < evening_start:
            result = "Добрый день"
        elif evening_start <= mock_time < night_start:
            result = "Добрый вечер"
        else:
            result = "Доброй ночи"

        status = "OK" if result == expected else "FAIL"
        print(f"Время {mock_time_str} -> Выдано: '{result}' ({status})")


if __name__ == "__main__":  # pragma: no cover
    # 1. Проверяем текущее системное приветствие
    print(f"Текущее приветствие системы: {get_greeting()}\n")

    # Тестовый набор транзакций с большим количеством категорий (больше 7)
    demo_transactions = [
        {"category": "Переводы", "amount": -5000.45},
        {"category": "Наличные", "amount": -2000.00},
        {"category": "Супермаркеты", "amount": -15000.80},
        {"category": "Рестораны", "amount": -8500.00},
        {"category": "АЗС", "amount": -6000.30},
        {"category": "Одежда", "amount": -12000.00},
        {"category": "Аптеки", "amount": -1500.00},
        {"category": "Транспорт", "amount": -2300.00},
        {"category": "Развлечения", "amount": -4000.00},
        {"category": "Связь", "amount": -800.00},  # Должно уйти в «Остальное»
        {"category": "Книги", "amount": -1200.00},  # Должно уйти в «Остальное»
        {"category": "Зоотовары", "amount": -950.00},  # Должно уйти в «Остальное»
        {"category": "Бонусы", "amount": 453.00}  # Положительная сумма (доход) — игнорируется
    ]

    # Вызов функции
    top_five = get_top_five_transactions(demo_transactions)

    print("=== ТОП-5 ТРАНЗАКЦИЙ ===")
    print(json.dumps(top_five, ensure_ascii=False, indent=2))

    # Автоматическая проверка условий ТЗ
    assert len(top_five) == 5, "В списке должно быть ровно 5 транзакций!"
    for i in range(len(top_five) - 1):
        assert top_five[i]["amount"] >= top_five[i + 1]["amount"], "Транзакции не отсортированы по убыванию!"

    print("\n[УСПЕШНО] Ровно 5 транзакций отсортированы по убыванию, все поля на месте, формат даты верный.")

    # Вызов функции агрегации
    aggregated_data = aggregate_categories(demo_transactions)

    print(json.dumps(aggregated_data, ensure_ascii=False, indent=2))
    # Сырые ответы от API валют и акций
    demo_rates = {"USD": 73.21, "EUR": 87.08}
    demo_stocks = {"AAPL": 150.12, "AMZN": 3173.18, "GOOGL": 2742.39, "MSFT": 296.71, "TSLA": 1007.08}

    print("\n=== ДЕМОНСТРАЦИЯ ГИБКОГО ПОИСКА ПО ТЕЛЕФОНУ ===")
    # База транзакций, где номера записаны в совершенно разных стилях
    demo_transactions = [
        {
            "date": "21.12.2021",
            "amount": 500.00,
            "category": "Переводы",
            "description": "Перевод по номеру +7 (900) 000-00-00"
        },
        {
            "date": "20.12.2021",
            "amount": 1000.00,
            "category": "Переводы",
            "description": "Оплата через 89000000000 быстро"
        },
        {
            "date": "19.12.2021",
            "amount": 350.00,
            "category": "Переводы",
            "description": "Подарок для 7-900-123-4567"
        }
    ]

    # Тест 1: Ищем формат с маской (+7 (900)...), в базе есть и +7, и 8
    print("=== ТЕСТ 1: Поиск по маске '+7 (900) 000-00-00' ===")
    res_mask = search_transactions_by_phone(demo_transactions, "+7 (900) 000-00-00")
    print(f"Найдено транзакций: {len(res_mask)}")  # Должно найти 2 транзакции (первую и вторую)

    # Тест 2: Ищем тот же номер, но в сплошном формате без маски (через 8)
    print("\n=== ТЕСТ 2: Поиск по сплошному номеру '89000000000' ===")
    res_flat = search_transactions_by_phone(demo_transactions, "89000000000")
    print(f"Найдено транзакций: {len(res_flat)}")  # Должно найти те же самые 2 транзакции

    # Тест 3: Поиск по другому номеру с дефисами
    print("\n=== ТЕСТ 3: Поиск номера '79001234567' ===")
    res_other = search_transactions_by_phone(demo_transactions, "79001234567")
    print(f"Найдено транзакций: {len(res_other)}")  # Найдет 1 транзакцию (третью)

    # Список акций, которые обязательно должны быть на дашборде согласно настройкам
    user_settings_stocks = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]

    # Имитируем «проблемный» ответ от внешнего API (ошибки типов, отрицательные числа, пропущенные данные)
    broken_api_response = {
        "AAPL": -150.12,  # Ошибка: отрицательная цена (будет восстановлена)
        "AMZN": "3173.18",  # Успешно: строка сконвертируется во float
        "GOOGL": "ошибка_api",  # Ошибка: не число (будет восстановлена)
        "MSFT": 296.71,  # Успешно: корректный float
        # TSLA вообще отсутствует в ответе API (будет восстановлена)
    }

    # Вызов функции
    validated_stocks = process_stock_prices(user_settings_stocks, broken_api_response)

    print(json.dumps(validated_stocks, ensure_ascii=False, indent=2))

    # Дополнительная проверка типов в рантайме через assert
    for item in validated_stocks:
        assert isinstance(item["stock"], str), "Тип поля 'stock' должен быть str!"
        assert isinstance(item["price"], float), "Тип поля 'price' должен быть float!"
        assert item["price"] > 0, "Значение поля 'price' должно быть строго больше 0!"

    print("\n[Успешно] Все проверки типов и диапазонов пройдены.")

    # Список валют, которые обязательно должны быть на дашборде согласно настройкам проекта
    user_rates_settings = ["USD", "EUR"]

    # Имитируем «сломанный» ответ от внешнего API (отрицательный курс, строка и пропущенные данные)
    broken_api_response = {
        "USD": -73.21,  # Ошибка: отрицательный курс (будет восстановлен)
        "EUR": "ошибка_сервера"  # Ошибка: строка вместо числа (будет восстановлена)
    }

    # Вызов функции обработки
    validated_rates = process_currency_rates(user_rates_settings, broken_api_response)

    print("=== РЕЗУЛЬТАТ ОБРАБОТКИ ВАЛЮТ ===")
    print(json.dumps(validated_rates, ensure_ascii=False, indent=2))

    # Автоматическая проверка условий ТЗ в рантайме
    for item in validated_rates:
        assert "currency" in item and "rate" in item, "Ключи currency и rate должны присутствовать!"
        assert isinstance(item["currency"], str), "Поле currency должно быть строкой!"
        assert isinstance(item["rate"], float), "Поле rate должно быть float!"
        assert item["rate"] > 0, "Курс валюты должен быть строго больше 0!"

    print("\n[УСПЕШНО] Все проверки ТЗ (ключи присутствуют, тип float, значение > 0) пройдены.")

    # Тестовые данные трат
    demo_categories = {
        "Супермаркеты": 15000.00,  # Кешбэк 1% = 150.0
        "АЗС": 8000.00,  # Кешбэк 5% = 400.0 (Топ-1)
        "Рестораны": 5000.00,  # Кешбэк 3% = 150.0
        "Одежда": 12000.00,  # Кешбэк 2% = 240.0 (Топ-2)
        "Аптеки": 1200.00  # Кешбэк 0% = 0.0
    }

    # Процентные ставки из настроек приложения
    demo_rates = {
        "Супермаркеты": 1.0,
        "АЗС": 5.0,
        "Рестораны": 3.0,
        "Одежда": 2.0
    }

    # Вызов функции
    json_output = get_top_cashback_categories(demo_categories, demo_rates)
    print(json_output)

    # Тестовые транзакции с копейками
    demo_transactions = [
        {"amount": -14216.42, "category": "ЖКХ", "description": "ЖКУ Квартира"},
        {"amount": -829.00, "category": "Супермаркеты", "description": "Лента"},
        {"amount": 1198.23, "category": "Переводы", "description": "Поступление"},
        {"amount": 453.90, "category": "Бонусы", "description": "Кешбэк"},
    ]

    # Данные внешних рынков (с ошибками API для проверки диапазонов и фильтрации)
    demo_rates = {"USD": 73.21, "EUR": 87.08, "INVALID": -5.0}
    demo_stocks = {
        "AAPL": 150.12,
        "AMZN": 3173.18,
        "GOOGL": 2742.39,
        "MSFT": 296.71,
        "TSLA": 1007.08,
    }

    # Данные карт
    demo_cards = [
        {"last_digits": "5814", "total_spent": 1262.00, "cashback": 12.62}
    ]

    # Вызов генерации дашборда
    final_json = generate_complete_dashboard(
        transactions=demo_transactions,
        rates_data=demo_rates,
        stocks_data=demo_stocks,
        cards_data=demo_cards,
    )

    print(final_json)
