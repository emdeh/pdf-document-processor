import pandas as pd
import fitz # PyMuPDF
import re
import os
import shutil
from pathlib import Path
from datetime import datetime
import string

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
    A class to handle post-processing of PDF files.
    """
    # Registry of PDF tasks
    task_registry = {
        'categorise_by_field': {
            'func': 'categorise_by_field',
            'description': 'Categorise PDF statements into folders based on a specified field.'
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

    def categorise_by_field(self):
        """
        Categorise PDF statements into folders based on a specified field.
        """
        field_name = input("Please enter the field name to categorise by as it appears on the statement (e.g., 'Account Number', 'Statement Number'):\n")
        print(f"Categorising PDF statements by {field_name}...")
        example = input(f"Please enter an example of how the {field_name} value appears in the statement, including the field name. For example Account Number: 123 (not just 123):\n")
        pattern = self.generate_regex_from_example(field_name, example)
        if not pattern:
            print("Pattern generation failed. Exiting task.")
            return

        for pdf_file in self.pdf_files:
            pdf_path = str(pdf_file)
            extracted_value = self.extract_field(pdf_path, pattern)

            if extracted_value:
                # Construct folder name using the field name and extracted value
                sanitised_field_name = self.sanitise_folder_name(field_name.replace(" ", ""))
                sanitised_value = self.sanitise_folder_name(extracted_value)
                folder_name = f"{sanitised_field_name}-{sanitised_value}"
                folder_path = os.path.join(self.input_folder, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                
                # Move file
                destination = os.path.join(folder_path, pdf_file.name)
                shutil.move(pdf_path, destination)
                print(f"Moved {pdf_file.name} to {folder_path}")
            else:
                print(f"{field_name} not found in {pdf_file.name}")

    def generate_regex_from_example(self, field_name, example):
        """
        Generates a regex pattern from the field name and a user-provided example.

        Args:
            field_name (str): The name of the field to extract.
            example (str): An example of how the field appears in the statement. (INCLUDING THE FIELD NAME)

        Returns:
            str: The generated regex pattern.
        """
        # Escape field name and example
        escaped_field_name = re.escape(field_name.strip())
        escaped_example = re.escape(example.strip())

        # Check if field name is present in the example
        field_pos = escaped_example.lower().find(escaped_field_name.lower())
        if field_pos == -1:
            print("The field name was not found in your example. Please provide an example that includes the field name as it appears in the statement.")
            return None

        # Find the variable part in the example
        # We assume the variable part is the sequence of alphanumeric characters that is not part of the field name
        variable_part_pattern = r'[A-Za-z0-9\-]+'
        matches = list(re.finditer(variable_part_pattern, escaped_example))

        if not matches:
            print("No variable part found in the example.")
            return None

        # Identify the variable part (value) that is not part of the field name
        field_name_positions = [(m.start(), m.end()) for m in re.finditer(re.escape(escaped_field_name), escaped_example, re.IGNORECASE)]
        variable_part = None
        for match in matches:
            start, end = match.span()
            # Check if this match overlaps with the field name
            if not any(f_start <= start < f_end for f_start, f_end in field_name_positions):
                variable_part = (start, end)
                break

        if variable_part is None:
            print("Could not identify the variable part in the example.")
            return None

        variable_start, variable_end = variable_part
        # Build the pattern
        prefix = escaped_example[:variable_start]
        suffix = escaped_example[variable_end:]

        # Allow optional characters between field name and value (like colon, whitespace)
        prefix = prefix.rstrip('\\') + r'[:\s\-]*'

        pattern = f"(?i){prefix}([A-Za-z0-9\\-]+){suffix}"
        # Replace escaped whitespace with \s+
        pattern = re.sub(r'\\\s+', r'\\s+', pattern)
        print(f"Generated pattern: {pattern}\n")
        return pattern

    def extract_field(self, pdf_path, pattern):
        """
        Extracts a field from a PDF using a regex pattern.

        Args:
            pdf_path (str): The path to the PDF file.
            pattern (str): The regex pattern to search for.

        Returns:
            str: The extracted field.
        """
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(min(5, len(doc))):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        # Normalize whitespace in text
        text = re.sub(r'\s+', ' ', text)
        # Search for the pattern
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
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
