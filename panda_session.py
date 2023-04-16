from typing import Literal

import requests
from bs4 import BeautifulSoup

from panda_class import PandaClass
from task import Task


class PandaSession(requests.Session):
    BASE_URL = "https://panda.ecs.kyoto-u.ac.jp"
    API_SITE_URL = f"{BASE_URL}/direct/site.json?_limit=1000"
    API_ALL_ASSIGNMENT_URL = f"{BASE_URL}/direct/assignment/site"
    API_TESTQUIZ_URL = f"{BASE_URL}/direct/sam_pub/context"

    def __init__(self, user_name: str, password: str) -> None:
        super().__init__()
        self.user_name = user_name
        self.password = password

    def create_soup(self, url):
        "urlからsoupを作る"
        res = self.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup

    def __get_lt(self, url):
        # ltを取得する
        soup = self.create_soup(url)
        lt = soup.find(attrs={"name": "lt"}).get("value")
        return lt

    def login(self):
        # PandAにログインする
        login_url = f"{self.BASE_URL}/cas/login?service=https%3A%2F%2Fpanda.ecs.kyoto-u.ac.jp%2Fsakai-login-tool%2Fcontainer"
        login_data = {
            "username": self.user_name,
            "password": self.password,
            "warn": "true",
            "lt": self.__get_lt(login_url),
            "execution": "e1s1",
            "_eventId": "submit",
        }
        self.post(login_url, data=login_data)

    def get_sites(self, year: int, semester: Literal["前期", "後期"]):
        res = self.get(self.API_SITE_URL).json()
        return [
            site
            for site in res["site_collection"]
            if site["title"].startswith(f"[{year}{semester}")
        ]

    def get_assignment(self, panda_class: PandaClass):
        res: list = self.get(
            f"{self.API_ALL_ASSIGNMENT_URL}/{panda_class.id}.json"
        ).json()["assignment_collection"]
        tasks: list[Task] = [
            Task("assignment", assignment, panda_class) for assignment in res
        ]
        return tasks

    def get_testquiz(self, panda_class: PandaClass):
        res: list = self.get(f"{self.API_TESTQUIZ_URL}/{panda_class.id}.json").json()[
            "sam_pub_collection"
        ]
        tasks: list[Task] = [
            Task("testquiz", testquiz, panda_class) for testquiz in res
        ]
        return tasks

    def get_short_url(self, path: str):
        return self.get(f"{self.BASE_URL}/direct/url/shorten/?path={path}").text
