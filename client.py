import html
import logging

import requests
from lxml import etree
from navigators import *

from utils import htags, prune_tree


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

    def homework(self, class_id: int):
        assignment_tree = self.lesson_plans(class_id)
        assignment_text = ""
        for e in self.pick_homework(assignment_tree):
            assignment_text += etree.tostring(e).decode('utf8') + '\n'
        assignment_text = html.unescape(assignment_text)
        return assignment_text
