import json
import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

CURRENCY_API_URL: str = os.getenv(
    "CURRENCY_API_URL",
    "https://api.frankfurter.app",
)

STOCK_API_URL: str = os.getenv(
    "STOCK_API_URL",
    "https://query1.finance.yahoo.com/v7/finance/quote",
)

HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "10"))

logger = logging.getLogger(__name__)


def get_greeting(dt: datetime) -> str:
    logger.debug("Определение приветствия по времени: %s", dt)

    hour: int = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def get_month_period(date: datetime) -> tuple[datetime, datetime]:
    """
    Возвращает период с начала месяца по указанную дату.
    """
    logger.debug("Расчет периода месяца для даты %s", date)

    start: datetime = date.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
    )
    return start, date


def load_user_settings(
    path: str = "user_settings.json",
) -> dict[str, list[str]]:
    """
    Загружает пользовательские настройки валют и акций.
    """
    logger.info("Загрузка пользовательских настроек: %s", path)

    if not os.path.exists(path):
        logger.warning("Файл user_settings.json не найден")
        return {"user_currencies": [], "user_stocks": []}

    with open(path, "r", encoding="utf-8") as f:
        content: str = f.read().strip()

    if not content:
        logger.error("Файл user_settings.json пустой")
        return {"user_currencies": [], "user_stocks": []}

    try:
        data: Any = json.loads(content)

        return {
            "user_currencies": list(map(str, data.get("user_currencies", []))),
            "user_stocks": list(map(str, data.get("user_stocks", []))),
        }

    except json.JSONDecodeError as exc:
        logger.exception("Ошибка парсинга user_settings.json")
        raise exc


def cards_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Агрегация расходов и кешбэка по картам.
    """
    logger.info("Формирование сводки по картам")

    grouped: pd.Series = df.groupby("Номер карты")["Сумма операции с округлением"].sum()

    result: list[dict[str, Any]] = []

    for card, amount in grouped.items():
        result.append(
            {
                "last_digits": str(card)[-4:],
                "total_spent": round(float(amount), 2),
                "cashback": round(abs(float(amount)) * 0.01, 2),
            }
        )

    return result


def top_transactions(
    df: pd.DataFrame,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Топ транзакций по абсолютной сумме.
    """
    logger.info("Поиск топ-%s транзакций", limit)

    sorted_index = df["Сумма операции с округлением"].abs().sort_values(ascending=False).head(limit).index

    top_df: pd.DataFrame = df.loc[sorted_index]

    result: list[dict[str, Any]] = []

    for _, row in top_df.iterrows():
        result.append(
            {
                "date": row["Дата операции"].strftime("%d.%m.%Y"),
                "amount": round(float(row["Сумма операции с округлением"]), 2),
                "category": str(row["Категория"]),
                "description": str(row["Описание"]),
            }
        )

    return result


def get_currency_rates(
    currencies: list[str],
) -> list[dict[str, Any]]:
    """
    Получает курсы валют через frankfurter.app
    (база — EUR)
    """
    if not currencies:
        logger.info("Список валют пуст — пропуск запроса")
        return []

    logger.info("Запрос курсов валют: %s", currencies)

    try:
        response = requests.get(
            f"{CURRENCY_API_URL}/latest",
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        rates: dict[str, Any] = data.get("rates", {})

        result: list[dict[str, Any]] = []

        for currency in currencies:
            if currency == "EUR":
                result.append({"currency": "EUR", "rate": 1.0})
            elif currency in rates:
                result.append(
                    {
                        "currency": currency,
                        "rate": round(float(rates[currency]), 2),
                    }
                )

        return result

    except requests.RequestException as exc:
        logger.warning(
            "Ошибка API курсов валют (%s). Возврат fallback-данных",
            exc,
        )

        fallback_rates: dict[str, float] = {
            "EUR": 1.0,
            "USD": 1.17,
            "GBP": 0.86,
        }

        return [{"currency": c, "rate": fallback_rates[c]} for c in currencies if c in fallback_rates]


def get_stock_prices(
    stocks: list[str],
) -> list[dict[str, Any]]:
    """
    Получение цен акций Yahoo Finance
    """
    if not stocks:
        logger.info("Список акций пуст — пропуск запроса")
        return []

    logger.info("Запрос цен акций: %s", stocks)

    headers: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://finance.yahoo.com/",
    }

    try:
        response = requests.get(
            STOCK_API_URL,
            params={"symbols": ",".join(stocks)},
            headers=headers,
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        quotes: list[dict[str, Any]] = data.get("quoteResponse", {}).get("result", [])

        result: list[dict[str, Any]] = []

        for q in quotes:
            price = q.get("regularMarketPrice")
            symbol = q.get("symbol")

            if price is None or symbol is None:
                continue

            result.append(
                {
                    "stock": str(symbol),
                    "price": round(float(price), 2),
                }
            )

        return result

    except requests.RequestException as exc:
        logger.warning(
            "Ошибка Yahoo Finance (%s). Возврат fallback-данных",
            exc,
        )

        return [
            {"stock": "AAPL", "price": 189.84},
            {"stock": "AMZN", "price": 154.21},
            {"stock": "GOOGL", "price": 141.73},
            {"stock": "MSFT", "price": 374.92},
            {"stock": "TSLA", "price": 238.45},
        ]
