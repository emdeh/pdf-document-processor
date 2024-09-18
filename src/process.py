# process.py

import os
import argparse
from dotenv import load_dotenv
from prep_env import EnvironmentPrep
from doc_ai_utils import DocAIUtils
from csv_utils import CSVUtils

def main():
    # Load environment variables
    load_dotenv()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='PDF Processing Script')
    parser.add_argument('--input_folder', type=str, required=True, help='Path to the folder containing PDFs to process')
    parser.add_argument('--output_folder', type=str, required=True, help='Path to the output folder for results')
    parser.add_argument('--config_path', type=str, required=True, help='Path to the statement types configuration YAML file')
    parser.add_argument('--statement_type_name', type=str, required=True, help='Name of the statement type to use')
    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder
    config_path = args.config_path
    statement_type_name = args.statement_type_name

    # Load configuration
    env_prep = EnvironmentPrep()
    config = env_prep.load_statement_config(config_path)

    # Select statement type
    statement_type, selected_env_var = env_prep.select_statement_type(statement_type_name)

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

    files_to_process = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    files_to_go = len(files_to_process)

    # Create the analysed-files folder under output_folder
    analysed_files_folder = os.path.join(output_folder, "analysed-files")
    os.makedirs(analysed_files_folder, exist_ok=True)

    for document_path in files_to_process:
        # Analyze the document
        original_document_name = os.path.basename(document_path)

        if model_id == "prebuilt-layout":
            results = doc_ai_utils.analyse_layout_document(doc_ai_client, document_path)
            static_info = {"DocumentName": original_document_name}
            summary_info = {
                "TotalPages": len(results.pages),
                "DocumentName": original_document_name,
            }
            transactions = []

            # Extract table data
            tables = doc_ai_utils.extract_table_data(results)
            for table_idx, table in tables:
                for row in table:
                    row_data = {
                        "DocumentName": original_document_name,
                        "TableIndex": table_idx,
                    }
                    for col_idx, content in enumerate(row):
                        row_data[f"Column{col_idx + 1}"] = content
                    all_table_data.append(row_data)
        else:
            results = doc_ai_utils.analyse_document(doc_ai_client, model_id, document_path)
            print("Processing extracted data...\n")
            if not results:
                print(f"Error: No results found for {original_document_name}.")
                continue
            static_info = csv_utils.extract_static_info(
                results, original_document_name, statement_type
            )
            summary_info = csv_utils.extract_and_process_summary_info(
                results, statement_type
            )
            transactions = csv_utils.process_transactions(results, statement_type)

        # Start post-processing
        updated_transactions = []

        for transaction in transactions:
            combined_transaction = {**static_info, **transaction}
            updated_transactions.append(combined_transaction)

        static_info["DocumentName"] = original_document_name
        summary_info["DocumentName"] = original_document_name

        # Aggregate transactions and summary info
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
        statement_type=statement_type  # Pass statement_type here
    )

if __name__ == "__main__":
    main()
