import json
import logging
import os
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

# ---------------------- ЛОГИРОВАНИЕ ----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------- ДЕКОРАТОР ----------------------
def report_to_file(filename: Optional[str] = None) -> Callable:
    """
    Декоратор для сохранения результата функции в JSON-файл.

    Если имя файла не задано, формируется автоматически на основе имени функции
    и текущего времени.

    Путь сохранения: ../data относительно текущего файла.

    Parameters
    ----------
    filename : Optional[str]
        Имя файла для сохранения (например, "report.json").
        Если None — имя генерируется автоматически.

    Returns
    -------
    Callable
        Декорированная функция, сохраняющая результат в файл.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # создаём папку data, если её нет
            data_dir = Path(__file__).resolve().parent.parent / "data"
            data_dir.mkdir(exist_ok=True)

            # имя файла
            if filename:
                file_name = filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{func.__name__}_{timestamp}.json"

            file_path = os.path.join(data_dir, file_name)

            # сохраняем
            try:
                if isinstance(result, pd.DataFrame):
                    data = result.to_dict(orient="records")
                else:
                    data = result

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                logger.info(f"Отчет сохранен в {file_path}")

            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {e}")

            return result

        return wrapper

    return decorator


# ---------------------- ПОДГОТОВКА ДАННЫХ ----------------------
def prepare_dataframe(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Подготавливает DataFrame с транзакциями к анализу.

    Выполняет:
    - преобразование столбца "Дата операции" в datetime
    - очистку и нормализацию столбца "Категория"
    - приведение "Сумма операции" к числовому типу

    Parameters
    ----------
    input_df : pd. DataFrame
        Исходный DataFrame с транзакциями.

    Returns
    -------
    pd. DataFrame
        Обработанный DataFrame.
    """

    # Имя переменной изменено на processed_df, чтобы не пересекаться с глобальным scope
    processed_df = input_df.copy()

    processed_df["Дата операции"] = pd.to_datetime(
        processed_df["Дата операции"],
        format="%d.%m.%Y %H:%M:%S",
        errors="coerce"
    )

    processed_df["Категория"] = (
        processed_df["Категория"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    processed_df["Сумма операции"] = pd.to_numeric(
        processed_df["Сумма операции"],
        errors="coerce"
    )

    return processed_df


# ---------------------- 1. ТРАТЫ ПО КАТЕГОРИИ ----------------------
@report_to_file()
def spending_by_category(
    transactions: pd.DataFrame,
    target_category: str,
    end_date_str: Optional[str] = None
) -> pd.Series:  # Исправлено: возвращается pd. Series или pd.DataFrame
    """
    Рассчитывает суммарные траты по заданной категории за последние 3 месяца.

    Parameters
    ----------
    transactions : pd. DataFrame с транзакциями.
    target_category : str
        Название категории (например, "супермаркеты").
    end_date_str : Optional[str]
        Конечная дата периода (в формате строки).
        Если None — используется текущая дата.

    Returns
    -------
    pd. DataFrame с суммой трат по категории.
    """

    processed_df = prepare_dataframe(transactions)

    # Имена переменных изменены, чтобы не перекрывать встроенный модуль 'date'
    parsed_end_date = pd.to_datetime(end_date_str, dayfirst=True) if end_date_str else pd.Timestamp.now()
    start_date = parsed_end_date - pd.DateOffset(months=3)

    clean_category = target_category.strip().lower()

    # Фильтрация по уникальным локальным переменным
    filtered_df = processed_df[
        (processed_df["Дата операции"] >= start_date)
        & (processed_df["Дата операции"] <= parsed_end_date)
        & (processed_df["Категория"] == clean_category)
    ]

    result = (
        filtered_df
        .groupby("Категория", as_index=False)["Сумма операции"]
        .sum()
    )
    return result


# ---------------------- 2. ТРАТЫ ПО ДНЯМ НЕДЕЛИ ----------------------
@report_to_file()
def spending_by_weekday(
    transactions: pd.DataFrame,
    end_date_str: Optional[str] = None
) -> pd.DataFrame:
    """
    Рассчитывает средние траты по дням недели за последние 3 месяца.

    Parameters
    ----------
    transactions : pd. DataFrame с транзакциями.
    end_date_str : Optional[str]
        Конечная дата периода.
        Если None — используется текущая дата.

    Returns
    -------
    pd. DataFrame
        Таблица со средними тратами по дням недели.
    """

    # Уникальное имя переменной processed_df вместо df, чтобы избежать shadows outer scope
    processed_df = prepare_dataframe(transactions)

    # Имя параметра end_date_str не перекрывает встроенный модуль date
    parsed_end_date = pd.to_datetime(end_date_str, dayfirst=True) if end_date_str else pd.Timestamp.now()
    start_date = parsed_end_date - pd.DateOffset(months=3)

    # Переименовано в filtered_df, чтобы исключить конфликты с внешними переменными
    filtered_df = processed_df[
        (processed_df["Дата операции"] >= start_date)
        & (processed_df["Дата операции"] <= parsed_end_date)
    ].copy()

    filtered_df["weekday"] = filtered_df["Дата операции"].dt.day_name()

    result = (
        filtered_df
        .groupby("weekday")["Сумма операции"]
        .mean()
        .reset_index(name="Средние траты")
    )

    return result


# ---------------------- 3. РАБОЧИЙ / ВЫХОДНОЙ ----------------------
@report_to_file()
def spending_by_workday(
    transactions: pd.DataFrame,
    end_date_str: Optional[str] = None
) -> pd.DataFrame:
    """
    Рассчитывает средние траты для рабочих и выходных дней за последние 3 месяца.

    Parameters
    ----------
    transactions : pd. DataFrame с транзакциями.
    end_date_str : Optional[str]
        Конечная дата периода.
        Если None — используется текущая дата.

    Returns
    -------
    pd. DataFrame
        Таблица со средними тратами:
        - Рабочий день
        - Выходной день
    """

    # Уникальное имя переменной processed_df вместо df
    processed_df = prepare_dataframe(transactions)

    # Имя параметра end_date_str не перекрывает встроенный модуль date
    parsed_end_date = pd.to_datetime(end_date_str, dayfirst=True) if end_date_str else pd.Timestamp.now()
    start_date = parsed_end_date - pd.DateOffset(months=3)

    # Переименовано в filtered_df для изоляции от внешних переменных
    filtered_df = processed_df[
        (processed_df["Дата операции"] >= start_date)
        & (processed_df["Дата операции"] <= parsed_end_date)
    ].copy()

    filtered_df["is_weekend"] = filtered_df["Дата операции"].dt.weekday >= 5

    filtered_df["Тип дня"] = filtered_df["is_weekend"].map({
        True: "Выходной",
        False: "Рабочий"
    })

    result = (
        filtered_df
        .groupby("Тип дня")["Сумма операции"]
        .mean()
        .reset_index(name="Средние траты")
    )

    return result


# ---------------------- ЗАПУСК ----------------------
if __name__ == "__main__":  # pragma: no cover
    """
    Точка входа для локального запуска скрипта.

    Загружает Excel-файл с транзакциями и выводит:
    - траты по категории
    - траты по дням недели
    - траты по типу дня
    """

    df = pd.read_excel(
        r"A:\Project_2\data\operations.xlsx",
        engine="openpyxl"
    )

    print(spending_by_category(df, "супермаркеты"))
    print(spending_by_weekday(df))
    print(spending_by_workday(df))
