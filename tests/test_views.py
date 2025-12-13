from unittest.mock import patch

import pandas as pd
import pytest

from src.views import main_page_view

# Тестирование основного сценария main_page_view с использованием mock-ов


@patch("src.views.get_stock_prices")
@patch("src.views.get_currency_rates")
@patch("src.views.top_transactions")
@patch("src.views.cards_summary")
@patch("src.views.load_user_settings")
@patch("src.views.get_greeting")
def test_main_page_view_basic_flow(
    mock_get_greeting,
    mock_load_user_settings,
    mock_cards_summary,
    mock_top_transactions,
    mock_get_currency_rates,
    mock_get_stock_prices,
    sample_transactions_df,
):
    """
    Проверяет, что main_page_view вызывает все необходимые вспомогательные
    функции и формирует корректную структуру ответа.
    """

    mock_get_greeting.return_value = "Добрый день, User!"
    mock_load_user_settings.return_value = {"user_currencies": ["EUR", "USD"], "user_stocks": ["AAPL"]}
    mock_cards_summary.return_value = [{"card": "Visa 1234", "balance": 1000.0}]
    mock_top_transactions.return_value = [{"date": "...", "amount": -500.0}]
    mock_get_currency_rates.return_value = [{"currency": "EUR", "rate": 90.0}]
    mock_get_stock_prices.return_value = [{"stock": "AAPL", "price": 150.0}]

    date_time_input = "2021-12-21 14:30:00"

    result = main_page_view(
        date_time=date_time_input,
        transactions=sample_transactions_df,
    )

    mock_get_greeting.assert_called_once_with(pd.to_datetime(date_time_input))
    mock_load_user_settings.assert_called_once()

    mock_cards_summary.assert_called_once()
    mock_top_transactions.assert_called_once()

    mock_get_currency_rates.assert_called_once_with(["EUR", "USD"])
    mock_get_stock_prices.assert_called_once_with(["AAPL"])

    assert "greeting" in result
    assert "cards" in result
    assert "top_transactions" in result
    assert "currency_rates" in result
    assert "stock_prices" in result

    assert result["greeting"] == "Добрый день, User!"
    assert result["currency_rates"] == [{"currency": "EUR", "rate": 90.0}]
    assert result["stock_prices"] == [{"stock": "AAPL", "price": 150.0}]


# Тестирование сценариев без пользовательских настроек


@patch("src.views.get_stock_prices")
@patch("src.views.get_currency_rates")
@patch("src.views.load_user_settings")
def test_main_page_view_no_settings(
    mock_load_user_settings, mock_get_currency_rates, mock_get_stock_prices, sample_transactions_df
):
    """
    Проверяет, что запросы на курсы валют/акции НЕ выполняются, если
    в настройках пользователя они не указаны.
    """

    mock_load_user_settings.return_value = {"user_currencies": [], "user_stocks": []}

    date_time_input = "2021-12-21 14:30:00"

    result = main_page_view(
        date_time=date_time_input,
        transactions=sample_transactions_df,
    )

    mock_get_currency_rates.assert_not_called()
    mock_get_stock_prices.assert_not_called()

    assert result["currency_rates"] == []
    assert result["stock_prices"] == []


# Тестирование обработки ошибок


def test_main_page_view_invalid_date_format(sample_transactions_df):
    """
    Проверяет, что функция выбрасывает ValueError при некорректном формате даты/времени.
    """
    invalid_date = "2021-12-21_INVALID_TIME"

    with pytest.raises(ValueError, match="Некорректный формат даты"):
        main_page_view(
            date_time=invalid_date,
            transactions=sample_transactions_df,
        )
