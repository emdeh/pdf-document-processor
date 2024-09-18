# src/csv_utils.py

import csv
import pandas as pd
import os


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
                        # Assuming fields have 'content' or 'value' attributes
                        return ' '.join([field.content if field.content else field.value])
            return ""  # Return an empty string if the label is not found

        static_info = {
            'OriginalFileName': original_file_name}
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
        """
        Convert the amount string to a float and return the conversion success flag.

        Parameters:
        amount_str (str): The amount string to be converted.

        Returns:
        tuple: A tuple containing the converted amount (float) and a flag indicating the success of the conversion (bool).

        If the conversion is successful, the flag will be True and the converted amount(int) will be returned.
        If the conversion fails, the flag will be False and the original amount(str) string will be returned.

        Example:
        >>> convert_amount("1,000.50")
        (1000.5, True)

        >>> convert_amount("+USD100")
        ("+USD100", False)
        """
        try:
            return float(amount_str.replace(',', '')), True
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

    def write_transactions_and_summaries_to_excel(
        self, transactions_records, summary_data, output_dir, excel_filename, table_data=None
    ):
        """
        Writes transaction records and summary data to an Excel file.

        Args:
            transactions_records (list): A list of dictionaries representing transaction records.
            summary_data (list): A list of dictionaries representing summary data.
            output_dir (str): The directory where the Excel file will be saved.
            excel_filename (str): The name of the Excel file.
            table_data (list, optional): A list of dictionaries representing table data. Defaults to None.

        Returns:
            None
        """
        import pandas as pd
        import os

        transactions_df = pd.DataFrame(transactions_records)

        # Initialize an empty list for rows
        summary_rows = []
        for summary in summary_data:
            # **Use 'self.format_summary_for_excel' instead of 'format_summary_for_excel'**
            flattened_summary = self.format_summary_for_excel(summary)
            summary_rows.append(flattened_summary)

        # Now create a DataFrame from the list of rows
        summaryinfo_df = pd.DataFrame(summary_rows)

        output_file_path = os.path.join(output_dir, excel_filename)

        with pd.ExcelWriter(output_file_path, engine='openpyxl', mode='a' if os.path.exists(output_file_path) else 'w') as writer:
            if not transactions_df.empty:
                transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            summaryinfo_df.to_excel(writer, sheet_name='Summary', index=False)

            if table_data:
                table_df = pd.DataFrame(table_data)
                if not table_df.empty:
                    table_df.to_excel(writer, sheet_name='Tables', index=False)

        print(f"Data written to the file '{os.path.basename(excel_filename)}' in {os.path.basename(output_dir)}.\n")