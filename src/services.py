import json
import logging
import re
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


# Выгодные категории повышенного кешбэка
def cashback_by_category(
    transactions: list[dict[str, Any]],
    year: int,
    month: int,
) -> str:
    """
    Анализирует фактический кешбэк по категориям
    за указанный месяц.
    Возвращает JSON-строку согласно ТЗ.
    """

    logger.info(
        "Анализ кешбэка по категориям за %04d-%02d",
        year,
        month,
    )

    if not transactions:
        logger.warning("Список транзакций пуст")
        return json.dumps({}, ensure_ascii=False)

    df: pd.DataFrame = pd.DataFrame(transactions)

    df["Дата операции"] = df["Дата операции"].apply(lambda x: datetime.strptime(x, "%d.%m.%Y %H:%M:%S"))

    filtered: pd.DataFrame = df[
        (df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month) & (df["Кэшбэк"] > 0)
    ]

    if filtered.empty:
        logger.warning("Нет данных для анализа кешбэка")
        return json.dumps({}, ensure_ascii=False)

    result: dict[str, float] = filtered.groupby("Категория")["Кэшбэк"].sum().round(2).to_dict()

    logger.info("Проанализировано категорий: %d", len(result))
    return json.dumps(result, ensure_ascii=False)


# Простой поиск
def search_transactions(
    transactions: list[dict[str, Any]],
    query: str,
) -> str:
    """
    Поиск по описанию и категории.
    Возвращает JSON-строку.
    """

    logger.info("Поиск транзакций по запросу: %s", query)

    query_lower: str = query.lower()

    result: list[dict[str, Any]] = []

    for item in transactions:
        description: str = str(item.get("Описание", "")).lower()
        category: str = str(item.get("Категория", "")).lower()

        if query_lower in description or query_lower in category:
            result.append(item)

    logger.info("Найдено транзакций: %d", len(result))
    return json.dumps(result, ensure_ascii=False)


# Поиск по телефонным номерам
def search_phone_numbers(
    transactions: list[dict[str, Any]],
    phone: str,
) -> str:
    """
    Возвращает транзакции,
    содержащие указанный номер телефона
    (или его часть) в описании.
    Возвращает JSON-строку.
    """

    logger.info("Поиск транзакций по номеру телефона: %s", phone)

    user_digits: str = re.sub(r"\D", "", phone)

    if not user_digits:
        logger.warning("Пустой номер телефона")
        return json.dumps([], ensure_ascii=False)

    result: list[dict[str, Any]] = []

    for item in transactions:
        description: str = str(item.get("Описание", ""))
        digits_in_text: str = re.sub(r"\D", "", description)

        if user_digits in digits_in_text:
            result.append(item)

    logger.info("Найдено транзакций: %d", len(result))
    return json.dumps(result, ensure_ascii=False)
