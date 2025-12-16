import json
from typing import Any

import pytest

from src.services import cashback_by_category, search_phone_numbers, search_transactions


@pytest.fixture
def sample_transactions() -> list[dict[str, Any]]:
    return [
        {
            "Дата операции": "10.01.2022 12:00:00",
            "Категория": "Кафе и рестораны",
            "Описание": "Обед",
            "Кэшбэк": 2.5,
        },
        {
            "Дата операции": "15.01.2022 18:30:00",
            "Категория": "Кафе и рестораны",
            "Описание": "Ужин",
            "Кэшбэк": 2.0,
        },
        {
            "Дата операции": "20.01.2022 09:00:00",
            "Категория": "Мобильная связь",
            "Описание": "Оплата телефона 89001234567",
            "Кэшбэк": 7.0,
        },
        {
            "Дата операции": "05.02.2022 10:00:00",
            "Категория": "ЖКХ",
            "Описание": "Коммунальные услуги",
            "Кэшбэк": 0.0,
        },
        {
            "Дата операции": "07.01.2022 11:00:00",
            "Категория": "Мобильная связь",
            "Описание": "Оплата телефона +7(901)987-65-43",
            "Кэшбэк": 0.0,
        },
    ]


# cashback_by_category


def test_cashback_by_category_basic(sample_transactions):
    result_json = cashback_by_category(
        transactions=sample_transactions,
        year=2022,
        month=1,
    )

    result = json.loads(result_json)

    assert isinstance(result, dict)
    assert result["Кафе и рестораны"] == 4.5
    assert result["Мобильная связь"] == 7.0
    assert sum(result.values()) == 11.5


def test_cashback_by_category_no_data(sample_transactions):
    result_json = cashback_by_category(
        transactions=sample_transactions,
        year=2023,
        month=1,
    )

    result = json.loads(result_json)
    assert result == {}


def test_cashback_by_category_empty_transactions():
    result_json = cashback_by_category(
        transactions=[],
        year=2022,
        month=1,
    )

    result = json.loads(result_json)
    assert result == {}


# search_transactions


def test_search_transactions_by_description(sample_transactions):
    result_json = search_transactions(
        transactions=sample_transactions,
        query="обед",
    )

    result = json.loads(result_json)

    assert len(result) == 1
    assert result[0]["Описание"] == "Обед"


def test_search_transactions_by_category(sample_transactions):
    result_json = search_transactions(
        transactions=sample_transactions,
        query="жкх",
    )

    result = json.loads(result_json)

    assert len(result) == 1
    assert result[0]["Категория"] == "ЖКХ"


def test_search_transactions_no_results(sample_transactions):
    result_json = search_transactions(
        transactions=sample_transactions,
        query="такси",
    )

    result = json.loads(result_json)
    assert result == []


# search_phone_numbers


def test_search_phone_numbers_found(sample_transactions):
    result_json = search_phone_numbers(
        transactions=sample_transactions,
        phone="89001234567",
    )

    result = json.loads(result_json)

    assert len(result) == 1
    assert "89001234567" in result[0]["Описание"]


def test_search_phone_numbers_different_format(sample_transactions):
    result_json = search_phone_numbers(
        transactions=sample_transactions,
        phone="+7 901 987 65 43",
    )

    result = json.loads(result_json)

    assert len(result) == 1
    assert "987" in result[0]["Описание"]


def test_search_phone_numbers_not_found(sample_transactions):
    result_json = search_phone_numbers(
        transactions=sample_transactions,
        phone="9999999999",
    )

    result = json.loads(result_json)
    assert result == []


def test_search_phone_numbers_empty_phone(sample_transactions):
    result_json = search_phone_numbers(
        transactions=sample_transactions,
        phone="",
    )

    result = json.loads(result_json)
    assert result == []
