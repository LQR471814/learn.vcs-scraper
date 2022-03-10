import html
import http.client as http_client
import logging
import re
import unicodedata
from urllib.parse import urlparse, urlunparse

from lxml import etree

root = 'https://learn.vcs.net'
text_without_accessibility = "//text()[not(ancestor::span[contains(@class, 'accesshide')])]"
htag_selector = '*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]'
lowered_text = "translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
#? Will select (case-insensitive if specified) current text and any children nodes that contain given keyword
deep_text_search = lambda s, t = '*', lowered = False: (
    f"[contains({lowered_text if lowered else 'text()'}, '{s}') or "
    f".//{t}[contains({lowered_text if lowered else 'text()'}, '{s}')]]"
)
inner_whitespace = re.compile(r'\s\s+')


def normalize_text(text: str) -> str:
    return inner_whitespace.sub(
        ' ', normalize_html_text(text)
    ).strip()


def normalize_html_text(text: str) -> str:
    return html.unescape(unicodedata.normalize('NFKD', text))


def cut(text: list[str], target: str) -> list[str]:
    result = []
    for s in text:
        for p in s.split(target):
            result.append(p)
    return result


def strip_lists(sources: list | list[list], targets: list[any] = None) -> list:
    if targets is None:
        targets = ['']

    for t in targets:
        try:
            for l in sources:
                if l in targets:
                    sources.remove(l)
                elif isinstance(l, list):
                    l.remove(t)
        except ValueError:
            pass

    return sources


def join_paths(p1: str, p2: str) -> str:
    sp1, sp2 = p1.split('/'), p2.split('/')
    strip_lists([sp1, sp2])
    return '/'.join(sp1 + sp2)


def normalize_redirect_url(request_url: str, fragment: str) -> str:
    base = urlparse(request_url)
    url = urlparse(fragment)
    return urlunparse(
        url._replace(
            scheme='http' if not base.scheme else base.scheme,
            netloc=base.netloc,
            path=join_paths(base.path, url.path),
            query=url.query
        )
    )


# ? Will go up ancestry of element until finding a valid next sibling
def get_next(element: etree._Element) -> etree._Element | None:
    sibling = element.getnext()
    while sibling is None:
        element = element.xpath('./..')
        if element is None or len(element) == 0:
            return None
        element = element[0]
        sibling = element.getnext()
    return sibling

# ? Pruning Algorithm:
# ?   element mutations
# ?    - Will remove child if prune child returns None
# ?    - Will remove child and append text to 'text' attribute if prune child returns str
# ?    - Will replace child with another child if prune child returns _Element
# ?   prune returns
# ?    - Will return None if element has no text or children
# ?    - Will return str if element has tail text and no children
# ?    - Will return _Element if none of the above are fulfilled


def prune_tree(element: etree._Element) -> etree._Element | str | None:
    child_nodes = element.xpath('./*')
    for child in [] if child_nodes is None else child_nodes:
        replaced = prune_tree(child)
        match replaced:
            case etree._Element():
                element.replace(child, replaced)
            case str():
                if element.text is None:
                    element.text = ''
                element.text += replaced
                element.remove(child)
            case None:
                element.remove(child)

    text = '' if element.text is None else element.text
    if len(text.strip()) == 0 and len(element) == 0:
        tail = '' if element.tail is None else element.tail
        if len(tail.strip()) > 0:
            return tail
        return None

    return element


def enable_debug_http():
    # ? HTTP Debugging
    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
