from datetime import datetime

import requests
from lxml import etree

from utils import normalize_redirect_url, text_without_accessibility


class NoEntreeError(Exception):
    def __init__(self) -> None:
        super().__init__("No entree for today.")


class Navigator:
    url: str
    tree: etree._ElementTree

    def __init__(
        self, url: str,
        session: requests.Session,
        tree: etree._ElementTree = None
    ) -> None:
        self.url = url
        self.tree = etree.HTML(session.get(url).text)

    def evaluate(self):  # ? This should return another navigator
        raise Exception("cannot run unimplemented function!")


class HomepageNavigator(Navigator):
    def evaluate(self) -> str | None:
        return self.tree.xpath("//a[contains(@title, 'Homework')]")[0].get('href')


class QuarterNavigator(Navigator):
    def __init__(
        self, url: str | None,
        session: requests.Session,
        tree: etree._ElementTree = None
    ) -> None:
        if url is None:
            self.tree = tree
        else:
            super().__init__(url, session, tree)

    def evaluate(self) -> str:
        number = 0
        for name in self.tree.xpath(f"//li[contains(@class, 'modtype_book')]{text_without_accessibility}"):
            split_name = name.split(' ')
            if int(split_name[1]) > number:
                number = int(split_name[1])
        return self.tree.xpath(
            f"//a[@class='aalink'][//*[contains(text(), 'Quarter {number}')]]"
        )[0].get('href')


class DateNavigator(Navigator):
    month_map: dict[int, str] = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    def evaluate(self) -> str:
        day_elements = self.tree.xpath(
            f"//li/a["
            f"contains(text(), '{self.month_map[datetime.now().month]}') and "
            f"contains(text(), '{datetime.now().day}')]"
        )

        if len(day_elements) < 1:
            raise NoEntreeError()

        if len(day_elements) > 1:
            raise Exception("More than one element matched for today's date!")

        return normalize_redirect_url(self.url, day_elements[0].get('href'))
