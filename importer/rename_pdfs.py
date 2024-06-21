"""Rename PDF files in a directory based on their filename."""

import re
from pathlib import Path

# Define the directory containing the PDFs
directory = Path("../pdf_downloads")  # Adjust the path to the pdf_downloads directory

# Define a regular expression to match the current filenames
pattern = re.compile(r"Bon Ã  Savoir_(\d{2})_(\d{4}).pdf")

# Iterate over all files in the directory
for filepath in directory.iterdir():
    if filepath.is_file():
        match = pattern.match(filepath.name)
        if match:
            # Extract the month and year from the filename
            month = match.group(1)
            year = match.group(2)

            # Create the new filename
            new_filename = f"bon_a_savoir_{year}_{month}.pdf"

            # Construct the full new file path
            new_filepath = directory / new_filename

            # Rename the file
            filepath.rename(new_filepath)
            print(f"Renamed: {filepath.name} -> {new_filename}")
        else:
            print(f"Skipped: {filepath.name}")
