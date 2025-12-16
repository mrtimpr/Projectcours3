import json
import os
from typing import Any

import pandas as pd

from src.reports import spending_by_category


def test_spending_by_category_basic(
    sample_transactions_df: pd.DataFrame,
) -> None:
    """
    Проверяет корректный JSON-результат отчёта
    «Траты по категории» за указанную дату.
    """

    result_json: str = spending_by_category(
        transactions=sample_transactions_df.to_dict(orient="records"),
        category="Супермаркеты",
        date="2021-12-31",
    )

    result: list[dict[str, Any]] = json.loads(result_json)

    assert isinstance(result, list)
    assert result == []


def test_spending_by_category_no_matches(
    sample_transactions_df: pd.DataFrame,
) -> None:
    """
    Проверяет, что при отсутствии операций
    возвращается пустой JSON-список.
    """

    result_json: str = spending_by_category(
        transactions=sample_transactions_df.to_dict(orient="records"),
        category="Транспорт",
        date="2021-12-31",
    )

    result = json.loads(result_json)

    assert isinstance(result, list)
    assert result == []


def test_spending_by_category_date_filter(
    sample_transactions_df: pd.DataFrame,
) -> None:
    """
    Проверяет фильтрацию строго по дате.
    """

    result_json: str = spending_by_category(
        transactions=sample_transactions_df.to_dict(orient="records"),
        category="ЖКХ",
        date="2022-03-15",
    )

    result = json.loads(result_json)

    assert isinstance(result, list)
    assert len(result) == 0


def test_spending_by_category_saves_json_file(
    sample_transactions_df: pd.DataFrame,
) -> None:
    """
    Проверяет, что декоратор сохраняет JSON-файл
    с корректным содержимым.
    """

    filename: str = "spending_by_category.json"

    result_json: str = spending_by_category(
        transactions=sample_transactions_df.to_dict(orient="records"),
        category="Супермаркеты",
        date="2021-12-31",
    )

    assert os.path.exists(filename)

    with open(filename, "r", encoding="utf-8") as f:
        file_content = json.load(f)  # ← это строка

    file_result = json.loads(file_content)
    result = json.loads(result_json)

    assert isinstance(file_result, list)
    assert file_result == result

    os.remove(filename)
