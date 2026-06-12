import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import requests
import urllib3

# === НАСТРОЙКА ЛОГИРОВАНИЯ В ФАЙЛ ПО СТАНДАРТУ PEP 8 ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Проверяем, чтобы обработчики не дублировались
if not logger.handlers:
    # Определяем путь к файлу логов в корне проекта (рядом с папкой src)
    log_file_path = Path(__file__).resolve().parent / ".." / "project.log"

    # Используем FileHandler для записи в файл вместо вывода в консоль
    handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="a")

    # Настраиваем единый формат вывода
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Подавление системных предупреждений о verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_json(file_path: str) -> Any:
    """Загружает и декодирует данные из файла в формате JSON.

    Args:
        file_path (str): Абсолютный или относительный путь к JSON-файлу.

    Returns:
        Any: Декодированные из JSON данные (обычно список или словарь).
             В случае ошибки возвращает пустой список.

    Raises:
        FileNotFoundError: Если файл отсутствует по указанному пути.
        Json.JSONDecodeError: Если файл содержит некорректный JSON-код.
    """
    logger.info(f"Попытка чтения JSON-файла по пути: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Файл {file_path} успешно прочитан.")
            return data
    except FileNotFoundError:
        logger.error(f"Файл не найден по пути: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования: файл {file_path} содержит некорректный JSON.")
        return []
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при чтении файла {file_path}: {e}")
        return []


def print_transactions(transactions: list[dict[str, Any]]) -> None:
    """Выводит список транзакций в консоль в читаемом формате.

    Извлекает дату (первые 10 символов), описание и сумму для каждой
    транзакции. Если данные отсутствуют, подставляет значения по умолчанию.

    Args:
        transactions (list[dict[str, Any]]): Список словарей, где каждый словарь
            представляет отдельную транзакцию и содержит ключи
            'date', 'description' и 'amount'.
    """
    for t in transactions:
        date: str = t.get("date", "Нет даты")[:10]
        description: str = t.get("description", "Без описания")
        amount: float | int = t.get("amount", 0)

        print(f"{date} {description}")
        print(f"Сумма: {amount}\n")


def read_transactions_json(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Читает транзакции из локального JSON-файла."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for value in data.values():
                    if isinstance(value, list):
                        return value
            return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def get_cbr_currency_rates() -> list:
    """Ультра-отказоустойчивый сбор курсов валют из СНГ и альтернативных API с маскировкой трафика."""
    fallback_rates = [{"currency": "USD", "rate": 89.45}, {"currency": "EUR", "rate": 96.12}]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # Источник №1: API Национального Банка Республики Беларусь (NBRB API)
    try:
        url_usd = "https://nbrb.by"
        url_eur = "https://nbrb.by"
        url_rub = "https://nbrb.by"

        timeout = 3
        res_usd = requests.get(url_usd, headers=headers, timeout=timeout, verify=False).json()
        res_eur = requests.get(url_eur, headers=headers, timeout=timeout, verify=False).json()
        res_rub = requests.get(url_rub, headers=headers, timeout=timeout, verify=False).json()

        rub_per_byn = float(res_rub["Cur_OfficialRate"]) / 100
        usd_rate = float(res_usd["Cur_OfficialRate"]) * rub_per_byn
        eur_rate = float(res_eur["Cur_OfficialRate"]) * rub_per_byn

        if usd_rate > 0 and eur_rate > 0:
            logger.info("Успешно получены курсы валют через NBRB API (Беларусь).")
            return [{"currency": "USD", "rate": round(usd_rate, 2)}, {"currency": "EUR", "rate": round(eur_rate, 2)}]

    except requests.RequestException as e:
        logger.warning(f"Сетевой сбой при обращении к NBRB API: {e}. Переходим к следующему шлюзу.")
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Ошибка обработки структуры данных NBRB API: {e}. Переходим к следующему шлюзу.")

    # Источник №2: Awesome Economy API
    try:
        url = "https://awesomeapi.com.br"
        response = requests.get(url, headers=headers, timeout=4, verify=False)
        if response.status_code == 200:
            data = response.json()
            usd_rate = float(data.get("USD RUB", {}).get("bid", 0))
            eur_rate = float(data.get("EUR RUB", {}).get("bid", 0))
            if usd_rate > 0 and eur_rate > 0:
                logger.info("Успешно получены курсы валют через Awesome API.")
                return [
                    {"currency": "USD", "rate": round(usd_rate, 2)},
                    {"currency": "EUR", "rate": round(eur_rate, 2)},
                ]
    except requests.RequestException as e:
        logger.warning(f"Сетевой сбой при обращении к Awesome API: {e}. Переходим к запасному шлюзу.")
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Ошибка парсинга данных Awesome API: {e}. Переходим к запасному шлюзу.")

    # Источник №3: Альтернативное CDN-зеркало exchangerate Host
    try:
        url = "https://exchangerate.host"
        response = requests.get(url, headers=headers, timeout=4, verify=False)
        if response.status_code == 200:
            quotes = response.json().get("quotes", {})
            rub_per_usd = float(quotes.get("USD RUB", 0))
            eur_per_usd = float(quotes.get("USD EUR", 0))

            if rub_per_usd > 0 and eur_per_usd > 0:
                logger.info("Успешно получены курсы валют через exchangerate Host.")
                return [
                    {"currency": "USD", "rate": round(rub_per_usd, 2)},
                    {"currency": "EUR", "rate": round(rub_per_usd / eur_per_usd, 2)},
                ]
    except requests.RequestException as e:
        logger.error(f"Все внешние API-шлюзы недоступны по причине сетевой ошибки: {e}.")
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Критическая ошибка структуры данных последнего шлюза: {e}.")

    # Если абсолютно всё упало — отдаем заглушку по ТЗ
    logger.info("Используются локальные резервные курсы валют (константы).")
    return fallback_rates


def sort_transactions_by_spent(transactions: list, reverse: bool = True) -> list:
    """Сортирует карты по сумме трат (total_spent)."""
    valid_data = [t for t in transactions if isinstance(t, dict) and "total_spent" in t]
    return sorted(valid_data, key=lambda x: x["total_spent"], reverse=reverse)


def filter_transactions_by_card(transactions: list, digits: str) -> list:
    """Ищет карты по последним цифрам (last_digits)."""
    filtered = []
    for t in transactions:
        if isinstance(t, dict) and "last_digits" in t:
            if str(t.get("last_digits")).strip() == digits.strip():
                filtered.append(t)
    return filtered


def load_transactions(file_path: str) -> list[dict[str, Any]]:
    """Загружает данные о транзакциях из JSON-файла.

    Args:
        file_path (str): Путь к файлу в формате JSON.

    Returns:
        list: Список словарей с данными транзакций.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_balance(transactions: list[dict]) -> None:
    """Подсчёт баланса"""
    if not transactions:
        print("\nНет данных.")
        return

    total: float = 0.0
    for tx in transactions:
        amount: float = tx.get("amount", 0.0)
        total += amount

    print(f"\nТекущий баланс: {round(total, 2)}")


def menu():
    print("\n========== МЕНЮ ==========")
    print("1. Загрузить транзакции")
    print("2. Показать транзакции")
    print("3. Показать баланс")
    print("4. Выход")
