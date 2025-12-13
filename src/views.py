import logging
from datetime import datetime

import pandas as pd

from src.utils import (cards_summary, get_currency_rates, get_greeting, get_month_period, get_stock_prices,
                       load_user_settings, top_transactions)

logger = logging.getLogger(__name__)


def main_page_view(date_time: str, transactions: pd.DataFrame) -> dict:
    """
    Формирует JSON-ответ для страницы «Главная».
    """
    logger.info("Формирование данных главной страницы")
    logger.debug("Входящая дата/время: %s", date_time)

    try:
        current_dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.exception("Некорректный формат даты: %s", date_time)
        raise ValueError(f"Некорректный формат даты: {date_time}")

    df = transactions.copy()

    logger.debug("Преобразование столбца 'Дата операции' в datetime")
    df["Дата операции"] = pd.to_datetime(
        df["Дата операции"],
        format="%d.%m.%Y %H:%M:%S",
    )

    start_date, end_date = get_month_period(current_dt)
    logger.info(
        "Период анализа: %s — %s",
        start_date.strftime("%d.%m.%Y"),
        end_date.strftime("%d.%m.%Y"),
    )

    df_period = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

    logger.info("Транзакций в периоде: %s", len(df_period))

    settings = load_user_settings()
    currencies = settings.get("user_currencies", [])
    stocks = settings.get("user_stocks", [])

    logger.debug(
        "Настройки пользователя — валюты: %s, акции: %s",
        currencies,
        stocks,
    )

    result = {
        "greeting": get_greeting(current_dt),
        "cards": cards_summary(df_period),
        "top_transactions": top_transactions(df_period),
        "currency_rates": get_currency_rates(currencies) if currencies else [],
        "stock_prices": get_stock_prices(stocks) if stocks else [],
    }

    logger.info("JSON для главной страницы сформирован")
    return result
