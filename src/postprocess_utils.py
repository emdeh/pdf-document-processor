import pandas as pd
import fitz # PyMuPDF
import re
import os
import shutil
from pathlib import Path
from datetime import datetime
import string
import math

class ExcelHandler:
    """
    A class to handle reading and writing of Excel files.
    """
    # Registry of tasks list
    task_registry = {
        'fill_missing_dates': {
            'func': 'fill_missing_dates',
            'description': 'Fill missing dates in the "Date" column by propagating the last known date downward.'
        },
        'another_task': {
            'func': 'another_task',
            'description': 'Description of another task.'
        },
        'yet_another_task': {
            'func': 'yet_another_task',
            'description': 'Description of yet another task.'
        }
        # Add more tasks here
    }

    def __init__(self, file_path):
        self.file_path = file_path
        self.summary_df = None
        self.transactions_df = None
        self._load_excel_file()

    def _load_excel_file(self):
        """Loads the Excel file into DataFrames."""
        print(f"Loading Excel file: {self.file_path}")
        excel_file = pd.ExcelFile(self.file_path)
        self.summary_df = pd.read_excel(excel_file, sheet_name='Summary')
        self.transactions_df = pd.read_excel(excel_file, sheet_name='Transactions')

    def save(self, output_file):
        """Saves the DataFrames back to an Excel file."""
        print(f"Saving to: {output_file}")
        with pd.ExcelWriter(output_file, 
                            engine='xlsxwriter',
                            datetime_format="DD/MM/YYYY",
                            date_format="DD/MM/YYYY",
                            ) as writer:
            self.summary_df.to_excel(writer, sheet_name='summary', index=False)
            self.transactions_df.to_excel(writer, sheet_name='transactions', index=False)

    @staticmethod
    def fill_missing_dates(transactions_df, **kwargs):
        """
        Fills missing dates in the 'Date' column by propagating the last known date downward.
        A new column 'Date_Processed' is created for the processed dates and placed next to the original 'Date' column.

        Args:
            transactions_df (pd.DataFrame): DataFrame containing transaction data.

        Returns:
            pd.DataFrame: Updated DataFrame with missing dates filled.
        """
        print("Filling missing dates in the 'Date' column...")

        # Ensure the 'Date' column is in datetime format (without time component)
        #transactions_df['Date_Processed'] = pd.to_datetime(transactions_df['Date'], errors='coerce').dt.normalize()

        # Forward-fill missing dates
        #transactions_df['Date_Processed'] = transactions_df['Date'].ffill()

         # Forward-fill missing dates within each statement, but grouped by statement name to stop the transform from overflowing dates
         # from the preceding statement, when a statement's first transaction is missing a date.
        transactions_df['Date_Processed'] = transactions_df.groupby('OriginalFileName')['Date'].transform(lambda group: group.ffill())

        #transactions_df['Date_Processed'] = pd.to_datetime(transactions_df)['Date_Processed']

        # Reorder the columns to place 'Date_Processed' next to 'Date'
        columns = transactions_df.columns.tolist()
        date_idx = columns.index('Date')
        columns.insert(date_idx + 1, columns.pop(columns.index('Date_Processed')))
        transactions_df = transactions_df[columns]

        # Reset the index to ensure proper ordering
        transactions_df.reset_index(drop=True, inplace=True)

        return transactions_df
    # TODO: The date formatting is partially duplicated from write_transactions_and_summaries_to_excel in csv_utils.py. Consider refactoring to a common function.

class PDFPostProcessor:
    """
    A class to handle post-processing of PDF files..
    """
    # Registry of PDF tasks
    task_registry = {
        'categorise_by_value': {
            'func': 'categorise_by_value',
            'description': 'Categorise PDF statements into folders based on a specified value pattern.'
        },
        'add_date_prefix_to_filenames': {
            'func': 'add_date_prefix_to_filenames',
            'description': 'Add statement start date as prefix to PDF filenames for chronological ordering.'
        },
        'identify_and_move_duplicates': {
            'func': 'identify_and_move_duplicates',
            'description': 'Identify duplicate statements and move them to a duplicates folder.'
        }
        # Add more tasks here as needed
    }

    def __init__(self, input_folder):
        self.input_folder = input_folder
        self.pdf_files = list(Path(input_folder).glob("*.pdf"))

    def categorise_by_value(self):
        """
        Categorise PDF statements into folders based on a value pattern derived from a provided example.
        """
        # TODO: Instead of prompting for an example, consider storing in yaml and calling from there.
        field_name = input("Please enter a name for the field (e.g., 'Account Number', 'Statement ID'):\n")
        print(f"Categorising PDF statements by {field_name}...")

        # Prompt the user for an example value
        value_example = input(f"Please enter an example of the {field_name} value (e.g., '123-456-789'):\n")

        # Generate the value pattern based on the example
        pattern = self.generate_regex_from_value_example(value_example)
        if not pattern:
            print("Pattern generation failed. Exiting task.")
            return

        print(f"Generated value pattern: {pattern}\n")

        for pdf_file in self.pdf_files:
            pdf_path = str(pdf_file)
            extracted_value = self.extract_value_from_pdf(pdf_path, pattern)
            if extracted_value:
                # Construct folder name using the field name and extracted value
                sanitised_field_name = self.sanitise_folder_name(field_name.replace(" ", ""))
                sanitised_value = self.sanitise_folder_name(extracted_value)
                folder_name = f"{sanitised_field_name}-{sanitised_value}"
                folder_path = os.path.join(self.input_folder, folder_name)
                os.makedirs(folder_path, exist_ok=True)

                # Rename the file to include the extracted value
                # This renaming part is purposely kept seperate from the prefix_date function so that function can
                # be called independently from the task registry specifically for date prefixes.
                new_filename = (f"{sanitised_field_name}-{sanitised_value}-{pdf_file.name}")
                print(f"File {pdf_file.name} renamed to {new_filename}")
                destination = os.path.join(folder_path, new_filename)

                # Move and rename the file                
                shutil.move(pdf_path, destination)
                print(f"Moved to Folder: {sanitised_value}")
            else:
                print(f"Value not found in {pdf_file.name}")

    def generate_regex_from_value_example(self, value_example):
        """
        Generates a regex pattern based on a value example.

        Args:
            value_example (str): An example of the value to generate the pattern from.

        Returns:
            str: The generated regex pattern.
        """
        pattern = ''
        i = 0
        value_example = value_example.strip()
        while i < len(value_example):
            c = value_example[i]
            if c.isdigit():
                # Start of a digit sequence
                j = i
                while j < len(value_example) and value_example[j].isdigit():
                    j += 1
                num_digits = j - i
                # Append \d{n}
                pattern += r'\d{' + str(num_digits) + r'}'
                i = j
            elif c.isalpha():
                # Start of a letter sequence
                j = i
                while j < len(value_example) and value_example[j].isalpha():
                    j += 1
                num_letters = j - i
                # Append [A-Za-z]{n}
                pattern += r'[A-Za-z]{' + str(num_letters) + r'}'
                i = j
            elif c.isspace():
                # Handle whitespace
                pattern += r'\s+'
                i += 1
                # Skip additional whitespace
                while i < len(value_example) and value_example[i].isspace():
                    i += 1
            else:
                # Special character
                # Escape special regex characters
                pattern += re.escape(c)
                i += 1
        # Make the pattern case-insensitive
        pattern = f"(?i){pattern}"
        return pattern

    def extract_value_from_pdf(self, pdf_path, pattern):
        """
        Extracts a value from a PDF using a regex pattern..

        Args:
            pdf_path (str): The path to the PDF file.
            pattern (str): The regex pattern to search for.

        Returns:
            str: The extracted value.

        Explanation of the "for block in page_dict['blocks']" loop:
        (Full disclosure, I needed ChatGPT to help me with this.)

        **Text Orientation Filtering:**

        We use the bounding box dimensions (`'bbox'`) of each text span to determine its orientation.
        By comparing the width and height of the bounding box, we can infer the text direction.
        - If the **width** is greater than the **height**, the text is considered **horizontal**.
        - If the **height** is greater than or equal to the **width**, the text is likely **vertical** or rotated.
        We include only the text spans where `width > height`, effectively filtering out vertical or rotated text.

        This excludes any text that is on the side and not left-to-right.

        **Limiting the Search Area:**

        We obtain the `'bbox'` (bounding box) of each span to get its vertical position on the page.
        By comparing the y-coordinates (`y0`, `y1`) to the page height, we can limit the text to the top portion of the page.
        We adjust the proportion (e.g., `0.2` for 20%) as needed based on the document layout.

        **Accumulating Text:**

        Then we concatenate the text from the desired spans into a single string.
        This text is then used for pattern matching.

        Wow.
        """
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_height = page.rect.height

            # Get text as a dictionary
            page_dict = page.get_text("dict")  # Use "dict"

            for block in page_dict["blocks"]:
                # Process only text blocks
                if block["type"] == 0:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            bbox = span["bbox"]
                            x0, y0, x1, y1 = bbox
                            width = x1 - x0
                            height = y1 - y0

                            # If width is greater than height, consider it horizontal text
                            if width > height:
                                # Optionally, limit to a specific area (e.g., top 20% of the page)
                                if y1 < page_height * 0.2:
                                    text += span["text"] + " "
                            else:
                                # Skip vertical or rotated text
                                continue

        doc.close()
        # Normalize whitespace in text
        text = re.sub(r'\s+', ' ', text)
        # Search for the pattern
        matches = re.findall(pattern, text)
        if matches:
            # If multiple matches are found, return the first match
            return matches[0].strip()
        return None

    def sanitise_folder_name(self, name):
        """
        Sanitises the folder name by removing or replacing invalid characters.
        """
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        sanitised_name = ''.join(c for c in name if c in valid_chars)
        return sanitised_name

    def format_date(self, date_str):
        """
        Formats a date string extracted from a PDF.

        Args:
            date_str (str): The date string to format.

        Returns:
            str: The formatted date.
        """
        pass

    @staticmethod
    def add_date_prefix_to_filenames(self):
        """
        Add statement start date as prefix to PDF filenames for chronological ordering.
        """
        pass

    @staticmethod
    def identify_and_move_duplicates(self):
        """
        Identify duplicate statements and move them to a duplicates folder.
        """
        pass
