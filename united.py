import os
import re
from datetime import datetime, timedelta
from time import sleep
from typing import Literal

import dotenv
import requests
from bs4 import BeautifulSoup
from requests import Session

TaskType = Literal["assignment", "testquiz"]


class PandaClass:
    BASE_URL = "https://panda.ecs.kyoto-u.ac.jp/portal/site/"
    DAYS_OF_WEEK_JA = ["月", "火", "水", "木", "金", "土", "日"]

    id: str
    title: str
    day_of_week: int
    """曜日（0:月曜日）"""
    period: int
    """○限"""
    # assignment_url: str | None
    # testquiz_url: str | None

    def __init__(self, site_data: dict) -> None:
        self.id = site_data["id"]
        self.title = re.sub(r"^\[.*?\]", "", site_data["title"]).strip()
        self.day_of_week = self.DAYS_OF_WEEK_JA.index(site_data["title"][7])
        self.period = ord(site_data["title"][8]) - ord("０")

    @property
    def url(self):
        return self.BASE_URL + self.id

    @property
    def day_of_week_ja(self):
        """日本語の曜日"""
        return self.DAYS_OF_WEEK_JA[self.day_of_week]


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
        return [site for site in res["site_collection"] if site["title"].startswith(f"[{year}{semester}")]

    def get_assignment(self, panda_class: PandaClass):
        res: list = self.get(f"{self.API_ALL_ASSIGNMENT_URL}/{panda_class.id}.json").json()["assignment_collection"]
        tasks: list[Task] = [Task("assignment", assignment, panda_class) for assignment in res]
        return tasks

    def get_testquiz(self, panda_class: PandaClass):
        res: list = self.get(f"{self.API_TESTQUIZ_URL}/{panda_class.id}.json").json()["sam_pub_collection"]
        tasks: list[Task] = [Task("testquiz", testquiz, panda_class) for testquiz in res]
        return tasks

    def get_short_url(self, path: str):
        return self.get(f"{self.BASE_URL}/direct/url/shorten/?path={path}").text


class Task:
    title: str
    panda_class: PandaClass
    task_type: TaskType
    panda_id: str
    deadline: int
    """締め切り（日本の標準時でエポック秒）"""
    panda_description: str
    finished: bool

    def __init__(self, type: TaskType, task_data, panda_class: PandaClass) -> None:
        self.title = task_data["title"]
        self.task_type = type
        self.panda_class = panda_class
        match (type):
            case "assignment":
                self.panda_id = task_data["id"]
                self.deadline = task_data["dueTime"]["epochSecond"] + 32400
                self.panda_description = re.sub(r"</?[a-z0-9]+>", "", task_data["instructions"])
                try:
                    self.finished = task_data["submissions"][0]["userSubmission"]
                except TypeError:
                    self.finished = False
            case "testquiz":
                self.panda_id = str(task_data["publishedAssessmentId"])
                self.deadline = task_data["dueDate"] // 1000 + 32400
                self.panda_description = ""
                self.finished = False

    @property
    def url(self):
        match (self.task_type):
            case "assignment":
                return f"https://panda.ecs.kyoto-u.ac.jp/direct/assignment/{self.panda_id}"
            case "testquiz":
                return self.panda_class.url

    @property
    def ticktick_title(self):
        """ticktickに登録するタイトル"""
        return f"{self.title}（{self.panda_class.day_of_week_ja}{self.panda_class.period}{self.panda_class.title}）"

    @property
    def ticktick_description(self):
        lines = [line for line in [self.panda_id, self.url, self.panda_description] if line]
        return "\n\n".join(lines)


class NotionClient(Session):
    exist_task_data: list[dict]

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, secret: str, db_id: str) -> None:
        """Parameters
        ----------
        - secret: シークレット
        - db_id: データベースID
        """
        super().__init__()
        self.secret = secret
        self.db_id = db_id
        self.__query_tasks()

    def __query_tasks(self) -> None:
        """Notionデータベースからタスクをクエリするためのプライベートメソッド。"""
        res = self.post(f"{self.db_url}/query", headers=self.HEADERS)
        self.exist_task_data = res.json()["results"]

    def find(self, task: Task):
        for task_data in self.exist_task_data:
            pid_li = task_data["properties"]["panda_id"]["rich_text"]
            if pid_li and pid_li[0]["plain_text"] == task.panda_id:
                return task_data

    def exist(self, task: Task) -> bool:
        if self.find(task):
            return True
        return False

    def register_task(self, task: Task) -> None:
        dl = datetime.fromtimestamp(task.deadline)
        if (dl.hour == 0 or dl.hour == 9) and dl.minute == 0:
            dl -= timedelta(minutes=1)
        body = {
            "parent": {"database_id": self.db_id},
            "properties": {
                "名前": {"title": [{"text": {"content": task.ticktick_title}}]},
                "panda_id": {"rich_text": [{"text": {"content": task.panda_id}}]},
                "締切": {"date": {"start": dl.strftime("%Y-%m-%dT%H:%M:%S+09:00")}},
                # "締切": {"date": {"start": (dl - timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S+09:00")}},
                "URL": {"url": task.url},
            },
        }
        self.post(self.pate_url, headers=self.HEADERS, json=body)

    @property
    def HEADERS(self):
        return {"accept": "application/json", "Notion-Version": "2022-06-28", "content-type": "application/json", "authorization": "Bearer " + self.secret}

    @property
    def db_url(self):
        """NotionデータベースのURLを返すプロパティ。"""
        return f"{self.BASE_URL}/databases/{self.db_id}"

    @property
    def pate_url(self):
        """NotionページのURLを返すプロパティ。"""
        return f"{self.BASE_URL}/pages"


def main(*args):
    # 環境変数の読み込み
    dotenv.load_dotenv()
    PANDA_USER_NAME = os.getenv("PANDA_USER_NAME")
    PANDA_PASSWORD = os.getenv("PANDA_PASSWORD")
    NOTION_SECRET = os.getenv("NOTION_SECRET")
    NOTION_DB_ID = os.getenv("NOTION_DB_ID")
    if not PANDA_USER_NAME:
        raise ValueError("PANDA_USER_NAME is not set")
    if not PANDA_PASSWORD:
        raise ValueError("PANDA_PASSWORD is not set")
    if not NOTION_SECRET:
        raise ValueError("NOTION_SECRET is not set")
    if not NOTION_DB_ID:
        raise ValueError("NOTION_DB_ID is not set")

    # PandAから課題を取得
    session = PandaSession(PANDA_USER_NAME, PANDA_PASSWORD)
    session.login()
    sites = session.get_sites(2023, "前期")
    classes = [PandaClass(site) for site in sites]
    tasks: list[Task] = []
    for cls in classes:
        tasks.extend(session.get_assignment(cls))
        sleep(0.5)
        tasks.extend(session.get_testquiz(cls))
        print(f"Get: {cls.title}")
        sleep(0.5)
    print()

    # TickTickに課題を登録
    notion_client = NotionClient(NOTION_SECRET, NOTION_DB_ID)
    for task in tasks:
        notion_task = notion_client.find(task)
        if task.finished:
            if notion_task:
                try:
                    # ticktick_client.task.complete(id=notion_task["id"])
                    print(f"Complete: {task.ticktick_title}")
                except TypeError:
                    pass
        else:
            if not notion_task:
                d = datetime.fromtimestamp(task.deadline)
                if d.hour == 0 and d.minute == 0:
                    d -= timedelta(minutes=1)
                notion_client.register_task(task)
                print(f"Create: {task.ticktick_title}")
        sleep(0.5)
