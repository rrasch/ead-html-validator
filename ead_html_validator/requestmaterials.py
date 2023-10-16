from bs4 import BeautifulSoup
from typing import List
import re


class RequestMaterials:
    def __init__(self, html_file, parser="html5lib"):
        self.soup = BeautifulSoup(
            open(html_file), parser, multi_valued_attributes=None
        )
        self.html_file = html_file

    def find_links(self) -> List[str]:
        return [
            a.get("href")
            for a in self.soup.find_all(
                lambda tag: tag.name == "a"
                and re.search(r"request", tag.parent.get("class", ""))
            )
        ]
