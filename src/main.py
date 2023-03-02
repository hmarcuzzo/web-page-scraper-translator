import logging

from src.core.constants.default_values import SCRAP_URL
from src.modules.scrap_page.scrap_page import ScrapPage


if __name__ == "__main__":
    # configure the logger
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    scrap_page = ScrapPage(SCRAP_URL)
    scrap_page.save_page()
