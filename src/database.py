from typing import Dict, List

import psycopg2
from psycopg2 import sql

from config import DB_SETTINGS


class DBManager:
    """Класс для управления базой данных PostgreSQL."""

    def __init__(self):
        """Инициализирует соединение с БД и автоматически создает её, если она не существует."""
        try:
            # Подключение к серверу PostgreSQL (без указания БД)
            conn = psycopg2.connect(
                host=DB_SETTINGS["host"],
                user=DB_SETTINGS["user"],
                password=DB_SETTINGS["password"],
                port=DB_SETTINGS["port"],
            )
            conn.autocommit = True
            cur = conn.cursor()

            # Проверка существования БД и создание, если её нет
            cur.execute(
                sql.SQL("SELECT 1 FROM pg_database WHERE datname = {}").format(
                    sql.Literal(DB_SETTINGS["dbname"])
                )
            )
            if not cur.fetchone():
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(DB_SETTINGS["dbname"])
                    )
                )
                print(f"БД {DB_SETTINGS['dbname']} создана.")

            cur.close()
            conn.close()

            # Подключение к конкретной БД
            self.conn = psycopg2.connect(**DB_SETTINGS)
            self.conn.autocommit = True
        except psycopg2.Error as e:
            raise Exception(f"Ошибка при подключении к БД: {e}")

    def create_tables(self) -> None:
        """Создает таблицы employers и vacancies, если они не существуют."""
        with self.conn.cursor() as cur:
            try:
                # Таблица работодателей
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS employers (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        url VARCHAR(100)
                    )
                """
                )

                # Таблица вакансий
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vacancies (
                        id INTEGER PRIMARY KEY,
                        employer_id INTEGER REFERENCES employers(id),
                        title VARCHAR(100) NOT NULL,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        url VARCHAR(100)
                    )
                """
                )
                print("Таблицы созданы или уже существуют.")
            except psycopg2.Error as e:
                print(f"Ошибка при создании таблиц: {e}")

    def save_employer(self, employer: Dict) -> None:
        """Сохраняет работодателя в БД."""
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO employers (id, name, url)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (employer["id"], employer["name"], employer.get("alternate_url")),
                )
            except psycopg2.Error as e:
                print(f"Ошибка при сохранении работодателя: {e}")

    def save_vacancy(self, vacancy: Dict) -> None:
        """Сохраняет вакансию в БД."""
        salary = vacancy.get("salary") or {}
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO vacancies (id, employer_id, title, salary_from, salary_to, url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        vacancy["id"],
                        vacancy["employer"]["id"],
                        vacancy["name"],
                        salary.get("from"),
                        salary.get("to"),
                        vacancy.get("alternate_url"),
                    ),
                )
            except psycopg2.Error as e:
                print(f"Ошибка при сохранении вакансии: {e}")

    def get_companies_and_vacancies_count(self) -> List[Dict]:
        """Возвращает список компаний и количество их вакансий."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.name, COUNT(v.id)
                FROM employers e
                LEFT JOIN vacancies v ON e.id = v.employer_id
                GROUP BY e.id
                ORDER BY COUNT(v.id) DESC
                """
            )
            return [{"name": row[0], "count": row[1]} for row in cur.fetchall()]

    def get_all_vacancies(self) -> List[Dict]:
        """Возвращает все вакансии с информацией о компаниях."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.name, v.title, v.salary_from, v.salary_to, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
            """
            )
            return [
                {
                    "company": row[0],
                    "title": row[1],
                    "salary_from": row[2],
                    "salary_to": row[3],
                    "url": row[4],
                }
                for row in cur.fetchall()
            ]

    def get_avg_salary(self) -> float:
        """Возвращает среднюю зарплату по всем вакансиям."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT AVG((salary_from + salary_to) / 2)
                FROM vacancies
                WHERE salary_from IS NOT NULL AND salary_to IS NOT NULL
            """
            )
            result = cur.fetchone()[0]
            return float(result) if result else 0.0

    def get_vacancies_with_higher_salary(self) -> List[Dict]:
        """Возвращает вакансии с зарплатой выше средней."""
        avg = self.get_avg_salary()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.name, v.title, v.salary_from, v.salary_to, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                WHERE (v.salary_from + v.salary_to) / 2 > %s
            """,
                (avg,),
            )
            return [
                {
                    "company": row[0],
                    "title": row[1],
                    "salary_from": row[2],
                    "salary_to": row[3],
                    "url": row[4],
                }
                for row in cur.fetchall()
            ]

    def get_vacancies_with_keyword(self, keyword: str) -> List[Dict]:
        """Ищет вакансии по ключевому слову в названии."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.name, v.title, v.salary_from, v.salary_to, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.id
                WHERE v.title ILIKE %s
            """,
                (f"%{keyword}%",),
            )
            return [
                {
                    "company": row[0],
                    "title": row[1],
                    "salary_from": row[2],
                    "salary_to": row[3],
                    "url": row[4],
                }
                for row in cur.fetchall()
            ]

    def close(self) -> None:
        """Закрывает соединение с БД."""
        if self.conn:
            self.conn.close()
