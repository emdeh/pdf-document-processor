import os
import glob
from os.path import basename
from dotenv import load_dotenv
from pdf_processor import process_all_pdfs
from count_pdfs import process_folders, save_to_excel
from csv_utils import extract_static_info, process_transactions, extract_summary_info, write_data_to_excel
from doc_ai_utils import initialise_analysis_client, analyse_document
from prep_env import create_folders
import os
from prep_env import create_folders

# Load env variables from .env file
load_dotenv()

if __name__ == "__main__":

    initial_input_folder = os.getenv("INITIAL_INPUT_FOLDER")
    #output_folder = os.getenv("OUTPUT_FOLDER")
    #pre_process_count = os.getenv("PDF_COUNT_PRE_OUTPUT_FILE")
    #post_process_count = os.getenv("PDF_COUNT_POST_OUTPUT_FILE")
    #extracted_data_output = os.getenv("EXTRACTED_DATA_OUTPUT")
    doc_model_endpoint = os.getenv("MODEL_ENDPOINT")
    doc_model_api_key = os.getenv("MODEL_API_KEY")
    doc_model_id = os.getenv("MODEL_ID")
    #manual_processing_folder = os.getenv("FILES_TO_SPLIT_MANUALLY")

    # Prepare environment
    statement_set_name, split_files_folders, manual_splitting_folder = create_folders()
    
    # Count input PDFs
    print(f"Counting files and pages in {initial_input_folder}...\n")
    detailed_data_before, summary_data_before = process_folders([initial_input_folder])
    save_to_excel(detailed_data_before, summary_data_before, statement_set_name, "pre-split-counts.xlsx")
    print(f"Saved pre-splitting count to {statement_set_name}.\n\n")

    # Process all PDFs to split them into separate statements
    print(f"Splitting files in {initial_input_folder} and saving individual statements to {split_files_folders}...\n")
    process_all_pdfs(initial_input_folder, split_files_folders, manual_splitting_folder)
    print(f"Splitting complete.\n\n")

    # Count processed PDFs
    print(f"Counting files and pages of split statements saved to {split_files_folders}...\n")
    detailed_data_after, summary_data_after = process_folders([split_files_folders])
    save_to_excel(detailed_data_after,summary_data_after, statement_set_name, "post-split-counts.xlsx")
    print(f"Saved post-splitting count to {statement_set_name}.\n\n")

    # Initialise the Azure Document Analysis Client
    print("Initialising Document Intelligence Client...\n")
    doc_ai_client = initialise_analysis_client(doc_model_endpoint,doc_model_api_key)
    print(f"Document Intelligence Client {doc_ai_client} ready at endpoint {doc_model_endpoint}.\n Preparing to extract data...\n")

    all_transactions = []
    all_summaries = []

    for document_path in glob.glob(os.path.join(split_files_folders, '*.pdf')):
        # Analyse the document
        print(f"Analysing {document_path}...\n")
        original_document_name = basename(document_path)
        results = analyse_document(doc_ai_client, doc_model_id, document_path)
        print(f"Analysed {document_path}...\n")

        # Process the results
        print("Processing extracted data...\n")
        static_info = extract_static_info(results, original_document_name)
        summary_info = extract_summary_info(results)
        transactions = process_transactions(results)

        updated_transactions = []

        for transaction in transactions:
            # Combine dictionaries with static info first
            combined_transaction = {**static_info, **transaction}
            updated_transactions.append(combined_transaction)

        static_info['DocumentName'] = original_document_name
        summary_info['DocumentName'] = original_document_name

        # Aggregate transactions and summary info
        all_transactions.extend(updated_transactions)
        all_summaries.append(summary_info)
        
        print(f"Data extraction processed!\nData aggregated for {document_path}.")

    # once all documents processed, write data to Excel
    print(f"Writing extracted data to {statement_set_name} folder...\n")
    extracted_data = os.path.join(statement_set_name, "extracted-data.xlsx")
    write_data_to_excel(all_transactions, all_summaries, extracted_data)