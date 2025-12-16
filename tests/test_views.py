from typing import Any

import pandas as pd
import pytest

from src.views import main_page_view


def test_main_page_view_basic(
    sample_transactions_df: pd.DataFrame,
    monkeypatch,
) -> None:
    """
    Базовая проверка структуры JSON для главной страницы.
    """

    monkeypatch.setattr(
        "src.views.get_currency_rates",
        lambda _: [{"currency": "USD", "rate": 90}],
    )
    monkeypatch.setattr(
        "src.views.get_stock_prices",
        lambda _: [{"ticker": "AAPL", "price": 150}],
    )

    result: dict[str, Any] = main_page_view(
        date_time="2022-01-15 12:00:00",
        transactions=sample_transactions_df.to_dict(orient="records"),
    )

    assert isinstance(result, dict)

    # расходы
    assert "expenses" in result
    assert isinstance(result["expenses"]["total_amount"], int)
    assert isinstance(result["expenses"]["main"], list)
    assert isinstance(result["expenses"]["transfers_and_cash"], list)

    # доходы
    assert "income" in result
    assert isinstance(result["income"]["total_amount"], int)
    assert isinstance(result["income"]["main"], list)

    # курсы / акции
    assert isinstance(result["currency_rates"], list)
    assert isinstance(result["stock_prices"], list)


def test_main_page_view_expenses_content(
    sample_transactions_df: pd.DataFrame,
    monkeypatch,
) -> None:
    """
    Проверяет корректность структуры элементов расходов.
    """

    monkeypatch.setattr("src.views.get_currency_rates", lambda _: [])
    monkeypatch.setattr("src.views.get_stock_prices", lambda _: [])

    result = main_page_view(
        date_time="2022-01-20 10:00:00",
        transactions=sample_transactions_df.to_dict(orient="records"),
    )

    expenses_main = result["expenses"]["main"]

    for item in expenses_main:
        assert "category" in item
        assert "amount" in item
        assert isinstance(item["category"], str)
        assert isinstance(item["amount"], int)


def test_main_page_view_income_content(
    sample_transactions_df: pd.DataFrame,
    monkeypatch,
) -> None:
    monkeypatch.setattr("src.views.get_currency_rates", lambda _: [])
    monkeypatch.setattr("src.views.get_stock_prices", lambda _: [])

    result = main_page_view(
        date_time="2022-01-10 09:00:00",
        transactions=sample_transactions_df.to_dict(orient="records"),
    )

    for item in result["income"]["main"]:
        assert "category" in item
        assert "amount" in item
        assert isinstance(item["category"], str)
        assert isinstance(item["amount"], int)


def test_main_page_view_invalid_date_format(
    sample_transactions_df: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError):
        main_page_view(
            date_time="2022/01/10",
            transactions=sample_transactions_df.to_dict(orient="records"),
        )


def test_main_page_view_empty_transactions(
    monkeypatch,
) -> None:
    monkeypatch.setattr("src.views.get_currency_rates", lambda _: [])
    monkeypatch.setattr("src.views.get_stock_prices", lambda _: [])

    result = main_page_view(
        date_time="2022-01-01 00:00:00",
        transactions=[],
    )

    assert result == {}
