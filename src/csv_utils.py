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

def process_transactions(results, statement_type):
    transactions = []

    for document in results.documents:
        if 'accountTransactions' in document.fields:
            account_trans_list = document.fields['accountTransactions'].value

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
                        field_value, temp_conversion_success = convert_amount(field_value_str)
                        conversion_success = conversion_success and temp_conversion_success

                    transaction[field_name] = field_value

                transaction['ConversionSuccess'] = conversion_success
                transactions.append(transaction)

    return transactions

def convert_amount(amount_str):
    """Attempt to convert the amount string to float and return the conversion success flag."""
    try:
        return float(amount_str.replace(',', '')), True
    except ValueError:
        print(f"Could not convert {amount_str} to float. Mapping actual value.")
        return amount_str, False

def extract_and_process_summary_info(document_analysis_results, statement_type):
    """
    Extracts summary information from a document's results, now including CIs,
    and uses the statement_type configuration to determine how to process each field.

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
            value, _ = convert_amount(value)  # Assuming convert_amount returns (converted_value, success_flag)
        else:
            # For non-amount fields, just ensure it's appropriately formatted or left as is
            value = value.strip()
        
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
