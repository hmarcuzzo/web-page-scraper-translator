import os

from dotenv import load_dotenv


load_dotenv()

# --------------- DEFAULT APP CONFIGURATION --------------- #
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------- MS TRANSLATOR CONFIG --------------- #
MS_TRANSLATOR_KEY = os.getenv("MS_TRANSLATOR_KEY")
MS_TRANSLATOR_ENDPOINT = os.getenv("MS_TRANSLATOR_ENDPOINT")
MS_TRANSLATOR_REGION = os.getenv("MS_TRANSLATOR_REGION")
