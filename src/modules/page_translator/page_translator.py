import datetime
import glob
import logging
import os
import shutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment, NavigableString

from config import MS_TRANSLATOR_ENDPOINT, MS_TRANSLATOR_KEY, MS_TRANSLATOR_REGION, ROOT_DIR
from src.core.constants.default_values import TARGET_LANGUAGE


class PageTranslator:
    def __init__(
        self,
        url: str,
        from_language: str = "",
        target_lang: str = TARGET_LANGUAGE,
        path: str = "/static/pages",
    ):
        self.constructed_url = urljoin(MS_TRANSLATOR_ENDPOINT, "/translate")

        self.params = {"api-version": "3.0", "from": from_language, "to": [target_lang]}
        self.headers = {
            "Ocp-Apim-Subscription-Key": MS_TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": MS_TRANSLATOR_REGION,
            "Content-type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }

        self.files = self.__get_files_of_type(url, path)

    # -------------------- PUBLIC METHODS --------------------
    def translate_files(self, files: List[str] = None) -> None:
        if files is None:
            files = self.files

        def translate_file(file: str) -> None:
            if os.path.exists(file + ".backup"):
                return

            start = time.time()
            logging.info(f"Translating file: {file}...")

            with open(file, "r") as fr:
                soup = BeautifulSoup(fr.read(), "html.parser")
                texts = self.__text_from_html(soup)

                self.__translate_texts(texts)

                shutil.copyfile(file, file + ".backup")
                with open(file, "w") as fw:
                    fw.write(soup.prettify())
                    logging.info(
                        f"File translated: {file} in {str(datetime.timedelta(seconds=time.time() - start))}"
                    )

        # with ThreadPoolExecutor() as executor:
        #     executor.map(translate_file, files)

        for f in files:
            translate_file(f)

    # -------------------- PRIVATE METHODS --------------------
    @staticmethod
    def __get_files_of_type(url: str, path: str, file_type: str = ".html") -> List[str]:
        parsed_url = urlparse(url)
        website_name = parsed_url.hostname.split(".")[1] + parsed_url.path
        directory = ROOT_DIR + os.path.join(path, website_name)

        return [
            file
            for file in glob.glob(os.path.join(directory, "**", f"*{file_type}"), recursive=True)
        ]

    def __translate_texts(self, texts: List[NavigableString]) -> None:
        def translate_text(element: NavigableString) -> None:
            text = element.strip()

            body = [{"text": element.strip()}]
            response = requests.post(
                self.constructed_url,
                params=self.params,
                headers=self.headers,
                json=body,
            )
            response.raise_for_status()

            translation = response.json()[0]["translations"][0]["text"]
            element.replace_with(translation)

        with ThreadPoolExecutor() as executor:
            executor.map(translate_text, texts)

    @staticmethod
    def __tag_visible(element):
        if element.parent.name in ["style", "script", "head", "title", "meta", "[document]"]:
            return False
        if isinstance(element, Comment):
            return False
        return True

    def __text_from_html(self, soup: BeautifulSoup) -> List[NavigableString]:
        texts = soup.findAll(text=True)

        visible_texts = filter(self.__tag_visible, texts)
        filtered_texts = filter(lambda t: t.strip(), visible_texts)

        return list(filtered_texts)
