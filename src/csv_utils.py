import csv
import pandas as pd
import os

def write_data_to_excel(transactions, all_summaries, output_path, output_filename):
    transactions_df = pd.DataFrame(transactions)
    
    # Initialize an empty list for rows
    summary_rows = []
    for summary in all_summaries:
        # Flatten each summary info dictionary and add it to the rows list
        flattened_summary = flatten_summary_info(summary)
        summary_rows.append(flattened_summary)
    
    # Now create a DataFrame from the list of rows
    summaryinfo_df = pd.DataFrame(summary_rows)

    output_file_path = os.path.join(output_path, output_filename)
    
    if os.path.exists(output_file_path):
        # Append data to existing file
        with pd.ExcelWriter(output_file_path, engine='openpyxl', mode='a', if_sheet_exists='new') as writer:
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            summaryinfo_df.to_excel(writer, sheet_name='Summary', index=False)
        print(f"Data appended to the file '{os.path.basename(output_filename)}' in {os.path.basename(output_path)}. folder.\n")

    else:
        # Create a new file
        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            summaryinfo_df.to_excel(writer, sheet_name='Summary', index=False)
        print(f"New file '{os.path.basename(output_filename)}' created in {os.path.basename(output_path)}.")
        print(f"Data written to the NEW file '{os.path.basename(output_filename)}' in {os.path.basename(output_path)}.\n")

def flatten_summary_info(summary_info_with_confidence):
    flattened = {}
    # Ensure that summary_info_with_confidence is indeed a dictionary as expected
    print("Debug - summary_info_with_confidence:", summary_info_with_confidence)  # Debug print
    if isinstance(summary_info_with_confidence, dict):
        for key, info in summary_info_with_confidence.items():
            #print("Debug - Processing:", key, info)  # Further debug print to inspect each item
            if isinstance(info, dict) and 'value' in info:
                flattened[f"{key}_Value"] = info['value']
                flattened[f"{key}_Confidence"] = info.get('confidence', 'N/A')
            else:
                print(f"Unexpected structure for {key}: {info}")
    else:
        print(f"flatten_summary_info was passed a non-dict object: {type(summary_info_with_confidence)}")
    return flattened


def aggregate_data(static_info, transactions, csv_file_path):
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)

        # Iterate over transactions to write each one to the CSV
        for transaction in transactions:
            # Assuming each transaction is a dictionary with 'Date', 'Description', 'Amount', and 'CR if Credit'
            # Note: You may need to adjust the extraction logic based on the actual structure of 'transaction'
            transaction_date = transaction.get('Date', '')
            transaction_description = transaction.get('Description', '').replace('\n', ' ')
            transaction_amount = transaction.get('Amount', '')
            cr_if_credit = transaction.get('CR if Credit', '')  # This field is optional
            conversion_flag = transaction.get('AmountConversionSuccess', False)  # Flag indicating if amount conversion was successful

            # Combine static and transaction-specific information into one row
            row = [
                static_info['OriginalFileName'],
                static_info['AccountHolder'],
                static_info['AccountEntity'],
                static_info['ABN'],
                static_info['CorporateID'],
                static_info['MembershipNumber'],
                static_info['StatementDate'],
                transaction_date,
                transaction_description,
                transaction_amount,
                cr_if_credit,
                conversion_flag
            ]
            
            # Write the row to the CSV
            csvwriter.writerow(row)

def extract_static_info(results, original_file_name):
    """Extract static information from the analysis results."""
    def extract_label_value(label):
        """Nested helper function to extract concatenated text values for a given label."""
        for document in results.documents:
            for name, field in document.fields.items():
                if name == label:
                    # Assuming fields have 'content' or 'value' attributes
                    return ' '.join([field.content if field.content else field.value])
        return ""  # Return an empty string if the label is not found

    original_file_name = original_file_name  # Placeholder, adjust accordingly

    static_info = {
        'OriginalFileName': original_file_name, 
        'AccountHolder': extract_label_value('AccountName'),
        'AccountEntity': extract_label_value('AccountEntity'),
        'ABN': extract_label_value('ABN'),
        'CorporateID': extract_label_value('CorporateID'),
        'MembershipNumber': extract_label_value('MembershipNumber'),
        'StatementDate': extract_label_value('StatementDate')
    }
    return static_info

def process_transactions(results):
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

def extract_summary_info(results):
    """Extracts summary information from a document's results, now including confidence levels."""
    
    def extract_summary_values_and_confidence(label):
        """Extracts values and their confidence."""
        value_concat = []
        confidence_concat = []
        for document in results.documents:
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

