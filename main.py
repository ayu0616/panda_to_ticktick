import os
from datetime import datetime, timedelta
from time import sleep

import dotenv

from panda_class import PandaClass
from panda_session import PandaSession
from task import Task
from ticktick_client import Client


def main():
    # 環境変数の読み込み
    dotenv.load_dotenv()
    PANDA_USER_NAME = os.getenv("PANDA_USER_NAME")
    PANDA_PASSWORD = os.getenv("PANDA_PASSWORD")
    TICKTICK_CLIENT_ID = os.getenv("TICKTICK_CLIENT_ID")
    TICKTICK_CLIENT_SECRET = os.getenv("TICKTICK_CLIENT_SECRET")
    TICKTICK_USER_NAME = os.getenv("TICKTICK_USER_NAME")
    TICKTICK_PASSWORD = os.getenv("TICKTICK_PASSWORD")
    if not PANDA_USER_NAME:
        raise ValueError("PANDA_USER_NAME is not set")
    if not PANDA_PASSWORD:
        raise ValueError("PANDA_PASSWORD is not set")
    if not TICKTICK_CLIENT_ID:
        raise ValueError("TICKTICK_CLIENT_ID is not set")
    if not TICKTICK_CLIENT_SECRET:
        raise ValueError("TICKTICK_CLIENT_SECRET is not set")
    if not TICKTICK_USER_NAME:
        raise ValueError("TICKTICK_USER_NAME is not set")
    if not TICKTICK_PASSWORD:
        raise ValueError("TICKTICK_PASSWORD is not set")

    # PandAから課題を取得
    session = PandaSession(PANDA_USER_NAME, PANDA_PASSWORD)
    session.login()
    sites = session.get_sites(2023, "前期")
    classes = [PandaClass(site) for site in sites]
    tasks: list[Task] = []
    for cls in classes:
        tasks.extend(session.get_assignment(cls))
        sleep(1)
        tasks.extend(session.get_testquiz(cls))
        print(f"Get: {cls.title}")
        sleep(1)
    print()

    # TickTickに課題を登録
    ticktick_client = Client.login(
        TICKTICK_CLIENT_ID,
        TICKTICK_CLIENT_SECRET,
        TICKTICK_USER_NAME,
        TICKTICK_PASSWORD,
    )
    for task in tasks:
        ticktick_task = ticktick_client.find(task)
        if task.finished:
            if ticktick_task:
                ticktick_client.task.complete(id=ticktick_task["id"])
                print(f"Complete: {task.ticktick_title}")
        else:
            if not ticktick_task:
                d = datetime.fromtimestamp(task.deadline)
                if d.hour == 0 and d.minute == 0:
                    d -= timedelta(minutes=1)
                new_task = ticktick_client.task_builder(
                    title=task.ticktick_title,
                    content=task.ticktick_description,
                    due_date=d,
                )
                ticktick_client.task.create(new_task)
                print(f"Create: {task.ticktick_title}")
        sleep(1)


if __name__ == "__main__":
    main()
