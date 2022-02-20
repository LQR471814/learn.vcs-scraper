import html
import logging
import unicodedata
from urllib.parse import parse_qs, urlparse

import requests
from lxml import etree

from learnvcs.navigators import *
from learnvcs.utils import htags, prune_tree, root


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
        login_page_req = session.get(f'{root}/login/index.php')

        tree = etree.HTML(login_page_req.text)
        logintoken = tree.xpath("//input[@name='logintoken']")[0].get('value')

        login_post = session.post(
            f'{root}/login/index.php',
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

    def lesson_plans(self, course_id: int) -> etree._ElementTree:
        url = f'https://learn.vcs.net/course/view.php?id={course_id}'
        prevtree = None
        for Nav in self.navigation:
            navigator = Nav(url, self.session, prevtree)
            url = navigator.evaluate()
            prevtree = navigator.tree

        logging.info(url)
        r = self.session.get(url)
        assignment_tree = prune_tree(etree.HTML(r.text))
        return assignment_tree

    def __pick_homework(self, tree: etree.ElementTree) -> list[etree.Element]:
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

    def __format_homework_tree(self, tree: list[etree._Element]):
        homework_text = ""
        for e in tree:
            homework_text += etree.tostring(e).decode('utf8') + '\n'
        return html.unescape(homework_text)

    def homework(self, course_id: int) -> list[str]:
        assignments: list[str] = []

        assignment_tree = self.lesson_plans(course_id)
        homework_tree = self.__pick_homework(assignment_tree)

        for e in homework_tree[0]:
            if e.tag == 'li' and e.text is not None:
                assignments.append(unicodedata.normalize(
                    'NFKD', ''.join(e.itertext())))
            else:
                raise UnexpectedHomeworkFormat(
                    self.__format_homework_tree(homework_tree))

        return assignments

    def homework_raw(self, course_id: int) -> str:
        assignment_tree = self.lesson_plans(course_id)
        homework_tree = self.__pick_homework(assignment_tree)
        return self.__format_homework_tree(homework_tree)

    def courses(self) -> dict[str, int]:
        courses: dict[str, int] = {}

        r = self.session.get(root)
        tree = etree.HTML(r.text)

        for course in tree.xpath(f"//div/ul[@class='unlist']/li//a"):
            courses[course.xpath('.//text()')[0]] = int(
                parse_qs(urlparse(course.get('href')).query)['id'][0]
            )

        return courses
