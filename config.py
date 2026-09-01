import os
from pathlib import Path
from dotenv import load_dotenv

# Env variables
BASE_FOLDER = Path(__file__).resolve().parent
ENV_FILE = BASE_FOLDER / ".env"

load_dotenv(ENV_FILE)


BASE_URL = os.getenv("MSTR_BASE_URL")
ACCOUNT_ID = os.getenv("MSTR_USERNAME")
ACCOUNT_PASSWORD = os.getenv("MSTR_PASSWORD")

# Paths
APP_NAME = "microstrategy-metadata-downloader"
LOG_FOLDER = BASE_FOLDER / "logs"
RESULTS_FOLDER = BASE_FOLDER / "results"

LOG_FOLDER.mkdir(parents=True, exist_ok=True)
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)


# MicroStrategy object types
OBJECT_TYPE_ATTRIBUTE = 12
OBJECT_SUBTYPE_ATTRIBUTE = 3072
OBJECT_TYPE_METRIC = 4
OBJECT_TYPE_FILTER = 1
OBJECT_TYPE_FACT = 13


# Project configuration
PROJECTS = {
    "1": {
        "name": "Big Data",
        "project_id": "86B8BBB711E8A19F0A290080EF251385",
        "attribute_root": "6F55FB47F9974EABA18CB0C5FF46785C"
    },
    "2": {
        "name": "MUC",
        "project_id": "B32C690C11EAEDFDC5090080EF35D25D",
        "attribute_root": "6F55FB47F9974EABA18CB0C5FF46785C"
    }
}

