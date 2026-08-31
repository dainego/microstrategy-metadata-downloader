import logging

#Function to set up logging
def setup_logger(name="app", log_file=None, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optionally log to file
    if log_file:
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

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

