import http.client as http_client
import logging

import requests
from lxml import etree

from xpath_utils import text_without_accessibility

def enable_debug_http():
    #? HTTP Debugging
    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def get_session(username: str, password: str) -> requests.Session:
    login_page_req = requests.get(
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
            'Cookie': 'MoodleSessionprod=1986a9d6be71745a5ef179b928f1699f; intelliboardPage=site; intelliboardParam=1; intelliboardTime=3',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }
    )
    tree = etree.HTML(login_page_req.text)
    logintoken = tree.xpath("//input[@name='logintoken']")[0].get('value')

    logging.info(f'logintoken {logintoken}')
    logging.info(f'cookies {login_page_req.cookies.get_dict()}')

    login_post = requests.post(
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
        cookies=login_page_req.cookies.copy(),
        allow_redirects=False,
    )

    logging.info(f'Session {login_post.cookies.get("MoodleSessionprod")}')
    # assert login_post.cookies.get('MOODLEID1_prod')

    session = requests.Session()
    session.cookies = login_post.cookies.copy()
    # session.cookies.set('MoodleSessionprod', 'aee0646be17e092bd1b5d1b93db63a43')

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
        for name in tree.xpath(f"//li[contains(@class, 'modtype_book')]{text_without_accessibility}"):
            print(name)

    pick_quarter(quarter_tree)


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
    get_lesson_plans(session, 1154)
