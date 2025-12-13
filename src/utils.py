import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_URL = os.getenv("EXCHANGE_API_URL")
API_KEY = os.getenv("EXCHANGE_API_KEY")

if not API_URL or not API_KEY:
    logger.warning("API_URL или API_KEY не заданы в .env")


def get_greeting(dt: datetime) -> str:
    logger.debug("Определение приветствия по времени: %s", dt)

    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def get_month_period(date: datetime) -> Tuple[datetime, datetime]:
    """
    Возвращает период с начала месяца по указанную дату.
    """
    logger.debug("Расчет периода месяца для даты %s", date)

    start = date.replace(day=1, hour=0, minute=0, second=0)
    return start, date


def load_user_settings(path: str = "user_settings.json") -> Dict:
    """
    Загружает пользовательские настройки валют и акций.
    """
    logger.info("Загрузка пользовательских настроек: %s", path)

    if not os.path.exists(path):
        logger.warning("Файл user_settings.json не найден")
        return {"user_currencies": [], "user_stocks": []}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

        if not content:
            logger.error("Файл user_settings.json пустой")
            return {"user_currencies": [], "user_stocks": []}

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.exception("Ошибка парсинга user_settings.json")
            raise e


def cards_summary(df: pd.DataFrame) -> List[Dict]:
    """
    Агрегация расходов и кешбэка по картам.
    """
    logger.info("Формирование сводки по картам")

    grouped = df.groupby("Номер карты")["Сумма операции с округлением"].sum()

    result = [
        {
            "last_digits": str(card)[-4:],
            "total_spent": round(amount, 2),
            "cashback": round(abs(amount) * 0.01, 2),
        }
        for card, amount in grouped.items()
    ]

    logger.debug("Сформировано карт: %s", len(result))
    return result


def top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict]:
    """
    Топ транзакций по абсолютной сумме.
    """
    logger.info("Поиск топ-%s транзакций", limit)

    top_df = df.reindex(df["Сумма операции с округлением"].abs().sort_values(ascending=False).head(limit).index)

    return [
        {
            "date": row["Дата операции"].strftime("%d.%m.%Y"),
            "amount": round(row["Сумма операции с округлением"], 2),
            "category": row["Категория"],
            "description": row["Описание"],
        }
        for _, row in top_df.iterrows()
    ]


def get_currency_rates(currencies: list[str]) -> list[dict]:
    logger.info("Запрос курсов валют: %s", currencies)

    filtered = list(filter(lambda c: c != "USD", currencies))
    if not filtered:
        return []

    url = f"{API_URL}/live"

    params = {
        "base": "USD",
        "symbols": ",".join(filtered),
    }

    headers = {
        "apikey": API_KEY,
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10,
        )
        logger.debug("Currency API URL: %s", response.url)

        response.raise_for_status()
        data = response.json()

        rates = data.get("rates", {})

        result = list(
            map(
                lambda c: {
                    "currency": c,
                    "rate": round(rates[c], 2),
                },
                filter(lambda c: c in rates, filtered),
            )
        )

        logger.info("Курсы валют получены успешно")
        return result

    except requests.Timeout:
        logger.error("Таймаут при запросе курсов валют")
        return []

    except requests.RequestException as e:
        logger.error("Ошибка API курсов валют: %s", str(e))
        return []


def get_stock_prices(stocks: List[str]) -> List[Dict]:
    """
    Получение цен акций через stooq (бесплатный API).
    """
    logger.info("Запрос цен акций: %s", stocks)

    def fetch(stock: str):
        try:
            url = f"https://stooq.com/q/l/?s={stock.lower()}.us&i=d"
            r = requests.get(url, timeout=10)
            rows = r.text.splitlines()

            if len(rows) > 1:
                price = float(rows[1].split(",")[6])
                return {"stock": stock, "price": round(price, 2)}
        except Exception:
            logger.exception("Ошибка получения акции %s", stock)
        return None

    result = list(filter(None, map(fetch, stocks)))
    logger.debug("Получено акций: %s", len(result))
    return result
