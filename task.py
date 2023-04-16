import re
from typing import Literal

from panda_class import PandaClass

TaskType = Literal["assignment", "testquiz"]


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
                self.deadline = task_data["dueTime"]["epochSecond"]
                self.panda_description = re.sub(
                    r"</?[a-z]+>", "", task_data["instructions"]
                )
                self.finished = task_data["submissions"][0]["userSubmission"]
            case "testquiz":
                self.panda_id = str(task_data["publishedAssessmentId"])
                self.deadline = task_data["dueDate"] // 1000
                self.panda_description = ""
                self.finished = False

    @property
    def url(self):
        match (self.task_type):
            case "assignment":
                return (
                    f"https://panda.ecs.kyoto-u.ac.jp/direct/assignment/{self.panda_id}"
                )
            case "testquiz":
                return self.panda_class.url

    @property
    def ticktick_title(self):
        """ticktickに登録するタイトル"""
        return f"{self.title}（{self.panda_class.day_of_week_ja}{self.panda_class.period}{self.panda_class.title}）"

    @property
    def ticktick_description(self):
        lines = [
            line for line in [self.panda_id, self.url, self.panda_description] if line
        ]
        return "\n\n".join(lines)
