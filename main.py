import html
import http.client as http_client
import logging
from datetime import datetime

import requests
from lxml import etree

from utils import htags, normalize_redirect_url, text_without_accessibility


def enable_debug_http():
    # ? HTTP Debugging
    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def get_session(username: str, password: str) -> requests.Session:
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

    return session


def get_lesson_plans(session: requests.Session, class_id: int):
    def get_quarter_screen() -> tuple[str, etree.ElementTree]:
        r = session.get(
            'https://learn.vcs.net/course/view.php',
            params={'id': class_id}
        )
        tree = etree.HTML(r.text)
        with open('debug', 'w') as f:
            f.write(r.text)
        return tree.xpath("//a[contains(@title, 'Homework')]")[0].get('href'), tree

    quarter_screen_url, quarter_tree = get_quarter_screen()
    if quarter_screen_url is not None:
        r = session.get(quarter_screen_url)
        quarter_tree = etree.HTML(r.text)

    def pick_quarter(tree: etree.ElementTree) -> str:
        number = 0
        for name in tree.xpath(f"//li[contains(@class, 'modtype_book')]{text_without_accessibility}"):
            split_name = name.split(' ')
            if int(split_name[1]) > number:
                number = int(split_name[1])
            print(split_name)

        return tree.xpath(
            f"//a[@class='aalink'][//*[contains(text(), 'Quarter {number}')]]"
        )[0].get('href')

    quarter_link = pick_quarter(quarter_tree)
    logging.info(quarter_link)
    r = session.get(quarter_link)
    dates_tree = etree.HTML(r.text)

    def pick_date(tree: etree.ElementTree) -> str:
        month_map: dict[int, str] = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }

        day_elements = tree.xpath(
            f"//li/a["
            f"contains(text(), '{month_map[datetime.now().month]}') and "
            f"contains(text(), '{datetime.now().day}')]"
        )

        if len(day_elements) < 1:
            raise Exception("No entree for today.")

        if len(day_elements) > 1:
            raise Exception("More than one element matched for today's date!")

        return normalize_redirect_url(r.url, day_elements[0].get('href'))

    assignment_url = pick_date(dates_tree)
    logging.info(assignment_url)
    r = session.get(assignment_url)
    assignment_tree = etree.HTML(r.text)

    def pick_homework(tree: etree.ElementTree) -> list[etree.Element]:
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

    def prune_tree(tree: etree._Element) -> etree._Element | None:
        children = tree.xpath('./*')
        if len(children) == 0:
            return None
        for child in children:
            if isinstance(child, etree._Element):
                replaced = prune_tree(child)
                if replaced is not None:
                    tree.replace(child, replaced)
                else:
                    tree.remove(child)
            elif isinstance(child, str) and len(child.strip()) == 0:
                tree.remove(child)
        return tree

    assignment_text = ""
    for e in pick_homework(assignment_tree):
        assignment_text += etree.tostring(e).decode('utf8') + '\n'
    assignment_text = html.unescape(assignment_text)
    print(assignment_text)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # ? You get these classes from the 'id' query param in the class homepage url
    inspect_class_ids = [ 1154, 1446, 433, 1468, 56 ]

    f = open('credentials', 'r')
    username, password, *_ = f.read().split('\n')
    print("Using", username, password)

    session = get_session(username, password)
    for i in inspect_class_ids:
        try:
            get_lesson_plans(session, i)
        except Exception as e:
            logging.error(str(e))
