from datetime import datetime, timedelta

from requests import Session

from task import Task


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
            if task_data["properties"]["panda_id"]["rich_text"][0]["plain_text"] == task.panda_id:
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
                "名前": {"title": [{"text": {"content": f"{task.ticktick_title}）"}}]},
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
