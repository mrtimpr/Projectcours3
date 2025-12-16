import json
import logging
from typing import Any

import pandas as pd

from log_setup import setup_logging
from src.reports import spending_by_category
from src.services import (
    cashback_by_category,
    search_phone_numbers,
    search_transactions,
)
from src.views import main_page_view

DATA_PATH: str = "data/operations.xlsx"


def ask_date(prompt: str) -> str:
    while True:
        value: str = input(prompt).strip()
        try:
            pd.to_datetime(value)
            return value
        except ValueError:
            print("❌ Неверный формат даты. Используй YYYY-MM-DD")


def ask_int(prompt: str) -> int:
    while True:
        value: str = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print("❌ Нужно ввести целое число")


def show_menu() -> None:
    print(
        """
=== МЕНЮ ===
1. Отчет: траты по категории
2. Главная страница
3. Анализ выгодных категорий кешбэка
4. Поиск по транзакциям
5. Поиск по номеру телефона
0. Выход
"""
    )


def main() -> None:
    setup_logging()
    logger: logging.Logger = logging.getLogger(__name__)

    logger.info("Запуск приложения")

    print("=== Загрузка данных ===")
    df: pd.DataFrame = pd.read_excel(DATA_PATH)
    print(f"Загружено транзакций: {len(df)}")

    transactions: list[dict[str, Any]] = df.to_dict(orient="records")

    categories: list[str] = (
        df["Категория"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    categories.sort()

    while True:
        show_menu()
        choice: str = input("Выбери пункт меню: ").strip()

        # 0. Выход
        if choice == "0":
            logger.info("Завершение работы")
            print("Выход из программы 👋")
            return

        # 1. Траты по категории
        if choice == "1":
            print("\n=== Траты по категории ===")

            for i, cat in enumerate(categories, start=1):
                print(f"{i}. {cat}")

            while True:
                try:
                    idx: int = int(input("Выбери номер категории: "))
                    category: str = categories[idx - 1]
                    break
                except (ValueError, IndexError):
                    print("❌ Неверный выбор категории")

            date: str = ask_date("Введите дату (YYYY-MM-DD): ")

            result_json: str = spending_by_category(
                transactions=transactions,
                category=category,
                date=date,
            )

            print(result_json)
            continue

        # 2. Главная страница
        if choice == "2":
            print("\n=== Главная страница ===")

            date_time: str = input(
                "Введите дату и время (YYYY-MM-DD HH:MM:SS): "
            ).strip()

            try:
                view_result: dict[str, Any] = main_page_view(
                    date_time=date_time,
                    transactions=transactions,
                )
                print(json.dumps(view_result, ensure_ascii=False, indent=2))
            except ValueError as exc:
                print(f"❌ Ошибка: {exc}")

            continue

        # 3. Кешбэк
        if choice == "3":
            print("\n=== Анализ кешбэка ===")

            year: int = ask_int("Введите год: ")
            month: int = ask_int("Введите месяц (1–12): ")

            if not 1 <= month <= 12:
                print("❌ Месяц должен быть от 1 до 12")
                continue

            result_json: str = cashback_by_category(
                transactions=transactions,
                year=year,
                month=month,
            )

            print(result_json)
            continue

        # 4. Поиск
        if choice == "4":
            print("\n=== Поиск по транзакциям ===")

            query: str = input("Введите строку для поиска: ").strip()

            result_json: str = search_transactions(
                transactions=transactions,
                query=query,
            )

            result: list[dict[str, Any]] = json.loads(result_json)

            print(f"Найдено операций: {len(result)}")
            print(json.dumps(result[:3], ensure_ascii=False, indent=2))
            continue

        # 5. Телефон
        if choice == "5":
            print("\n=== Поиск по номеру телефона ===")

            phone: str = input(
                "Введите номер телефона (в любом формате): "
            ).strip()

            result_json: str = search_phone_numbers(
                transactions=transactions,
                phone=phone,
            )

            result: list[dict[str, Any]] = json.loads(result_json)

            print(f"Найдено операций: {len(result)}")
            print(json.dumps(result[:3], ensure_ascii=False, indent=2))
            continue

        print("❌ Неизвестный пункт меню")


if __name__ == "__main__":
    main()
