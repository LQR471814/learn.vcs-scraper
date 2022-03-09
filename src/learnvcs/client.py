import logging
from urllib.parse import parse_qs, urlparse

import requests
from lxml import etree

from learnvcs.navigators import *
from learnvcs.navigators import NavigationConfig
from learnvcs.utils import get_next, htag_selector, normalize_text, prune_tree, root


class DebugHomeworkStructure(Exception):
    def __init__(self, dump: str) -> None:
        super().__init__(
            f"Got an unexpected element whilst structuring homework\nDUMP:\n{dump}")

class UnexpectedHomeworkFormat(Exception):
    def __init__(self, url: str, message: str = 'Unexpected homework format!') -> None:
        self.url = url
        super().__init__(f"{message}\nGo to {url} for manual review")


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

    def lesson_plans(self, course_id: int, config: NavigationConfig = None) -> tuple[etree._ElementTree, str]:
        url = f'https://learn.vcs.net/course/view.php?id={course_id}'
        prevtree = None
        for Nav in self.navigation:
            navigator = Nav(url, self.session, config, prevtree)
            url = navigator.evaluate()
            prevtree = navigator.tree

        r = self.session.get(url)
        return etree.HTML(r.text), url

    def __pick_homework(self, tree: etree.ElementTree) -> etree.Element:
        root = tree.xpath("//div[@role='main']")[0]
        clean_root = prune_tree(root)
        anchor = clean_root.xpath(
            f".//{htag_selector}[contains(text(), 'Homework')]"
        )

        if anchor is not None and len(anchor) > 0:
            return get_next(anchor[0])
        else:
            anchor = root.xpath(f".//p[.//*[contains(text(), 'Homework')]]")
            if anchor is not None and len(anchor) > 0:
                return get_next(anchor[0])
            raise DebugHomeworkStructure(
                self.__format_homework_tree(root)
            )

    def __format_homework_tree(self, element: etree._Element):
        return normalize_text(
            etree.tostring(element).decode('utf8')
        ) + '\n'

    def homework(self, course_id: int, config: NavigationConfig = None) -> list[str]:
        assignments: list[str] = []

        lesson_plans_tree, url = self.lesson_plans(course_id, config)
        try:
            homework_body = self.__pick_homework(lesson_plans_tree)
        except DebugHomeworkStructure as err:
            raise UnexpectedHomeworkFormat(
                message=err, url=url,
            )

        if homework_body is None:
            raise UnexpectedHomeworkFormat(
                message='Could not get homework body!', url=url,
            )

        list_nodes = homework_body.xpath('.//li')
        if len(list_nodes) > 0:
            for node in list_nodes:
                homework_text = node.xpath('.//text()')
                if homework_text is None:
                    continue
                text = normalize_text(''.join(homework_text))
                if text == 'None':
                    continue
                assignments.append(text)
        else:
            homework_text = homework_body.xpath('.//text()')
            if homework_text is None:
                raise DebugHomeworkStructure(
                    self.__format_homework_tree(homework_body)
                )
            for text in homework_text:
                assignments.append(text)

        return assignments

    def homework_raw(self, course_id: int, config: NavigationConfig = None) -> str:
        assignment_tree = self.lesson_plans(course_id, config)
        homework_tree = self.__pick_homework(assignment_tree)
        return self.__format_homework_tree(homework_tree)

    def courses(self) -> dict[str, int]:
        courses: dict[str, int] = {}

        r = self.session.get(root)
        tree = etree.HTML(r.text)

        for course in tree.xpath(f"//div/ul[@class='unlist']/li//a"):
            courses[str(course.xpath('.//text()')[0])] = int(
                parse_qs(urlparse(course.get('href')).query)['id'][0]
            )

        return courses
