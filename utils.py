from urllib.parse import urlparse, urlunparse

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
