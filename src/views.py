import logging
from datetime import datetime
from typing import Any

import pandas as pd

from src.utils import get_currency_rates, get_stock_prices

logger = logging.getLogger(__name__)


def main_page_view(
    date_time: str,
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:

    df = pd.DataFrame(transactions)

    """
    Формирует финансовый отчет для страницы «Главная».
    """

    logger.info("Формирование главной страницы за %s", date_time)

    try:
        report_dt: datetime = datetime.strptime(
            date_time,
            "%Y-%m-%d %H:%M:%S",
        )
    except ValueError as exc:
        raise ValueError("Неверный формат даты") from exc

    if not transactions:
        logger.warning("Список транзакций пуст")
        return {}

    df: pd.DataFrame = pd.DataFrame(transactions)

    df["Дата операции"] = pd.to_datetime(
        df["Дата операции"],
        format="%d.%m.%Y %H:%M:%S",
        errors="coerce",
    )

    # РАСХОДЫ
    expenses_df = df[df["Сумма операции"] < 0].copy()
    expenses_df["amount"] = expenses_df["Сумма операции"].abs()

    total_expenses: int = int(expenses_df["amount"].sum())

    grouped_expenses = expenses_df.groupby("Категория")["amount"].sum().sort_values(ascending=False)

    main_expenses: list[dict[str, Any]] = []
    transfers_and_cash: list[dict[str, Any]] = []

    for category, amount in grouped_expenses.items():
        item = {
            "category": str(category),
            "amount": int(amount),
        }

        if category in ("Наличные", "Переводы"):
            transfers_and_cash.append(item)
        else:
            main_expenses.append(item)

    # ДОХОДЫ
    income_df = df[df["Сумма операции"] > 0]
    total_income: int = int(income_df["Сумма операции"].sum())

    grouped_income = income_df.groupby("Категория")["Сумма операции"].sum().sort_values(ascending=False)

    income_main = [
        {
            "category": str(category),
            "amount": int(amount),
        }
        for category, amount in grouped_income.items()
    ]

    # КУРСЫ / АКЦИИ
    currency_rates = get_currency_rates(["USD", "EUR"])
    stock_prices = get_stock_prices(["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"])

    result = {
        "expenses": {
            "total_amount": total_expenses,
            "main": main_expenses,
            "transfers_and_cash": transfers_and_cash,
        },
        "income": {
            "total_amount": total_income,
            "main": income_main,
        },
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    logger.info("Главная страница успешно сформирована")
    return result
