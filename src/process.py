# process.py

import os
import argparse
from dotenv import load_dotenv
from prep_env import EnvironmentPrep
from doc_ai_utils import DocAIUtils
from csv_utils import CSVUtils
import pandas as pd
import time

def main():
    # Start time
    start_time = time.time()
    # Load environment variables
    load_dotenv()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='''PDF Processing Script
                                     
        This script takes a preprocessed folder of PDFs each containing individual statements and extracts the information into an excel file.
        The input requires the user to specify what type of statement is being accessed. The available types can be found in the type_models.yaml.
        The config argument is pre-defined but can be changed if required.
        ''',
                                     
        epilog = '''Example: python src/process.py --input PATH/TO/PREPROCESSED PDFS --type "AMEX - Card Statement"
        '''
        )
    parser.add_argument(
        '--input', 
        type=str, 
        required=True, 
        help='Path to the input folder containing preprocessed PDFs'
        )
    parser.add_argument(
        '--config_type', 
        type=str, 
        default='/config/type_models.yaml', 
        help='Path to the statement types configuration YAML file'
        )
    parser.add_argument(
        '--type', 
        type=str, 
        required=True, 
        help='Name of the statement type to use'
        )
    args = parser.parse_args()

    input_dir = args.input
    output_folder = args.input #Output folder for processed PDFs will be created inside the initial input folder
    config_type = args.config_type
    type = args.type

    # Load configuration
    env_prep = EnvironmentPrep()
    config = env_prep.load_statement_config(config_type)

    # Select statement type
    statement_type, selected_env_var = env_prep.select_statement_type(type)

    # Set model_id using the environment variable from .env
    model_id = env_prep.set_model_id(selected_env_var)

    # Read model endpoint and API key from environment variables
    model_endpoint = os.getenv("MODEL_ENDPOINT")
    model_api_key = os.getenv("MODEL_API_KEY")

    if not model_endpoint or not model_api_key:
        print("Error: MODEL_ENDPOINT and MODEL_API_KEY must be set in the .env file.")
        exit(1)

    # Initialize Document Analysis Client
    doc_ai_utils = DocAIUtils()
    doc_ai_client = doc_ai_utils.initialise_analysis_client(
        model_endpoint, model_api_key, model_id
    )

    # Process PDFs
    csv_utils = CSVUtils()
    all_transactions = []
    all_summaries = []
    all_table_data = []

    files_to_process = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    files_to_go = len(files_to_process)

    # Create the analysed-files folder under output_folder
    analysed_files_folder = os.path.join(output_folder, "analysed-files")
    os.makedirs(analysed_files_folder, exist_ok=True)

    for document_path in files_to_process:
        # Analyze the document
        original_document_name = os.path.basename(document_path)

        # Analyze document and extract static info, summary, transactions
        results = doc_ai_utils.analyse_document(doc_ai_client, model_id, document_path)
        print("Processing extracted data...\n")
        if not results:
            print(f"Error: No results found for {original_document_name}.")
            continue

        static_info = csv_utils.extract_static_info(results, original_document_name, statement_type)
        summary_info = csv_utils.extract_and_process_summary_info(results, original_document_name, statement_type)
        transactions = csv_utils.process_transactions(results, statement_type)

        # **Debugging: Print summary_info**
        # print(f"Summary Info for {original_document_name}: {summary_info}")

        # **Assign years for each document’s transactions individually**
        if 'StatementStartDate' in summary_info and 'StatementEndDate' in summary_info:
            statement_start_date = summary_info['StatementStartDate']['value']
            statement_end_date = summary_info['StatementEndDate']['value']

                # Add these lines to include dates in static_info
            static_info['StatementStartDate'] = statement_start_date
            static_info['StatementEndDate'] = statement_end_date

            # Convert transactions list to a DataFrame
            transactions_df = pd.DataFrame(transactions)
            # print("Initial Transactions DataFrame:\n", transactions_df[['Date']].head())

            # Debugging: Check if Date column is present and in the expected format
            #if 'Date' in transactions_df.columns:
            #    print("Initial Transactions DataFrame - Date Column:\n", transactions_df[['Date']].head())
            #else:
            #    print("Error: 'Date' column missing from transactions.")
            #    continue  # Skip to next file if 'Date' is missing

            # **Convert 'Date' column to datetime before assigning years**
            transactions_df['Date'] = pd.to_datetime(
                transactions_df['Date'], 
                format='%d %b',  # Adjust format if necessary
                errors='coerce'
            )
            # print("Transactions DataFrame after parsing 'Date':\n", transactions_df[['Date']].head())

            # Assign years to transaction dates for this document
            transactions_df = csv_utils.assign_years_to_dates(transactions_df, statement_start_date, statement_end_date)

            # Verify the assignment
            # print("Transactions DataFrame after assigning years:\n", transactions_df[['Date']].head())

            # Convert back to list of dictionaries for consistency
            transactions = transactions_df.to_dict(orient='records')

        else:
            print("Warning: 'StatementStartDate' or 'StatementEndDate' missing in summary_info.")

        # Add static info to each transaction
        updated_transactions = []
        for transaction in transactions:
            combined_transaction = {**static_info, **transaction}
            updated_transactions.append(combined_transaction)

        # Aggregate transactions and summaries
        all_transactions.extend(updated_transactions)
        all_summaries.append(summary_info)

        print(f"Data aggregated for:\n{os.path.basename(document_path)}.\n")

        # Move the analysed file to the analysed-files folder
        env_prep.move_analysed_file(document_path, analysed_files_folder)

        files_to_go -= 1
        print(f"Number of files remaining: {files_to_go}.\n")

    print(f"Total transactions extracted: {len(all_transactions)}")
    print(f"Total summaries extracted: {len(all_summaries)}")

    # Write extracted data to Excel
    csv_utils.write_transactions_and_summaries_to_excel(
        all_transactions,
        all_summaries,
        output_folder,
        "extracted-data.xlsx",
        table_data=all_table_data,
        statement_type=statement_type,  # Pass statement_type here
        static_info=static_info
    )
    # end time
    end_time = time.time()
    # Calculate time taken and print as hh:mm:ss
    print(f"Time taken: {time.strftime('%H:%M:%S', time.gmtime(end_time - start_time))}")

if __name__ == "__main__":
    main()