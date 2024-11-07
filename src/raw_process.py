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
        description='''\
        PDF Processing Script
                                     
        This script takes a preprocessed folder of PDFs each containing individual statements and extracts the RAW DATA into an excel file.
        It creates a folder within the --input folder and saves the excel into that folder.
        The excel is saved as "extracted-data.xlsx"''',        
        formatter_class=argparse.RawDescriptionHelpFormatter,                                     
        epilog = '''Example: python src/raw_process.py -i PATH/TO/PDFS'''
        )
    
    parser.add_argument(
        '-i', '--input', 
        type=str, 
        required=True, 
        help='Path to the input folder containing preprocessed PDFs'
    )
    
    args = parser.parse_args()

    input_dir = args.input
    output_folder = args.input #Output folder for processed PDFs will be created inside the initial input folder
    config_type = "config/type_models.yaml"
    type = "Raw-extract"

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
    all_text = []

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

        # Extract table data from the results
        extracted_text = doc_ai_utils.extract_all_text(results)
        all_text.append({
            "Document Name": original_document_name,
            "Extracted Text": extracted_text    
        })

    # Move the analysed file to the analysed-files folder
    env_prep.move_analysed_file(document_path, analysed_files_folder)

    files_to_go -= 1
    print(f"Number of files remaining: {files_to_go}.\n")

    # Write extracted data to Excel
    if all_text:
        csv_utils.write_raw_data_to_excel(
            all_text,
            output_folder,
            "extracted-data.xlsx"
        )
    else:
        print("No data extracted from the documents.")

    # end time
    end_time = time.time()
    # Calculate time taken and print as hh:mm:ss
    print(f"Time taken: {time.strftime('%H:%M:%S', time.gmtime(end_time - start_time))}")

if __name__ == "__main__":
    main()