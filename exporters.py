
import csv
import json


def write_to_json(data, file_path, indent=4):
    """
    Writes JSON data to a file.
    """

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=indent,
            ensure_ascii=False
        )


def write_to_csv(data, file_path):
    """
    Writes JSON data to a CSV file.
    """

    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=data[0].keys()
        )

        writer.writeheader()
        writer.writerows(data)


def write_to_text(data, file_path, separator="|"):
    """
    Writes JSON data to a text file with a specified separator.
    """

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