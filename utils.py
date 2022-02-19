import http.client as http_client
import logging
from urllib.parse import urlparse, urlunparse

from lxml import etree

text_without_accessibility = "//text()[not(ancestor::span[contains(@class, 'accesshide')])]"
htag_selector = '*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]'
htags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

def join_paths(p1: str, p2: str) -> str:
    sp1, sp2 = p1.split('/'), p2.split('/')
    try:
        sp1.remove(''); sp2.remove('')
    except ValueError:
        pass
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
        if element.text is None:
            return None
        elif len(element.text.strip()) == 0:
            return None
    for child in element:
        match child:
            case etree._Element():
                replaced = prune_tree(child)
                if replaced is not None:
                    element.replace(child, replaced)
                else:
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
