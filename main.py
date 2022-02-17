from datetime import datetime
import http.client as http_client
import logging

import requests
from lxml import etree

from utils import normalize_redirect_url, text_without_accessibility, htag_selector, htags

def enable_debug_http():
    #? HTTP Debugging
    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def get_session(username: str, password: str) -> requests.Session:
    session = requests.Session()
    login_page_req = session.get(
        'https://learn.vcs.net/login/index.php',
        headers={
            'Host': 'learn.vcs.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://learn.vcs.net/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }
    )

    tree = etree.HTML(login_page_req.text)
    logintoken = tree.xpath("//input[@name='logintoken']")[0].get('value')

    login_post = session.post(
        'https://learn.vcs.net/login/index.php',
        headers={
            'Host': 'learn.vcs.net',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': '96',
            'Origin': 'https://learn.vcs.net',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://learn.vcs.net/login/index.php',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        },
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
            params={ 'id': class_id }
        )
        tree = etree.HTML(r.text)
        with open('debug', 'w') as f: f.write(r.text)
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
            1: 'January',
            2: 'February',
            3: 'March',
            4: 'April',
            5: 'May',
            6: 'June',
            7: 'July',
            8: 'August',
            9: 'September',
            10: 'October',
            11: 'November',
            12: 'December'
        }

        day_link = tree.xpath(
            "//li/*[contains(text(), '"
            f"{month_map[datetime.now().month]} {datetime.now().day}"
            "')]"
        )[0]

        return normalize_redirect_url(r.url, day_link.get('href'))

    assignment_url = pick_date(dates_tree)
    logging.info(assignment_url)
    r = session.get(assignment_url)
    assignment_tree = etree.HTML(r.text)

    def pick_homework(tree: etree.ElementTree) -> list[etree.Element]:
        collecting = False
        collection = []

        for e in tree.xpath("//div[@class='no-overflow']/*"):
            if e.tag in htags:
                collecting = 'homework' in ''.join(e.xpath('//text()')).lower()
                continue
            if collecting:
                collection.append(e)

        return collection

    for e in pick_homework(assignment_tree):
        print(etree.tostring(e))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    #? You get these classes from the 'id' query param in the class homepage url
    inspect_class_ids = [
        1154,
        1446,
        433,
        1468,
        56,
    ]

    f = open('credentials', 'r')
    username, password, *_ = f.read().split('\n')
    print("Using", username, password)

    session = get_session(username, password)
    get_lesson_plans(session, 433)
