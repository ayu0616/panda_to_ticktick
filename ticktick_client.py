from datetime import datetime, timedelta

from ticktick.api import TickTickClient
from ticktick.oauth2 import OAuth2

from task import Task


class Client(TickTickClient):
    PROJECT_ID = "60adb8098f08ea011ac0621e"
    REMINDERS = ["TRIGGER:-PT1440M", "TRIGGER:-PT60M"]

    exist_task_data: list[dict]

    def __init__(self, username: str, password: str, oauth: OAuth2) -> None:
        super().__init__(username, password, oauth)
        self.__query_task()

    @classmethod
    def login(
        cls,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ):
        oauth = OAuth2(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://127.0.0.1:3000",
        )
        return cls(username, password, oauth)

    def __query_task(self):
        res = self.task.get_from_project(self.PROJECT_ID)
        if type(res) != list:
            res = []
        now = datetime.now()
        completed = self.task.get_completed(now - timedelta(days=180), now)
        res.extend([task for task in completed if task["projectId"] == self.PROJECT_ID])
        self.exist_task_data = res

    def find(self, task: Task):
        for task_data in self.exist_task_data:
            if task_data["content"].startswith(task.panda_id):
                return task_data
        return None

    def exist(self, task: Task):
        if self.find(task):
            return True
        return False

    def task_builder(
        self,
        title: str,
        content: str,
        due_date: datetime,
        reminders: list[str] = REMINDERS,
    ):
        return self.task.builder(
            title=title,
            projectId=self.PROJECT_ID,
            content=content,
            startDate=due_date,
            dueDate=due_date,
            reminders=reminders,
        )


if __name__ == "__main__":
    import os
    from pprint import pprint

    TICKTICK_CLIENT_ID = os.getenv("TICKTICK_CLIENT_ID")
    TICKTICK_CLIENT_SECRET = os.getenv("TICKTICK_CLIENT_SECRET")
    TICKTICK_USER_NAME = os.getenv("TICKTICK_USER_NAME")
    TICKTICK_PASSWORD = os.getenv("TICKTICK_PASSWORD")
    if not TICKTICK_CLIENT_ID:
        raise ValueError("TICKTICK_CLIENT_ID is not set")
    if not TICKTICK_CLIENT_SECRET:
        raise ValueError("TICKTICK_CLIENT_SECRET is not set")
    if not TICKTICK_USER_NAME:
        raise ValueError("TICKTICK_USER_NAME is not set")
    if not TICKTICK_PASSWORD:
        raise ValueError("TICKTICK_PASSWORD is not set")
    ticktick_client = Client.login(
        TICKTICK_CLIENT_ID,
        TICKTICK_CLIENT_SECRET,
        TICKTICK_USER_NAME,
        TICKTICK_PASSWORD,
    )

    tasks = ticktick_client.query_task()
    pprint(tasks)
