from typing import Dict, List, Optional

import requests


class HeadHunterAPI:
    """Класс для работы с API HeadHunter"""

    BASE_URL = 'https://api.hh.ru/'

    def get_employer(self, employer_id: int) -> Optional[Dict]:
        """Получает информацию о работодателе"""
        url = f"{self.BASE_URL}employers/{employer_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_employer_vacancies(self, employer_id: int) -> List[Dict]:
        """Получает вакансии работодателя"""
        url = f"{self.BASE_URL}vacancies"
        params = {'employer_id': employer_id, 'per_page': 100}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        return []
