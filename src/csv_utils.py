import csv
import json

# Function to prepare the CSV file with headers for output
def create_output_file(csv_output):
    with open(csv_output, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['AccountHolder', 'AccountEntity', 'ABN', 'CorporateID', 'MembershipNumber', 'StatementDate', 'TransactionDate', 'TransactionDescription', 'TransactionAmount', 'CRifCredit'])

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
            if transaction_date is None:
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

def extract_label_value(data, label_path, default=''):
    """Utility function to extract concatenated text values for a given label path."""
    for label in data.get('labels', []):
        if label['label'] == label_path:
            # Concatenate text values with a space
            return ' '.join([value['text'] for value in label['value']])
    return default