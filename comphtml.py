from bs4 import BeautifulSoup
import logging
import re

class CompHTML:

    def __init__(self, soup):
        self.soup = soup

    def __str__(self):
        # return str(self.soup)
        return self.soup.prettify()

