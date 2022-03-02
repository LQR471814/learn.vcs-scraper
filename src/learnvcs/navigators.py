import traceback
from datetime import datetime

import requests
from lxml import etree

from learnvcs.utils import (cut, normalize_redirect_url, strip_lists,
                            text_without_accessibility)


class DateFormatError(Exception):
    def __init__(self, error: Exception, date: datetime, url: str) -> None:
        super().__init__(
            f'Invalid date format!\n'
            f'{error}\n{traceback.format_exc()}'
            f"{date.month}/{date.day} URL {url}"
        )

class NoEntreeError(Exception):
    def __init__(self) -> None:
        super().__init__("No entree for today.")


class NavigationConfig:
    date: datetime

    def __init__(self, date: datetime = None) -> None:
        self.date = date


class Navigator:
    url: str
    tree: etree._ElementTree
    config: NavigationConfig

    def __init__(
        self, url: str,
        session: requests.Session,
        config: NavigationConfig | None,
        tree: etree._ElementTree = None,
    ) -> None:
        self.url = url
        self.tree = etree.HTML(session.get(url).text)
        self.config = config if config is not None else NavigationConfig()

    def evaluate(self):  # ? This should return another navigator
        raise Exception("cannot run unimplemented function!")


class HomepageNavigator(Navigator):
    def evaluate(self) -> str | None:
        return self.tree.xpath("//a[contains(@title, 'Homework')]")[0].get('href')


class QuarterNavigator(Navigator):
    def __init__(
        self, url: str | None,
        session: requests.Session,
        config: NavigationConfig | None,
        tree: etree._ElementTree = None
    ) -> None:
        if url is None:
            self.tree = tree
        else:
            super().__init__(url, session, tree)

    def evaluate(self) -> str:
        number = 0
        for name in self.tree.xpath(f"//li[contains(@class, 'modtype_book')]{text_without_accessibility}"):
            split_name = name.split(' ')
            if int(split_name[1]) > number:
                number = int(split_name[1])
        return self.tree.xpath(
            f"//a[@class='aalink'][.//*[contains(text(), 'Quarter {number}')]]"
        )[0].get('href')


class DateNavigator(Navigator):
    month_map: dict[int, str] = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    month_map_inverse: dict[str, int] = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def evaluate(self) -> str:
        date = self.config.date
        if date is None:
            date = datetime.now()

        date_elements = self.tree.xpath(
            "//div[contains(@class, 'card-body')]"
            "/h5[contains(text(), 'Table of contents')]"
            "/following-sibling::div//li"
        )

        link = None

        for date_entry in date_elements:
            try:
                date_text = ''.join(date_entry.xpath('.//text()'))
                date_segments = strip_lists(cut(cut([date_text], '/'), ' '))

                valid_dates: list[datetime] = []
                last_month = None

                for segment in date_segments:
                    if segment[:3] in self.month_map.values():
                        last_month = self.month_map_inverse[segment[:3]]
                        continue
                    try:
                        day = int(segment)
                        if last_month is not None:
                            valid_dates.append(datetime(date.year, last_month, day))
                        else:
                            raise DateFormatError(
                                Exception("Last month reported was None!"),
                                date, self.url
                            )
                    except ValueError:
                        pass

                valid = False
                for d in valid_dates:
                    if date.month == d.month and date.day == d.day:
                        valid = True
                        break

                if valid:
                    if date_entry.xpath('.//a') is None:
                        link = self.url
                        break
                    link = date_entry.xpath('./a')[0].get('href')
                    break
            except Exception as err:
                raise DateFormatError(err, date, self.url)

        if link is None:
            raise NoEntreeError()

        return normalize_redirect_url(self.url, link)
