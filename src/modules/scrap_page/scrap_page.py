import logging
import os
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import ROOT_DIR
from src.core.constants.default_values import DEFAULT_DEPTH_LEVEL
from src.core.constants.regex_expressions import LINK_PATTERN


class ScrapPage:
    def __init__(
        self, url: str, depth_level: int = DEFAULT_DEPTH_LEVEL, path: str = "/static/pages"
    ):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.36"
        }

        self.url = url
        self.page = requests.get(self.url, headers=headers)
        self.soup = BeautifulSoup(self.page.content, "html.parser")

        self.depth_level = depth_level
        self.path = path

    # -------------------- PUBLIC METHODS --------------------
    def save_page(self) -> None:
        self.__save_referenced_pages()
        self.__save_html()

    # -------------------- PRIVATE METHODS --------------------
    def __get_file_name(self, url: str = None) -> str:
        if url is None:
            url = self.url
        parsed_url = urlparse(url)

        path_url = "/index" if os.path.basename(parsed_url.path).strip() == "" else parsed_url.path
        file_name = parsed_url.hostname.split(".")[1] + path_url
        return (ROOT_DIR + os.path.join(self.path, file_name)).strip()

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

            if self.__page_exists(url):
                continue

            scrap_page = ScrapPage(url, self.depth_level + 1)
            scrap_page.save_page()

    def __page_exists(self, url: str) -> bool:
        file_name = self.__get_file_name(url) + ".html"
        return os.path.exists(file_name)
