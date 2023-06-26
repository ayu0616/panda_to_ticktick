import os
from datetime import datetime, timedelta
from time import sleep

import dotenv

from panda_class import PandaClass
from panda_session import PandaSession
from task import Task
from notion_client import NotionClient


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


if __name__ == "__main__":
    main()
