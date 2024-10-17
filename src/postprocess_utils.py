import pandas as pd
import fitz # PyMuPDF
import re
import os
import shutil
from pathlib import Path
from datetime import datetime

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
        'categorise_by_account_number': {
            'func': 'categorise_by_account_number',
            'description': 'Categorise PDF statements into folders based on account number.'
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

    @staticmethod
    def categorise_by_account_number(self):
        """
        Categorise PDF statements into folders based on account number.
        """
        print("Categorising PDF statements by account number...")
        pattern = self.get_pattern_from_user("account_number")
        for pdf_file in self.pdf_files:
            pdf_path = str(pdf_file)
            account_number = self.extract_field(pdf_path, pattern)

            if account_number:
                # Create account-specific folder
                account_folder = os.path.join(self.input_folder, account_number)
                os.makedirs(account_folder, exist_ok=True)

                # Move PDF file to account-specific folder
                destination = os.path.join(account_folder, pdf_file.name)
                shutil.move(pdf_path, destination)
                print(f"Moved {pdf_file.name} to {account_folder}")
            else:
                print(f"ACcount number not found in {pdf_file.name}")

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

    def get_pattern_from_user(self, field_name):
        """
        Prompts the user for an example and generates a regex pattern.

        Args:
            field_name (str): The name of the field to extract.

        Returns:
            str: The regex pattern.
        """
        example = input(f"Please enter an example of how the {field_name} appears in the statement (use <VALUE> where the variable part is):\n")
        pattern = self.generate_regex_from_example(example)
        return pattern

    def generate_regex_from_example(self, example):
        """
        Generates a regex pattern from a user-provided example.

        Args:
            example (str): An example string to generate a regex pattern from.

        Returns:
            str: The regex pattern.
        """
        escaped_example = re.escape(example)
        pattern = escaped_example.replace(r'\<VALUE\>', r'(.+)')
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
        # This is very similar to detect_document_type() and find_x_statements() in pdf_processor.py. 
        # TODO: Consider refactoring to a common function.
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(min(5, len(doc))):
            page = doc.load_page(page_num)
            text += page.get_text()
        
        doc
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return None

    def format_date(self, date_str):
        """
        Formats a date string extracted from a PDF.

        Args:
            date_str (str): The date string to format.

        Returns:
            str: The formatted date.
        """
        pass
