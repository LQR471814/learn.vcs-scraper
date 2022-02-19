import html
import logging
import unicodedata

import requests
from lxml import etree
from navigators import *

from utils import htags, prune_tree


class UnexpectedHomeworkFormat(Exception):
    def __init__(self, dump: str) -> None:
        super().__init__(
            f"Got an unexpected element whilst structuring homework\nDUMP:\n{dump}")


class Client:
    navigation: list[Navigator] = [
        HomepageNavigator,
        QuarterNavigator,
        DateNavigator,
    ]

    def __init__(self, session: requests.Session) -> None:
        self.session = session

    @classmethod
    def login(cls, username: str, password: str):
        session = requests.Session()
        login_page_req = session.get('https://learn.vcs.net/login/index.php')

        tree = etree.HTML(login_page_req.text)
        logintoken = tree.xpath("//input[@name='logintoken']")[0].get('value')

        login_post = session.post(
            'https://learn.vcs.net/login/index.php',
            data={
                'anchor': '',
                'logintoken': logintoken,
                'username': username.lower(),
                'password': password,
            },
            allow_redirects=False,
        )

        logging.info(f'Session {login_post.cookies.get("MoodleSessionprod")}')
        return cls(session)

    def lesson_plans(self, class_id: int) -> etree._ElementTree:
        url = f'https://learn.vcs.net/course/view.php?id={class_id}'
        prevtree = None
        for Nav in self.navigation:
            navigator = Nav(url, self.session, prevtree)
            url = navigator.evaluate()
            prevtree = navigator.tree

        logging.info(url)
        r = self.session.get(url)
        assignment_tree = prune_tree(etree.HTML(r.text))
        return assignment_tree

    def pick_homework(self, tree: etree.ElementTree) -> list[etree.Element]:
        collecting = False
        collection = []

        for e in tree.xpath("//div[@class='no-overflow']/*"):
            if e.tag in htags:
                collecting = 'homework' in ''.join(
                    e.xpath('.//text()')).lower()
                continue
            if collecting:
                collection.append(e)

        return collection

    def homework(self, class_id: int) -> list[str]:
        assignments: list[str] = []

        assignment_tree = self.lesson_plans(class_id)
        homework_tree = self.pick_homework(assignment_tree)

        for e in homework_tree[0]:
            if e.tag == 'li' and e.text is not None:
                assignments.append(unicodedata.normalize('NFKD', ''.join(e.itertext())))
            else:
                raise UnexpectedHomeworkFormat(self.format_homework_tree(homework_tree))

        return assignments

    def homework_raw(self, class_id: int) -> str:
        assignment_tree = self.lesson_plans(class_id)
        homework_tree = self.pick_homework(assignment_tree)
        return self.format_homework_tree(homework_tree)

    def format_homework_tree(self, tree: list[etree._Element]):
        homework_text = ""
        for e in tree:
            homework_text += etree.tostring(e).decode('utf8') + '\n'
        return html.unescape(homework_text)
