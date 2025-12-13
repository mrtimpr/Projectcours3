import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.utils import (cards_summary, get_currency_rates, get_greeting, get_month_period, get_stock_prices,
                       load_user_settings, top_transactions)


def test_get_greeting():
    """
    Проверяет, что функция get_greeting возвращает правильное приветствие
    в зависимости от времени суток.
    """
    assert get_greeting(datetime(2023, 1, 1, 8, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2023, 1, 1, 14, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2023, 1, 1, 20, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2023, 1, 1, 2, 0, 0)) == "Доброй ночи"


def test_get_month_period():
    """
    Проверяет, что функция get_month_period возвращает правильный диапазон дат
    (с начала месяца по текущую дату).
    """
    date = datetime(2023, 5, 15, 10, 30, 0)
    start_date, end_date = get_month_period(date)

    assert start_date == datetime(2023, 5, 1, 0, 0, 0)
    assert end_date == date


@patch("builtins.open")
@patch("os.path.exists")
def test_load_user_settings_success(mock_exists, mock_open):
    """
    Проверяет успешную загрузку настроек из файла JSON.
    """
    mock_exists.return_value = True
    mock_file = MagicMock()
    mock_file.read.return_value = '{"user_currencies": ["USD"], "user_stocks": ["GOOG"]}'
    mock_open.return_value.__enter__.return_value = mock_file

    settings = load_user_settings("test_path.json")

    assert settings["user_currencies"] == ["USD"]
    assert settings["user_stocks"] == ["GOOG"]


@patch("os.path.exists")
def test_load_user_settings_file_not_found(mock_exists):
    """
    Проверяет возврат пустых настроек, если файл не найден.
    """
    mock_exists.return_value = False
    settings = load_user_settings("non_existent_file.json")

    assert settings == {"user_currencies": [], "user_stocks": []}


@patch("builtins.open")
@patch("os.path.exists")
def test_load_user_settings_empty_file(mock_exists, mock_open):
    """
    Проверяет возврат пустых настроек, если файл пустой.
    """
    mock_exists.return_value = True
    mock_file = MagicMock()
    mock_file.read.return_value = ""
    mock_open.return_value.__enter__.return_value = mock_file

    settings = load_user_settings("empty.json")

    assert settings == {"user_currencies": [], "user_stocks": []}


@patch("builtins.open")
@patch("os.path.exists")
def test_load_user_settings_invalid_json(mock_exists, mock_open):
    """
    Проверяет, что функция выбрасывает JSONDecodeError при некорректном JSON.
    """
    mock_exists.return_value = True
    mock_file = MagicMock()
    mock_file.read.return_value = '{"user_currencies": ["USD"],}'
    mock_open.return_value.__enter__.return_value = mock_file

    with pytest.raises(json.JSONDecodeError):
        load_user_settings("invalid.json")


# Тесты для аналитики по транзакциям (cards_summary, top_transactions)


def test_cards_summary(sample_transactions_df):
    """
    Проверяет корректность агрегации данных по картам.
    """
    df_dec = sample_transactions_df[
        sample_transactions_df["Дата операции"].str.contains("2021-12")
        | sample_transactions_df["Дата операции"].str.contains("20.12.2021")
        | sample_transactions_df["Дата операции"].str.contains("21.12.2021")
        | sample_transactions_df["Дата операции"].str.contains("10.12.2021")
    ].copy()

    if df_dec.empty:
        df_dec = sample_transactions_df[
            sample_transactions_df["Дата операции"].str.contains("20.12.2021")
            | sample_transactions_df["Дата операции"].str.contains("21.12.2021")
            | sample_transactions_df["Дата операции"].str.contains("10.12.2021")
        ].copy()

    summary = cards_summary(df_dec)

    assert len(summary) == 2

    card1 = next(item for item in summary if item["last_digits"] == "5814")
    card2 = next(item for item in summary if item["last_digits"] == "7512")

    assert card1["total_spent"] == -800.0
    assert card1["cashback"] == 8.0
    assert card2["total_spent"] == -2000.0
    assert card2["cashback"] == 20.0


def test_top_transactions(sample_transactions_df):
    """
    Проверяет, что функция возвращает топ транзакций, отсортированных по убыванию суммы.
    """

    sample_transactions_df["Дата операции"] = pd.to_datetime(
        sample_transactions_df["Дата операции"],
        format="%d.%m.%Y %H:%M:%S",
    )

    top_n = top_transactions(sample_transactions_df, limit=3)

    assert len(top_n) == 3
    amounts = [t["amount"] for t in top_n]
    assert amounts == [-2000.0, -500.0, -450.0]


# Тесты для внешних API (get_currency_rates, get_stock_prices)


@patch("src.utils.requests.get")
@patch.dict(os.environ, {"EXCHANGE_API_URL": "http://testapi.com", "EXCHANGE_API_KEY": "testkey"})
def test_get_currency_rates_success(mock_get):
    """
    Проверяет успешный запрос и парсинг курсов валют.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "base": "USD",
        "rates": {"EUR": 0.9, "GBP": 0.8},
    }
    mock_get.return_value = mock_response

    currencies = ["EUR", "GBP"]
    rates = get_currency_rates(currencies)

    assert len(rates) == 2
    assert rates[0]["currency"] == "EUR"
    assert rates[0]["rate"] == 0.9
    assert rates[1]["currency"] == "GBP"
    assert rates[1]["rate"] == 0.8
    mock_get.assert_called_once()


@patch("src.utils.requests.get")
def test_get_currency_rates_timeout(mock_get):
    """
    Проверяет обработку исключения таймаута запроса.
    """
    mock_get.side_effect = requests.Timeout("Таймаут")

    rates = get_currency_rates(["EUR"])

    assert rates == []
    mock_get.assert_called_once()


@patch("src.utils.requests.get")
def test_get_stock_prices_success(mock_get):
    """
    Проверяет успешный запрос и парсинг цен акций с Stooq API.
    """
    mock_response = MagicMock()
    mock_response.text = (
        "Symbol,Date,Time,Open,High,Low,Close,Volume\nAAPL.US,20230101,120000,150.0,155.0,149.0,152.5,10000"
    )
    mock_get.return_value = mock_response

    stocks = ["AAPL"]
    prices = get_stock_prices(stocks)

    assert len(prices) == 1
    assert prices[0]["stock"] == "AAPL"
    assert prices[0]["price"] == 152.5


@patch("src.utils.requests.get")
def test_get_stock_prices_failure(mock_get):
    """
    Проверяет обработку ошибки получения цены акции (возврат None и фильтрация).
    """
    mock_get.side_effect = Exception("Ошибка сети или парсинга")

    stocks = ["GOOG"]
    prices = get_stock_prices(stocks)

    assert prices == []
