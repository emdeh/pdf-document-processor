import os
import glob
from os.path import basename
from dotenv import load_dotenv
from pdf_processor import process_all_pdfs
from count_pdfs import process_folders, save_to_excel
from csv_utils import extract_static_info, process_transactions, extract_summary_info, write_data_to_excel
from doc_ai_utils import initialise_analysis_client, analyse_document
from prep_env import create_folders, move_analysed_file
import os
from prep_env import create_folders
import os

# Load env variables from .env file
load_dotenv()

if __name__ == "__main__":

    initial_input_folder = os.getenv("INITIAL_INPUT_FOLDER")
    doc_model_endpoint = os.getenv("MODEL_ENDPOINT")
    doc_model_api_key = os.getenv("MODEL_API_KEY")
    doc_model_id = os.getenv("MODEL_ID")
    

    # Prepare environment
    statement_set_name, ready_for_analysis, manual_splitting_folder, analysed_files_folder = create_folders()
    
    # Count input PDFs
    print(f"Counting files and pages in {os.path.basename(initial_input_folder)}...\n")
    detailed_data_before, summary_data_before, total_pre_files, total_pre_pages = process_folders([initial_input_folder])

    if total_pre_files == 0:
        print(f"No files found in {os.path.basename(initial_input_folder)} folder.")
        print(f"Checking for manually split files in the {os.path.basename(ready_for_analysis)} folder...\n")
    else:
        save_to_excel(detailed_data_before, summary_data_before, statement_set_name, "pre-split-counts.xlsx")
        print(f"Saved pre-splitting count to {os.path.basename(statement_set_name)}.\n\n Pre-splitting count is Files: {total_pre_files} Pages: {total_pre_pages}")

        # Process all PDFs to split them into separate statements
        print(f"Splitting files in {initial_input_folder} and saving individual statements to {ready_for_analysis}...\n")
        process_all_pdfs(initial_input_folder, ready_for_analysis, manual_splitting_folder)
        print(f"Splitting complete.\n\n")

    # Count processed PDFs
    print(f"Counting files and pages of split statements saved to {os.path.basename(ready_for_analysis)}...\n")
    detailed_data_after, summary_data_after, total_post_files, total_post_pages = process_folders([ready_for_analysis])
    save_to_excel(detailed_data_after,summary_data_after, statement_set_name, "post-split-counts.xlsx")
    print(f"Saved post-splitting count to {os.path.basename(statement_set_name)}.\n\nPost-splitting count is Files: {total_post_files} Pages: {total_post_pages}")

    # Check that total_pre_pages and total_post_pages match. If they do tell the user, if not warn the user then continue.
    if total_pre_pages == total_post_pages:
        print("Total pre-splitting pages and total post-splitting pages match.\nThis indicates that the splitting function has captured all data...\n")
    else:
        print(f"### WARNING: Total pre-splitting pages and total post-splitting pages do not match.\nThe difference is {total_pre_pages - total_post_pages}.\nThis may indicate some files could not be split. If you are not re-running extraction on manually split files. Look in the {os.path.basename(manual_splitting_folder)} for more details on what to split manually.\n\n")
    
    files_to_go = total_post_files
    # If files_to_go is 0, there are no files to process, quit the program
    if files_to_go == 0:
        print("No files to process. Exiting program.")
        quit()

    # Initialise the Azure Document Analysis Client
    print("Initialising Document Intelligence Client...\n")
    doc_ai_client = initialise_analysis_client(doc_model_endpoint,doc_model_api_key)
    print(f"Document Intelligence Client established with Endpoint: {doc_model_endpoint}.\nUsing {doc_model_id}.\nPreparing to extract data...\n\n")

    all_transactions = []
    all_summaries = []
    
    print(F"Analysis has begun.\nNumber of files remaining: {files_to_go}.\n")
    for document_path in glob.glob(os.path.join(ready_for_analysis, '*.pdf')):
        # Analyse the document
        print(f"Analysing:\n{os.path.basename(document_path)}.\n\n")
        original_document_name = basename(document_path)
        results = analyse_document(doc_ai_client, doc_model_id, document_path)
        print(f"Analysed:\n{os.path.basename(document_path)}.\n")

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

        print(f"Data aggregated for:\n{os.path.basename(document_path)}.\n")

        # Move the analysed file to the analysed-files folder
        move_analysed_file(document_path, analysed_files_folder)

        files_to_go -= 1
        print(f"Number of files remaining: {files_to_go}.\n")
   
    print(f"Writing extracted data to file...\n")
    write_data_to_excel(all_transactions, all_summaries, statement_set_name, "extracted-data.xlsx")
    print(f"Extracted data written to the file 'extracted-data.xlsx' in {os.path.basename(statement_set_name)}.\n")

    print("All done!")
    
