import csv
import json

# Function to prepare the CSV file with headers for output
def create_output_file(csv_output):
    with open(csv_output, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['OriginalFileName', 'AccountHolder', 'AccountEntity', 'ABN', 'CorporateID', 'MembershipNumber', 'StatementDate', 'TransactionDate', 'TransactionDescription', 'TransactionAmount', 'CRifCredit'])
'''
def parse_json_to_csv(json_content, csv_file_path):
    data = json_content
   
    # Open the CSV file for appending (writing additional rows)
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Extract static information
        static_info = {
            'AccountHolder': extract_label_value(data, 'AccountName'),
            'AccountEntity': extract_label_value(data, 'AccountEntity'),
            'ABN': extract_label_value(data, 'ABN'),
            'CorporateID': extract_label_value(data, 'CorporateID'),
            'MembershipNumber': extract_label_value(data, 'MembershipNumber'),
            'StatementDate': extract_label_value(data, 'StatementDate')
        }
        
        # Iterate through transactions
        index = 0
        while True:
            transaction_date = extract_label_value(data, f'accountTransactions/{index}/Date')
            print(f"Transaction {index}: Date: {transaction_date}")

            if transaction_date is None:
                print("No more transactions to process. Breaking loop")
                break  # No more transactions to process
            
            transaction_description = extract_label_value(data, f'accountTransactions/{index}/Description')
            transaction_amount = extract_label_value(data, f'accountTransactions/{index}/Amount')
            cr_if_credit = extract_label_value(data, f'accountTransactions/{index}/CR if Credit', default='')
            
            # Combine static and transaction-specific information into one row
            row = [
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
            
            index += 1
'''
'''
def extract_label_value(data, label_path, default=''):
    """Utility function to extract concatenated text values for a given label path."""
    for label in data.get('labels', []):
        if label['label'] == label_path:
            # Concatenate text values with a space
            return ' '.join([value['text'] for value in label['value']])
    return default
'''

def parse_json_to_csv(data, csv_file_path, static_info):
    # Initialize a dictionary to hold transaction data, grouped by index
    original_file_name = data.get('document', 'Unknown Document')
    transactions = {}

    # Function to parse the transaction label and extract the index and attribute
    def parse_transaction_label(label):
        parts = label.split('/')
        if len(parts) == 3 and parts[0] == "accountTransactions":
            return int(parts[1]), parts[2]  # Return index as int and attribute
        return None, None

    # Directly iterate over labels in the JSON data
    for label_item in data.get('labels', []):
        index, attribute = parse_transaction_label(label_item['label'])
        if index is not None:
            if index not in transactions:
                transactions[index] = {}
            # Assuming 'text' field within 'value' list contains the data for this attribute
            transactions[index][attribute] = ' '.join([v['text'].replace('\n', ' ') for v in label_item['value']])

    # Now transactions dictionary is organized by transaction index with their attributes

    # Open the CSV file for appending (writing additional rows)
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Iterate over sorted transactions by index to maintain order
        for index in sorted(transactions.keys()):
            transaction = transactions[index]
            row = [
                original_file_name,
                static_info['AccountHolder'],
                static_info['AccountEntity'],
                static_info['ABN'],
                static_info['CorporateID'],
                static_info['MembershipNumber'],
                static_info['StatementDate'],
                transaction.get('Date', ''),
                transaction.get('Description', ''),
                transaction.get('Amount', ''),
                transaction.get('CR if Credit', '') 
            ]
            # Write the constructed row to the CSV
            csvwriter.writerow(row)

def extract_static_info(data):
    """Extract static information from JSON data."""
    def extract_label_value(label):
        """Nested helper function to extract concatenated text values for a given label."""
        for label_item in data.get('labels', []):
            if label_item['label'] == label:
                # Concatenate text values with a space
                return ' '.join([value['text'] for value in label_item['value']])
        return None  # Return None if the label is not found

    # Extract static information using the helper function
    static_info = {
        'OriginalFileName':extract_label_value('document'),
        'AccountHolder': extract_label_value('AccountName'),
        'AccountEntity': extract_label_value('AccountEntity'),
        'ABN': extract_label_value('ABN'),
        'CorporateID': extract_label_value('CorporateID'),
        'MembershipNumber': extract_label_value('MembershipNumber'),
        'StatementDate': extract_label_value('StatementDate')
    }
    return static_info

