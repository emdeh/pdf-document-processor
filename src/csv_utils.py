import csv
import json

# Function to prepare the CSV file with headers for output
def create_output_file(csv_output):
    with open(csv_output, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['OriginalFileName', 'AccountHolder', 'AccountEntity', 'ABN', 'CorporateID', 'MembershipNumber', 'StatementDate', 'TransactionDate', 'TransactionDescription', 'TransactionAmount', 'CRifCredit'])


def parse_results_to_csv(static_info, transactions, csv_file_path):
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
                cr_if_credit
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
                
                # Build the transaction dictionary
                transaction = {
                    'Date': date_field.value if date_field else '',
                    'Description': description_field.value.replace('\n', ' ') if description_field else '',
                    'Amount': amount_field.value if amount_field else '',
                    'CR if Credit': cr_if_credit_field.value if cr_if_credit_field else ''
                }
                transactions.append(transaction)

    return transactions