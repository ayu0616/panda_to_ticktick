import re


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
