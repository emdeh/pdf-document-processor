##
## TO-DO: Update field names to be relative to yaml file like extract_static_info() function.
##

import csv
import pandas as pd
import os

def extract_static_info(results, original_file_name, statement_type):
    """Extract static information from the analysis results."""
    def extract_label_value(label):
        """Nested helper function to extract concatenated text values for a given label."""
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

def process_transactions(results):
    #print(f"Debug - {results}") # Debug print
    transactions = []

    # Iterate through the analyzed document results
    for document in results.documents:
        # Check if 'accountTransactions' is a key in this document
        if 'accountTransactions' in document.fields:
            # Get the list of transactions
            account_trans_list = document.fields['accountTransactions'].value
                        
            # Iterate through each transaction DocumentField in the list
            for transaction_field in account_trans_list:
                # Access each field within the transaction using the .value attribute of DocumentField
                date_field = transaction_field.value.get('Date', None)
                description_field = transaction_field.value.get('Description', None)
                amount_field = transaction_field.value.get('Amount', None)
                cr_if_credit_field = transaction_field.value.get('CR if Credit', None)
                
                # Prepare the amount_field value for conversion
                # Remove commas and convert to float
                amount_value = 0.0
                conversion_flag = False
                if amount_field:
                    amount_str = amount_field.value.replace(',', '')
                    try:
                        amount_value = float(amount_str)
                    except ValueError:
                        # Handle cases where conversion is not possible
                        amount_value = amount_str
                        conversion_flag = True
                        print(f"Could not convert {amount_str} to float. Mapping actual value.\n")

                # Build the transaction dictionary
                transaction = {
                    'Date': date_field.value if date_field else '',
                    'Description': description_field.value.replace('\n', ' ') if description_field else '',
                    'Amount': amount_value,
                    'CR if Credit': cr_if_credit_field.value if cr_if_credit_field else '',
                    'AmountConversionSuccess': not conversion_flag # True if conversion was successful, False otherwise
                    
                }
                transactions.append(transaction)

    return transactions

def extract_and_process_summary_info(document_analysis_results):
    """
    Extracts summary information from a document's results, now including CIs.
    Like this: 
    {
        "PreviousBalance": {"value": 1000.0, "confidence": "0.95"},
        "PaymentsAndCredits": {"value": 200.0, "confidence": "0.9"},
        // Other fields follow the same structure...
    }       
    """
    
    def extract_summary_values_and_confidence(label):
        """Extracts values and their confidence."""
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
        # Join multiple entries into a single string, if applicable
        value = ' '.join(value_concat) if value_concat else ''
        confidence = ' '.join(map(str, confidence_concat)) if confidence_concat else ''
        return value, confidence

    # Specified fields
    labels = ['PreviousBalance', 'PaymentsAndCredits', 'NewDebits', 'TotalBalance', 'BalanceDue', 'PaymentDueDate']
    summary_info_with_confidence = {}
    for label in labels:
        value, confidence = extract_summary_values_and_confidence(label)
        # Convert to float where applicable, except for 'PaymentDueDate'
        if label != 'PaymentDueDate':
            try:
                value = float(value.replace(',', '').strip())
            except ValueError:
                pass  # Keep the original value if conversion fails
        summary_info_with_confidence[label] = {"value": value, "confidence": confidence}

    return summary_info_with_confidence

def format_summary_for_excel(summary_data):
    """
    Takes the dictionary from extract_and_process_summary_info and flattens it.
    Returns a dictionary with keys for each summary field and its confidence.
    Like this:
    {
        "PreviousBalance_Value": 1000.0,
        "PreviousBalance_Confidence": "0.95",
        "PaymentsAndCredits_Value": 200.0,
        "PaymentsAndCredits_Confidence": "0.9",
        // This pattern is repeated for each original key...
    }        
    """
    flattened = {}
    # Ensure that summary_data is a dictionary as expected
    #print("Debug - summary_data:", summary_data)  # Debug print
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
        print(f"Was passed a non-dict object: {type(summary_data)}") # What passed it?
    return flattened

def write_transactions_and_summaries_to_excel(transactions_records, summary_data, output_dir, excel_filename):
    transactions_df = pd.DataFrame(transactions_records)
    
    # Initialize an empty list for rows
    summary_rows = []
    for summary in summary_data:
        # Flatten each summary info dictionary and add it to the rows list
        flattened_summary = format_summary_for_excel(summary)
        summary_rows.append(flattened_summary)
    
    # Now create a DataFrame from the list of rows
    summaryinfo_df = pd.DataFrame(summary_rows)

    output_file_path = os.path.join(output_dir, excel_filename)
    
    if os.path.exists(output_file_path):
        # Append data to existing file
        with pd.ExcelWriter(output_file_path, engine='openpyxl', mode='a', if_sheet_exists='new') as writer:
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            summaryinfo_df.to_excel(writer, sheet_name='Summary', index=False)
        print(f"Data appended to the file '{os.path.basename(excel_filename)}' in {os.path.basename(output_dir)}. folder.\n")

    else:
        # Create a new file
        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            summaryinfo_df.to_excel(writer, sheet_name='Summary', index=False)
        print(f"New file '{os.path.basename(excel_filename)}' created in {os.path.basename(output_dir)}.")
        print(f"Data written to the NEW file '{os.path.basename(excel_filename)}' in {os.path.basename(output_dir)}.\n")
