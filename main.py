from config import COMPANY_ID
from src.api import HeadHunterAPI
from src.database import DBManager


def main():
    # Инициализация
    hh_api = HeadHunterAPI()
    db = DBManager()

    # Создание таблиц
    db.create_tables()

    # Сбор и сохранение данных
    for company_id in COMPANY_ID:
        employer = hh_api.get_employer(company_id)
        if employer:
            db.save_employer(employer)
            print(f"Сохранен работодатель: {employer['name']}")

            vacancies = hh_api.get_employer_vacancies(company_id)
            for vacancy in vacancies:
                db.save_vacancy(vacancy)
            print(f"Сохранено вакансий: {len(vacancies)}")

    # Взаимодействие с пользователем
    while True:
        print("\nВыберите действие:")
        print("1. Список компаний и количество вакансий")
        print("2. Все вакансии")
        print("3. Средняя зарплата")
        print("4. Вакансии с зарплатой выше средней")
        print("5. Поиск вакансий по ключевому слову")
        print("0. Выход")

        choice = input("> ")

        if choice == "1":
            companies = db.get_companies_and_vacancies_count()
            for company in companies:
                print(f"{company['name']}: {company['count']} вакансий")

        elif choice == "2":
            vacancies = db.get_all_vacancies()
            for vac in vacancies:
                salary = f"от {vac['salary_from']} до {vac['salary_to']}" if vac['salary_from'] or vac[
                    'salary_to'] else "не указана"
                print(f"{vac['company']}: {vac['title']} - {salary}")
                print(f"Ссылка: {vac['url']}\n")

        elif choice == "3":
            avg = db.get_avg_salary()
            print(f"Средняя зарплата: {avg:.2f} руб.")

        elif choice == "4":
            vacancies = db.get_vacancies_with_higher_salary()
            for vac in vacancies:
                salary = f"от {vac['salary_from']} до {vac['salary_to']}"
                print(f"{vac['company']}: {vac['title']} - {salary}")
                print(f"Ссылка: {vac['url']}\n")

        elif choice == "5":
            keyword = input("Введите ключевое слово: ")
            vacancies = db.get_vacancies_with_keyword(keyword)
            for vac in vacancies:
                salary = f"от {vac['salary_from']} до {vac['salary_to']}" if vac['salary_from'] or vac[
                    'salary_to'] else "не указана"
                print(f"{vac['company']}: {vac['title']} - {salary}")
                print(f"Ссылка: {vac['url']}\n")

        elif choice == "0":
            break

    db.close()


if __name__ == "__main__":
    main()
