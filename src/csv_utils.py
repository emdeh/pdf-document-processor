# src/csv_utils.py

import csv
import pandas as pd
import os
import re


class CSVUtils:
    def __init__(self):
        pass

    def extract_static_info(self, results, original_file_name, statement_type):
        """
        Extracts static information from the analysis results.

        Args:
            results (AnalysisResults): The analysis results object.
            original_file_name (str): The original file name.
            statement_type (dict): The statement type dictionary.

        Returns:
            dict: A dictionary containing the extracted static information.

        """
        def extract_label_value(label):
            """
            Nested helper function to extract concatenated text values for a given label.

            Args:
                label (str): The label to extract values for.

            Returns:
                str: The concatenated text values for the given label.

            """
            for document in results.documents:
                for name, field in document.fields.items():
                    if name == label:
                        # Use 'or' to select the first non-None value
                        value = field.content or field.value
                        if value is not None:
                            return str(value)
                        else:
                            return ''
            return ""  # Return an empty string if the label is not found

        static_info = {
            'OriginalFileName': original_file_name
        }

        for field in statement_type["transaction_static_fields"]:
            field_name = field['field_name']
            static_info[field_name] = extract_label_value(field_name)

        return static_info

    def process_transactions(self, results, statement_type):
        """
        Process transactions from the provided results based on the statement type.

        Args:
            results (object): The results object containing the documents.
            statement_type (dict): The statement type configuration.

        Returns:
            list: A list of dictionaries representing the processed transactions.
        """
        
        transactions = []

        for document in results.documents:
            if 'Transactions' in document.fields: # TO-DO: This is Transactions for westpac and accountTransactions for amex due to field naming difference - need to fix to be dynamic somehow.
                account_trans_list = document.fields['Transactions'].value # TO-DO: Transactions for one type and accountTransactions for another - need to fix.

                for transaction_field in account_trans_list:
                    transaction = {}
                    conversion_success = True  # Assumes success unless proven otherwise
                    
                    for field_config in statement_type['transaction_dynamic_fields']:
                        field_name = field_config['field_name']
                        is_amount = field_config.get('is_amount', False)
                        # Initially assume field_value is None
                        field_value = None
                        # Check if the field exists and has a 'value' attribute
                        if field_name in transaction_field.value and hasattr(transaction_field.value[field_name], 'value'):
                            field_value = transaction_field.value[field_name].value
                        
                        if is_amount and field_value:
                            # Convert field_value to string in case it's not
                            field_value_str = str(field_value)
                            field_value, temp_conversion_success = self.convert_amount(field_value_str)
                            conversion_success = conversion_success and temp_conversion_success

                        transaction[field_name] = field_value

                    transaction['ConversionSuccess'] = conversion_success
                    transactions.append(transaction)

        return transactions

    def convert_amount(self, amount_str):
        import re

        try:
            # Use regex to extract numeric part
            match = re.search(r'[-+]?[\d,]*\.?\d+', amount_str)
            if match:
                amount_cleaned = match.group()
                amount_cleaned = amount_cleaned.replace(',', '')
                amount_float = float(amount_cleaned)
                # Determine the sign
                if '-' in amount_str:
                    amount_float = -amount_float
                return amount_float, True
            else:
                raise ValueError("No numeric value found")
        except ValueError:
            print(f"Could not convert {amount_str} to float. Mapping actual value.")
            return amount_str, False

    def extract_and_process_summary_info(self, document_analysis_results, statement_type):
        """
        Extracts summary information from a document's results, now including CIs,
        and uses the statement_type configuration to determine how to process each field.

        Args:
            document_analysis_results (AnalysisResults): The analysis results object.
            statement_type (dict): The statement type configuration.

        Returns:
            dict: A dictionary containing the extracted summary information with values and confidence.

        Example:
            >>> extract_and_process_summary_info(results, statement_type)
            {
                "PreviousBalance": {"value": 1000.0, "confidence": "0.95"},
                "PaymentsAndCredits": {"value": 200.0, "confidence": "0.9"},
                ...
            }

        """

        def extract_summary_values_and_confidence(label):
            """
            Extracts values and their confidence for a given label.

            Args:
                label (str): The label to extract values and confidence for.

            Returns:
                tuple: A tuple containing the extracted value (str) and confidence (str).

            Example:
                >>> extract_summary_values_and_confidence("PreviousBalance")
                ("1000.0", "0.95")

            """
            value_concat = []
            confidence_concat = []
            for document in document_analysis_results.documents:
                for name, field in document.fields.items():
                    if name == label:
                        # Concatenate content from multiple entries if necessary
                        content = field.content if field.content else field.value
                        if content is not None:
                            value_concat.append(content)
                        # Aggregate confidence if available; else use placeholder
                        confidence = field.confidence if field.confidence is not None else 'N/A'
                        confidence_concat.append(confidence)
            value = ' '.join(value_concat) if value_concat else ''
            confidence = ' '.join(map(str, confidence_concat)) if confidence_concat else ''
            return value, confidence

        summary_info_with_confidence = {}
        for field_config in statement_type["summary_fields"]:
            label = field_config['field_name']
            is_amount = field_config.get('is_amount', False)
            
            value, confidence = extract_summary_values_and_confidence(label)
            
            # Process the value based on whether it's flagged as an amount
            if is_amount:
                value, _ = self.convert_amount(value)  # Assuming convert_amount returns (converted_value, success_flag)
            else:
                # For non-amount fields, just ensure it's appropriately formatted or left as is
                value = value.strip()
            
            summary_info_with_confidence[label] = {"value": value, "confidence": confidence}

        return summary_info_with_confidence

    def format_summary_for_excel(self, summary_data):
        """
        Takes the dictionary from extract_and_process_summary_info() and flattens it.
        Returns a dictionary with keys for each summary field and its confidence.

        Args:
            summary_data (dict): A dictionary containing the summary data extracted from a document.

        Returns:
            dict: A flattened dictionary with keys for each summary field and its confidence.

        Example:
            summary_data = {
                "DocumentName": "Invoice.pdf",
                "PreviousBalance": {
                    "value": 1000.0,
                    "confidence": 0.95
                },
                "PaymentsAndCredits": {
                    "value": 200.0,
                    "confidence": 0.9
                }
            }
            flattened = format_summary_for_excel(summary_data)
            print(flattened)
            # Output:
            # {
            #     "DocumentName": "Invoice.pdf",
            #     "PreviousBalance_Value": 1000.0,
            #     "PreviousBalance_Confidence": 0.95,
            #     "PaymentsAndCredits_Value": 200.0,
            #     "PaymentsAndCredits_Confidence": 0.9
            # }
        """

        flattened = {}
        # Ensure that summary_data is a dictionary as expected
        if isinstance(summary_data, dict):
            for key, info in summary_data.items():
                if key == "DocumentName":
                    flattened[key] = str(info)
                elif isinstance(info, dict) and 'value' in info:
                    flattened[f"{key}_Value"] = info['value']
                    flattened[f"{key}_Confidence"] = info.get('confidence', 'N/A')
                else:
                    print(f"Unexpected structure for {key}: {info}")
        else:
            print(f"Was passed a non-dict object: {type(summary_data)}")
        return flattened

    def assign_years_to_dates(self, transactions_df, statement_start_date_str, statement_end_date_str):
        """
        Assigns years to dates that lack year information based on the statement period.

        Args:
            transactions_df (pd.DataFrame): The transactions DataFrame.
            statement_start_date_str (str): The statement start date as a string (e.g., '22 June 2022').
            statement_end_date_str (str): The statement end date as a string (e.g., '22 July 2023').

        Returns:
            pd.DataFrame: The updated transactions DataFrame with years assigned to dates.
        """
        # Parse the statement start and end dates
        statement_start_date = pd.to_datetime(statement_start_date_str, format='%d %B %Y', errors='coerce')
        statement_end_date = pd.to_datetime(statement_end_date_str, format='%d %B %Y', errors='coerce')

        if pd.isna(statement_start_date) or pd.isna(statement_end_date):
            raise ValueError("Statement start or end date is invalid.")

        # Get the years covered in the statement
        start_year = statement_start_date.year
        end_year = statement_end_date.year

        # Initialize the current year
        current_year = start_year
        previous_month = None
        dates_with_year = []

        # **Do not sort the transactions_df**
        # Ensure transactions are in the order they appear in the statement
        # transactions_df = transactions_df.sort_values(by='Date').reset_index(drop=True)

        # Iterate over the 'Date' column in the existing order
        for idx, date in transactions_df['Date'].items():
            if pd.isna(date):
                dates_with_year.append(pd.NaT)
                continue

            # Extract day and month from the date
            day = date.day
            month = date.month

            # Detect year rollover
            if previous_month and month < previous_month:
                current_year += 1
                if current_year > end_year:
                    current_year = end_year  # Prevent exceeding the end year

            # Create a new date with the assigned year
            try:
                new_date = pd.Timestamp(year=current_year, month=month, day=day)
            except ValueError:
                new_date = pd.NaT  # Handle invalid dates

            dates_with_year.append(new_date)
            previous_month = month

        # Assign the new dates to the DataFrame
        transactions_df['Date'] = dates_with_year

        # Debugging: Print a few rows to verify
        print("Transactions DataFrame after assigning years:\n", transactions_df.head())

        return transactions_df


    def write_transactions_and_summaries_to_excel(
            self, transactions_records, summary_data, output_dir, excel_filename, table_data=None, statement_type=None
        ):
        # Create DataFrames from records
        transactions_df = pd.DataFrame(transactions_records)

        # Process summary data
        summary_rows = []
        for summary in summary_data:
            flattened_summary = self.format_summary_for_excel(summary)
            summary_rows.append(flattened_summary)

        summaryinfo_df = pd.DataFrame(summary_rows)

        # Debugging: Print summaryinfo_df columns and content
        print("Summary DataFrame columns:", summaryinfo_df.columns.tolist())
        print("Summary DataFrame content:\n", summaryinfo_df.head())

        # Initialize sets for amount and date columns
        amount_columns = set()
        date_columns = set()
        date_column_formats = {}  # Mapping from column names to date formats

        # Extract field information from statement_type
        if statement_type:
            # Transaction Dynamic Fields
            for field in statement_type.get('transaction_dynamic_fields', []):
                field_name = field['field_name']
                if field.get('is_amount'):
                    amount_columns.add(field_name)
                if field.get('is_date'):
                    date_columns.add(field_name)
                    date_format = field.get('date_format')
                    if date_format:
                        date_column_formats[field_name] = date_format

            # Transaction Static Fields
            for field in statement_type.get('transaction_static_fields', []):
                field_name = field['field_name']
                if field.get('is_amount'):
                    amount_columns.add(field_name)
                if field.get('is_date'):
                    date_columns.add(field_name)
                    date_format = field.get('date_format')
                    if date_format:
                        date_column_formats[field_name] = date_format

            # Summary Fields
            for field in statement_type.get('summary_fields', []):
                field_name = field['field_name']
                if field.get('is_amount'):
                    amount_columns.add(field_name)
                if field.get('is_date'):
                    date_columns.add(field_name)
                    date_format = field.get('date_format')
                    if date_format:
                        date_column_formats[field_name] = date_format

        # Convert amount columns to numeric
        for col in amount_columns:
            if col in transactions_df.columns:
                transactions_df[col] = pd.to_numeric(transactions_df[col], errors='coerce')
            if col in summaryinfo_df.columns:
                summaryinfo_df[col] = pd.to_numeric(summaryinfo_df[col], errors='coerce')

        # Convert date columns to datetime
        for col in date_columns:
            date_format = date_column_formats.get(col)
            if col in transactions_df.columns:
                if date_format:
                    if transactions_df[col].dtype == object:
                        transactions_df[col] = transactions_df[col].str.title()  # Convert to Title Case
                    transactions_df[col] = pd.to_datetime(
                        transactions_df[col],
                        format=date_format,
                        errors='coerce',
                        dayfirst=True
                    )
                else:
                    transactions_df[col] = pd.to_datetime(
                        transactions_df[col],
                        errors='coerce',
                        dayfirst=True
                    )
            if col in summaryinfo_df.columns:
                if date_format:
                    if summaryinfo_df[col].dtype == object:
                        summaryinfo_df[col] = summaryinfo_df[col].str.title()  # Convert to Title Case
                    summaryinfo_df[col] = pd.to_datetime(
                        summaryinfo_df[col],
                        format=date_format,
                        errors='coerce',
                        dayfirst=True
                    )
                else:
                    summaryinfo_df[col] = pd.to_datetime(
                        summaryinfo_df[col],
                        errors='coerce',
                        dayfirst=True
                    )

        # Determine if year assignment is necessary
        assign_years = False
        if 'Date' in transactions_df.columns and date_column_formats.get('Date') == '%d %b':
            assign_years = True

        if assign_years:
            # Extract statement start and end dates from summaryinfo_df
            # Access 'StatementStartDate_Value' and 'StatementEndDate_Value'
            if 'StatementStartDate_Value' in summaryinfo_df.columns and 'StatementEndDate_Value' in summaryinfo_df.columns:
                statement_start_date_str = summaryinfo_df['StatementStartDate_Value'].dropna().iloc[0]
                statement_end_date_str = summaryinfo_df['StatementEndDate_Value'].dropna().iloc[0]
                print(f"Statement Start Date: {statement_start_date_str}")
                print(f"Statement End Date: {statement_end_date_str}")
            else:
                print("Warning: 'StatementStartDate_Value' or 'StatementEndDate_Value' is missing in the summary data.")
                statement_start_date_str = statement_end_date_str = None

            if statement_start_date_str and statement_end_date_str:
                # Ensure the dates are strings in the correct format
                if isinstance(statement_start_date_str, pd.Timestamp):
                    statement_start_date_str = statement_start_date_str.strftime('%d %B %Y')  # '%d %B %Y'
                elif isinstance(statement_start_date_str, str):
                    statement_start_date_str = statement_start_date_str.title()

                if isinstance(statement_end_date_str, pd.Timestamp):
                    statement_end_date_str = statement_end_date_str.strftime('%d %B %Y')  # '%d %B %Y'
                elif isinstance(statement_end_date_str, str):
                    statement_end_date_str = statement_end_date_str.title()

                try:
                    # Assign years to transaction dates
                    transactions_df = self.assign_years_to_dates(
                        transactions_df,
                        statement_start_date_str,
                        statement_end_date_str
                    )
                except Exception as e:
                    print(f"Error assigning years to dates: {e}")
            else:
                print("Warning: Statement start or end date is missing or invalid. Unable to assign years to transaction dates.")

        # Define the output file path
        output_file_path = os.path.join(output_dir, excel_filename)

        # Write DataFrames to Excel with formatting
        with pd.ExcelWriter(
            output_file_path,
            engine='xlsxwriter',
            datetime_format='dd/mm/yyyy',
            date_format='dd/mm/yyyy'
        ) as writer:
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            summaryinfo_df.to_excel(writer, sheet_name='Summary', index=False)

            # Access the workbook and sheets
            workbook = writer.book
            transactions_sheet = writer.sheets['Transactions']
            summary_sheet = writer.sheets['Summary']

            # Define formats
            money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
            date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy'})

            # Apply formats to Transactions sheet
            for idx, col in enumerate(transactions_df.columns):
                if col in amount_columns:
                    transactions_sheet.set_column(idx, idx, None, money_fmt)
                elif col in date_columns:
                    transactions_sheet.set_column(idx, idx, None, date_fmt)

            # Apply formats to Summary sheet
            for idx, col in enumerate(summaryinfo_df.columns):
                if col in amount_columns:
                    summary_sheet.set_column(idx, idx, None, money_fmt)
                elif col in date_columns:
                    summary_sheet.set_column(idx, idx, None, date_fmt)

            # Handle table_data if necessary

        print(f"Data written to the file '{os.path.basename(excel_filename)}' in {os.path.basename(output_dir)}.\n")