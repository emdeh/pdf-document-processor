import pandas as pd
import fitz # PyMuPDF
import re
import os
import shutil
from pathlib import Path
from datetime import datetime
from utils import Logger
import string
import math
import dateutil.parser

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
        self.logger = Logger.get_logger(self.__class__.__name__, log_to_file=True)

    def _load_excel_file(self):
        """Loads the Excel file into DataFrames."""
        self.logger.info(
            "Loading Excel file: %s",
            self.file_path
        )
        excel_file = pd.ExcelFile(self.file_path)
        self.summary_df = pd.read_excel(excel_file, sheet_name='Summary')
        self.transactions_df = pd.read_excel(excel_file, sheet_name='Transactions')

    def save(self, output_file):
        """Saves the DataFrames back to an Excel file."""
        self.logger.info(
            "Saving to: %s",
            output_file
        )
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
    # This makes the tasks appear for selection when running `python src/postprocess.py -h`
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

    # Class variables
    acc_input = None
    state_input = None
    date_input = None

    def __init__(self, input_folder):
        self.input_folder = input_folder
        self.pdf_files = list(Path(input_folder).glob("*.pdf"))
        self.logger = Logger.get_logger(self.__class__.__name__, log_to_file=True)

    def categorise_by_value(self):
        """
        Categorise PDF statements into folders based on a value pattern derived from a provided example.
        """
        # TODO: Instead of prompting for an example, consider storing in yaml and loading patterns from there.
        # Prompt the user for a field name, used to append a description to the folder and filename.
        field_name = input("Please enter a name for the field (e.g., 'Account Number', 'Statement ID'):\n")
        self.logger.info(
            "Categorising PDF statements by %s...",
            field_name
        )

        # Prompt the user for an example value
        # This example will be used to generate a regex pattern to extract the value from the PDF
        value_example = input(f"Please enter an example of the {field_name} value (e.g., '123-456-789'):\n")

        # Generate the value pattern based on the example.
        # Calls the `generate_regex_from_value_example` function to generate the pattern based on the example.
        pattern = self.generate_regex_from_value_example(value_example)
        if not pattern:
            self.logger.warning("Pattern generation failed. Exiting task.")
            return

        self.logger.info(
            "Generated value pattern: %s\n",
            pattern
        )

        for pdf_file in self.pdf_files:
            pdf_path = str(pdf_file)

            # Find and extract the value from the PDF based on the pattern
            extracted_value = self.extract_value_from_pdf(pdf_path, pattern)
            if extracted_value:
                # Construct folder name using the field name and extracted value found in the PDF.
                sanitised_field_name = self.sanitise_folder_name(field_name.replace(" ", ""))
                sanitised_value = self.sanitise_folder_name(extracted_value)
                folder_name = f"{sanitised_field_name}-{sanitised_value}"
                folder_path = os.path.join(self.input_folder, folder_name)

                # Create the folder based on the constructed folder name
                os.makedirs(folder_path, exist_ok=True)

                # Rename the file to include the extracted value
                ### NOTE:
                #   This renaming part is purposely kept seperate from the prefix_date function so that function can
                #   be called independently from the task registry specifically for date prefixes.
                ###
                new_filename = (f"{sanitised_field_name}-{sanitised_value}-{pdf_file.name}")
                self.logger.info(
                    "File %s renamed to $s",
                    pdf_file.name,
                    new_filename
                )
                destination = os.path.join(folder_path, new_filename)

                # Move and rename the file                
                shutil.move(pdf_path, destination)
                self.logger.info(
                    "Moved to Folder: %s",
                    sanitised_value
                )
            else:
                self.logger.info(
                    "Value not found in %s",
                    pdf_file.name
                )

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

    def extract_value_from_pdf(self, pdf_path, pattern, page_size = 0.2):
        """
        Extracts a value from a PDF using a regex pattern..

        Args:
            pdf_path (str): The path to the PDF file.
            pattern (str): The regex pattern to search for.
            OPTIONAL page_size (float): How much of the page the scanner will examine for the pattern.

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
        # Open the PDF file
        doc = fitz.open(pdf_path)

        # Initialize an empty string to store the extracted text
        text = ""

        # Iterate over each page in the PDF
        for page_num in range(len(doc)):
            # Load the page
            page = doc.load_page(page_num)
            # Get the height of the page
            page_height = page.rect.height

            # Get text as a dictionary
            page_dict = page.get_text("dict")  # Use "dict"

            # Iterate over each block in the page
            for block in page_dict["blocks"]:
                # Process only text blocks
                if block["type"] == 0:
                    # Iterate over each line in the block
                    for line in block["lines"]:
                        # Iterate over each span in the line
                        for span in line["spans"]:
                            # Get the bounding box of the span
                            bbox = span["bbox"]
                            # Extract the text of the span
                            x0, y0, x1, y1 = bbox
                            # Calculate the width and height of the span
                            width = x1 - x0
                            # Calculate the height of the span
                            height = y1 - y0

                            # If width is greater than height, consider it horizontal text
                            if width > height:
                                # Optionally, limit to a specific area (e.g., top 20% of the page)
                                if y1 < page_height * page_size:
                                    # Append the text of the span to the accumulated text
                                    text += span["text"] + " "
                            else:
                                # Skip vertical or rotated text
                                continue
        # Close the PDF
        doc.close()

        # Normalise whitespace in text
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
        # Define valid characters
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)\
        
        # Remove invalid characters
        sanitised_name = ''.join(c for c in name if c in valid_chars)

        # Replace spaces with underscores
        return sanitised_name

    def extract_statement_start_date(self, pdf_path, pattern):
        '''
        Extracts the start date of the statement. Currently just calls a different method and executes it. Might not need to be used.

        Args:
            pdf_path (str): The path to the PDF file.
            pattern (): The structure of the date to seek

        Returns:
            start_date (str): A date type in an unknown format.
        '''
        start_date = self.extract_value_from_pdf(pdf_path, pattern, page_size=1)
        return start_date
    def format_date(self, date_str):
        """
        Formats a date string extracted from a PDF.

        Args:
            date_str (str): The date string

        Returns:
            str: A string of the date in form YYYYMMDD. E.g., 20230130
        """
        # Dateutil's parser is designed to capture most date formats. If it fails, adjust to a try statement, with the except section parsing the atypical format.
        parsed_date = dateutil.parser.parse(date_str)

        str = parsed_date.strftime("%Y%m%d")
        return str

    def add_date_prefix_to_filenames(self):
        """
        Add statement start date as prefix to PDF filenames for chronological ordering.
        """
        # NOTE: Need to gain insight into which date target is the "correct" date.
        if self.__class__.date_input is None:
            date_input = input("Please input an example of the start date format. (e.g., '02-FEB-2024', '04-30-2019'):\n")
        else: 
            date_input = self.__class__.date_input
        # Develop regex pattern from input example
        pattern = self.generate_regex_from_value_example(date_input)
        # Insert pattern into extract_value_from_pdf and output
        if not pattern:
            self.logger.info("Pattern generation failed. Exiting task.")
            return
        for pdf_file in self.pdf_files:
            pdf_path = str(pdf_file)
            date_str = self.extract_statement_start_date(pdf_path, pattern)
            if date_str:
                # TODO: Move this function into the extraction method, to match statement number extraction method
                date_prefix = self.format_date(date_str)
                # Determine new file name
                new_filename = (f"{date_prefix}-{pdf_file.name}")
                # Specify start/end path, currently the same location.
                origin = os.path.join(self.input_folder, pdf_file.name)
                destination = os.path.join(self.input_folder, new_filename)

                # Rename the file                
                os.rename(origin, destination)
                self.logger.info(
                    "File %s renamed to %s",
                    pdf_file.name,
                    new_filename
                )
            else:
                self.logger.info(
                    "Value not found in %s",
                    pdf_file.name
                )

    def extract_statement_number(self, pdf_path, pattern):
        """
        Extract the statement number from the document

        Args:
            pdf_path (str): The path to the PDF file.
            pattern (): The structure of the date to seek

        Returns:
            statement_num (str): The statement number as a string.
        """

        # Implemented like statement date, however is capable and prefers accepting prefix identifier such as "Statement no."
        statement_num = self.extract_value_from_pdf(pdf_path, pattern, page_size=1)
        if statement_num:
            # Strips prefix identfiers to isolate the statement number
            statement_number = ''.join(c for c in statement_num if c.isdigit())
            return statement_number
        return statement_num

    def identify_and_move_duplicates(self):
        """
        Identify duplicate statements and move them to a duplicates folder.
        """
        # Initialise variables
        items = []
        folder_path = os.path.join(self.input_folder, 'duplicate')
        os.makedirs(folder_path, exist_ok=True)
        counter = 0

        # Gather user inputs
        if self.__class__.acc_input is None:
            self.__class__.acc_input = input("Please provide an example of the account number. (e.g., '44-1234'):\n")

        if self.__class__.state_input is None:
            self.__class__.state_input = input("Please provide an example of the statement number with prefix sentence. (e.g., 'Statement no. 12'): \n")

        if self.__class__.date_input is None:
            self.__class__.date_input = input("Please provide an example of the statement start date. (e.g., '12 NOV 2023'): \n")
        
        acc_input = self.__class__.acc_input
        state_input = self.__class__.state_input
        date_input = self.__class__.date_input

        # regex inputs
        acc_pattern = self.generate_regex_from_value_example(acc_input)
        state_pattern = self.generate_regex_from_value_example(state_input)
        date_pattern = self.generate_regex_from_value_example(date_input)


        # Regex error handling
        if not acc_pattern:
            self.logger.info("Account number pattern generation failed. Exiting task.")
            return
        if not state_pattern:
            self.logger.info("Statement number pattern generation failed. Exiting task.")
            return
        if not date_pattern:
            self.logger.info("Statement start date number pattern generation failed. Exiting task.")
            return
        
        # Loop over each pdf file
        for pdf_file in self.pdf_files:
            pdf_path = str(pdf_file)
            identifier = ''
            # Create a string of each item to assess individuality
            acc_str = self.extract_value_from_pdf(pdf_path, acc_pattern)
            state_str = self.extract_statement_number(pdf_path, state_pattern)
            date_str = self.extract_statement_start_date(pdf_path, date_pattern)
            # Combine items to create unique identifier
            identifier = ''.join(filter(None, [acc_str, state_str, date_str]))
            # In case of empty identifier
            if identifier:
                # Add identifier to list of known identifiers
                if identifier not in items:
                    items.append(identifier)
                # If identifier seen, move pdf to duplicates folder
                else:
                    destination = os.path.join(folder_path, pdf_file.name)
                    shutil.move(pdf_path, destination)
                    # Track total number of duplicates
                    counter += 1
                    self.logger.info("File moved to duplicate")
            else:
                self.logger.info(
                    "Value not found in %s",
                    pdf_file.name
                )
        return self.logger.info(
            "A total of %s duplicates were found",
            counter
        )