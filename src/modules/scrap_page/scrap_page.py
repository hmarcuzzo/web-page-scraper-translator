import logging
import os
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver

from config import ROOT_DIR
from src.core.constants.default_values import DEFAULT_DEPTH_LEVEL
from src.core.constants.regex_expressions import LINK_PATTERN


class ScrapPage:
    def __init__(
        self, url: str, depth_level: int = DEFAULT_DEPTH_LEVEL, path: str = "/static/pages"
    ):
        # wait 1 second to avoid being blocked by the server
        time.sleep(1)

        self.depth_level = depth_level
        self.path = path

        self.url = url

        browser = webdriver.Chrome()
        browser.get(url)

        self.__scroll_down_page(browser)

        self.page = browser.page_source
        self.soup = BeautifulSoup(self.page, "html.parser")

    # -------------------- PUBLIC METHODS --------------------
    def save_page(self) -> None:
        self.__save_referenced_pages()
        self.__save_html()

    # -------------------- PRIVATE METHODS --------------------
    def __get_file_name(self, url: str = None) -> str:
        if url is None:
            url = self.url
        parsed_url = urlparse(url)

        file_name = f"{parsed_url.hostname.split('.')[1]}{parsed_url.path or '/'}".strip()
        if file_name.endswith("/"):
            file_name += "index"

        file_name = os.path.join(self.path, file_name)

        return ROOT_DIR + file_name

    def __save_html(self) -> None:
        file_name = self.__get_file_name()

        dir_path = os.path.dirname(file_name)
        os.makedirs(dir_path, exist_ok=True)

        file_path = file_name + ".html"
        with open(file_path, "w") as f:
            f.write(self.soup.prettify())
            logging.info(f"File saved: {file_path}")

    def __save_referenced_pages(self) -> None:
        if self.depth_level == 0 or self.depth_level > DEFAULT_DEPTH_LEVEL:
            return

        for link in self.soup.find_all("a", href=LINK_PATTERN):
            url = link.get("href")

            if url.startswith("/"):
                url = self.url + url

            self.__link_to_local_file(link, url)

            if self.__should_ignore_url(url):
                continue

            scrap_page = ScrapPage(url, self.depth_level + 1)
            scrap_page.save_page()

    def __should_ignore_url(self, url: str) -> bool:
        file_name = self.__get_file_name(url) + ".html"

        base_url = urlparse(self.url).hostname.split(".")[1]
        link_base_url = urlparse(url).hostname.split(".")[1]
        if base_url != link_base_url or f"{base_url}/index.html" in file_name:
            return True

        return os.path.exists(file_name)

    def __link_to_local_file(self, link: Tag, url: str) -> None:
        domain_name = str(urlparse(url).hostname).split(".")[1]

        new_url = self.__get_file_name(url) + ".html"
        new_url = "." + new_url.replace(f"{ROOT_DIR}{self.path}/{domain_name}", "", 1)
        link["href"] = new_url

    @staticmethod
    def __scroll_down_page(browser, speed: int = 50):
        current_scroll_position, new_height = 0, 1
        while current_scroll_position <= new_height:
            current_scroll_position += speed
            browser.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
            new_height = browser.execute_script("return document.body.scrollHeight")
