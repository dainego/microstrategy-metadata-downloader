import logging
from pathlib import Path
import csv
import json

def setup_logger(
    name: str,
    log_file: Path | str,
    level: int = logging.INFO
) -> logging.Logger:

    """
    Create a logger that writes messages to both the console
    and a log file.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if the logger is initialized again
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Log to File
    if log_file:
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

#Function to clean text by removing line breaks, tabs, and repeated whitespace
def clean_text(value: str | None) -> str | None:
    """
    Remove line breaks, tabs, and repeated whitespace from text.
    """

    if value is None:
        return None

    return " ".join(value.split())

# Function to write JSON data to a file
def write_json_to_file(data, file_path, indent=4):
   
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=indent,
            ensure_ascii=False
        )

# Function to write JSON data to a CSV file
def write_to_csv(data, file_path):

    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=data[0].keys()
        )

        writer.writeheader()
        writer.writerows(data)

def write_to_text(data, file_path, separator="|"):
    if not data:
        return

    fieldnames = data[0].keys()

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        # Header
        file.write(
            separator.join(fieldnames) + "\n"
        )

        # Rows
        for row in data:
            values = [
                "" if row.get(field) is None else str(row.get(field))
                for field in fieldnames
            ]

            file.write(
                separator.join(values) + "\n"
            )

def parse_folder(folder):
    root_parts = ["Schema Objects", "Attributes"]

    result = {
        "model": None,
        "submodel": None,
        "submodel1": None,
        "submodel2": None,
        "submodel3": None
    }

    if not folder:
        return result

    # Divide la ruta y elimina componentes vacíos
    parts = [
        part.strip()
        for part in folder.replace("\\", "/").split("/")
        if part.strip()
    ]

    # Elimina la raíz Schema Objects/Attributes, si está presente
    if parts[:2] == root_parts:
        parts = parts[2:]

    field_names = [
        "model",
        "submodel",
        "submodel1",
        "submodel2",
        "submodel3"
    ]

    for field_name, value in zip(field_names, parts):
        result[field_name] = value

    return result