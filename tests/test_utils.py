import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import requests

from src.utils import (cards_summary, get_currency_rates, get_greeting, get_month_period, get_stock_prices,
                       load_user_settings, top_transactions)


def test_get_greeting() -> None:
    assert get_greeting(datetime(2023, 1, 1, 8, 0)) == "Доброе утро"
    assert get_greeting(datetime(2023, 1, 1, 14, 0)) == "Добрый день"
    assert get_greeting(datetime(2023, 1, 1, 20, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2023, 1, 1, 2, 0)) == "Доброй ночи"


def test_get_month_period() -> None:
    date = datetime(2023, 5, 15, 10, 30)
    start, end = get_month_period(date)

    assert start == datetime(2023, 5, 1, 0, 0, 0)
    assert end == date


@patch("os.path.exists", return_value=True)
@patch("builtins.open")
def test_load_user_settings_success(
    mock_open: Mock,
    mock_exists: Mock,
) -> None:
    mock_file = MagicMock()
    mock_file.read.return_value = json.dumps(
        {
            "user_currencies": ["USD"],
            "user_stocks": ["AAPL"],
        }
    )
    mock_open.return_value.__enter__.return_value = mock_file

    result = load_user_settings("settings.json")

    assert result == {
        "user_currencies": ["USD"],
        "user_stocks": ["AAPL"],
    }


@patch("os.path.exists", return_value=False)
def test_load_user_settings_file_not_found(mock_exists: Mock) -> None:
    result = load_user_settings("missing.json")

    assert result == {"user_currencies": [], "user_stocks": []}


@patch("os.path.exists", return_value=True)
@patch("builtins.open")
def test_load_user_settings_empty_file(
    mock_open: Mock,
    mock_exists: Mock,
) -> None:
    mock_file = MagicMock()
    mock_file.read.return_value = ""
    mock_open.return_value.__enter__.return_value = mock_file

    result = load_user_settings("empty.json")

    assert result == {"user_currencies": [], "user_stocks": []}


@patch("os.path.exists", return_value=True)
@patch("builtins.open")
def test_load_user_settings_invalid_json(
    mock_open: Mock,
    mock_exists: Mock,
) -> None:
    mock_file = MagicMock()
    mock_file.read.return_value = "{ invalid json }"
    mock_open.return_value.__enter__.return_value = mock_file

    with pytest.raises(json.JSONDecodeError):
        load_user_settings("broken.json")


def test_cards_summary(sample_transactions_df: pd.DataFrame) -> None:
    result = cards_summary(sample_transactions_df)

    assert isinstance(result, list)
    assert len(result) == 2

    for item in result:
        assert "last_digits" in item
        assert "total_spent" in item
        assert "cashback" in item
        assert isinstance(item["total_spent"], float)
        assert isinstance(item["cashback"], float)


def test_top_transactions(sample_transactions_df: pd.DataFrame) -> None:
    df = sample_transactions_df.copy()
    df["Дата операции"] = pd.to_datetime(
        df["Дата операции"],
        format="%d.%m.%Y %H:%M:%S",
    )

    result = top_transactions(df, limit=3)

    assert len(result) == 3

    amounts = [item["amount"] for item in result]
    assert amounts == sorted(amounts, key=abs, reverse=True)


@patch("src.utils.requests.get")
def test_get_currency_rates_success(mock_get: Mock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "rates": {
            "USD": 1.1,
            "GBP": 0.85,
        }
    }
    mock_get.return_value = mock_response

    result = get_currency_rates(["USD", "GBP", "EUR"])

    assert result == [
        {"currency": "USD", "rate": 1.1},
        {"currency": "GBP", "rate": 0.85},
        {"currency": "EUR", "rate": 1.0},
    ]


@patch("src.utils.requests.get", side_effect=requests.RequestException)
def test_get_currency_rates_failure(mock_get: Mock) -> None:
    result = get_currency_rates(["USD"])

    assert result == [{"currency": "USD", "rate": 1.17}]


@patch("src.utils.requests.get")
def test_get_stock_prices_success(mock_get: Mock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "quoteResponse": {
            "result": [
                {
                    "symbol": "AAPL",
                    "regularMarketPrice": 150.5,
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    result = get_stock_prices(["AAPL"])

    assert result == [{"stock": "AAPL", "price": 150.5}]


@patch("src.utils.requests.get", side_effect=requests.RequestException)
def test_get_stock_prices_failure(mock_get: Mock) -> None:
    result = get_stock_prices(["AAPL"])

    assert len(result) == 5
    assert result[0]["stock"] == "AAPL"
