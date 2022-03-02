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


def prune_tree(element: etree._Element) -> etree._Element | None:
    if len(list(element)) == 0:
        if element.tail is not None and len(element.tail.strip()) > 0:
            return element.tail
        if element.text is None:
            return None
        elif len(element.text.strip()) == 0:
            return None
    for child in element:
        match child:
            case etree._Element():
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
            case str():
                if len(child.strip()) == 0:
                    element.remove(child)
    return element


def enable_debug_http():
    # ? HTTP Debugging
    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
