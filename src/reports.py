import json
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, ParamSpec, TypeVar

import pandas as pd

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R", bound=list[dict[str, Any]])


def save_report(filename: Optional[str] = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор для сохранения JSON-отчета в файл.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            logger.info("Формирование отчёта: %s", func.__name__)

            result: R = func(*args, **kwargs)

            file_name: str = filename or f"{func.__name__}.json"

            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info("Отчёт сохранён в файл: %s", file_name)
            return result

        return wrapper

    return decorator


@save_report()
def spending_by_category(
    transactions: list[dict[str, Any]],
    category: str,
    date: str,
) -> str:
    """
    Формирует отчет трат по категории за дату.
    Возвращает JSON-строку.
    """

    logger.info("Формирование отчёта: spending_by_category")
    logger.info(
        "Отчёт трат по категории '%s', дата: %s",
        category,
        date,
    )

    if not transactions:
        return json.dumps([], ensure_ascii=False)

    df: pd.DataFrame = pd.DataFrame(transactions)

    df["Дата операции"] = pd.to_datetime(
        df["Дата операции"],
        errors="coerce",
        dayfirst=True,
    )

    target_date: datetime = pd.to_datetime(date)

    filtered = df[(df["Категория"] == category) & (df["Дата операции"].dt.date == target_date.date())]

    result = filtered.to_dict(orient="records")

    return json.dumps(result, ensure_ascii=False)
