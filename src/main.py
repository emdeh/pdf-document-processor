# src/main.py

import os
import glob
from os.path import basename
from dotenv import load_dotenv
from pdf_processor import PDFProcessor
from count_pdfs import PDFCounter
from csv_utils import CSVUtils
from doc_ai_utils import DocAIUtils
from prep_env import EnvironmentPrep
from utils import ask_user_to_continue

# Load env variables from .env file
load_dotenv()


def main():
    # Initialize environment preparation
    env_prep = EnvironmentPrep()
    initial_input_folder = os.getenv("INITIAL_INPUT_FOLDER")
    config_path = os.getenv("CONFIG_PATH")  # Yaml file with statement types

    # Create folders for the statement set
    (
        statement_set_name,
        ready_for_analysis,
        manual_splitting_folder,
        analysed_files_folder,
    ) = env_prep.create_folders()

    # Ask user if they want to skip pre-processing
    skip_preprocessing = input(
        "Do you want to skip the pre-processing (PDF splitting) step? (yes/no): "
    ).strip().lower()

    pdf_counter = PDFCounter()  # Instantiate PDFCounter here

    if skip_preprocessing == "yes":
        # Skip pre-processing steps
        print("Skipping pre-processing steps.\n")
        files_to_process_folder = ready_for_analysis

        # Ensure that the ready_for_analysis folder contains the files
        if not os.listdir(ready_for_analysis):
            # If the folder is empty, copy files from initial_input_folder
            env_prep.copy_files(initial_input_folder, ready_for_analysis)
            print(f"Copied files from {os.path.basename(initial_input_folder)} to {os.path.basename(ready_for_analysis)}.\n")
        else:
            print(f"Files already present in {os.path.basename(ready_for_analysis)}. Proceeding with those files.\n")

        # Count the number of files in ready_for_analysis
        (
            detailed_data,
            summary_data,
            total_files,
            total_pages,
        ) = pdf_counter.process_pdf_count([ready_for_analysis])
        files_to_go = total_files

        if files_to_go == 0:
            print(f"No files found in {os.path.basename(ready_for_analysis)} folder.")
            print("Exiting program.")
            exit()

    else:
        # Proceed with pre-processing
        # Count input PDFs
        (
            detailed_data_before,
            summary_data_before,
            total_pre_files,
            total_pre_pages,
        ) = pdf_counter.process_pdf_count([initial_input_folder])

        if total_pre_files == 0:
            print(f"No files found in {os.path.basename(initial_input_folder)} folder.")
            print(
                f"Checking for manually split files in the {os.path.basename(ready_for_analysis)} folder...\n"
            )
        else:
            pdf_counter.save_to_excel(
                detailed_data_before, summary_data_before, statement_set_name, "pre-split-counts.xlsx"
            )
            print(
                f"Saved pre-splitting count to {os.path.basename(statement_set_name)}.\n\n"
                f"Pre-splitting count is Files: {total_pre_files} Pages: {total_pre_pages}"
            )

            # Process all PDFs to split them into separate statements
            pdf_processor = PDFProcessor()
            pdf_processor.process_all_pdfs(
                initial_input_folder,
                ready_for_analysis,
                manual_splitting_folder,
            )

        # Count processed PDFs
        print(
            f"Counting files and pages of split statements saved to {os.path.basename(ready_for_analysis)}...\n"
        )
        (
            detailed_data_after,
            summary_data_after,
            total_post_files,
            total_post_pages,
        ) = pdf_counter.process_pdf_count([ready_for_analysis])
        pdf_counter.save_to_excel(
            detailed_data_after, summary_data_after, statement_set_name, "post-split-counts.xlsx"
        )
        print(
            f"Saved post-splitting count to {os.path.basename(statement_set_name)}.\n\n"
            f"Post-splitting count is Files: {total_post_files} Pages: {total_post_pages}"
        )

        # Check that total_pre_pages and total_post_pages match.
        if total_pre_pages == total_post_pages:
            print(
                "Total pre-splitting pages and total post-splitting pages match.\n"
                "This indicates that the splitting function has captured all data...\n"
            )
        else:
            print(
                f"### WARNING: Total pre-splitting pages and total post-splitting pages do not match.\n"
                f"The difference is {total_pre_pages - total_post_pages}.\n"
                f"This may indicate some files could not be split. If you are not re-running extraction on "
                f"manually split files. Look in the {os.path.basename(manual_splitting_folder)} for more details "
                f"on what to split manually.\n\n"
            )

        files_to_go = total_post_files
        files_to_process_folder = ready_for_analysis

        if files_to_go == 0:
            print("No files found to process. Exiting program.")
            exit()

        ask_user_to_continue()

    # Start processing
    # Load processing variables from .env
    doc_model_endpoint = os.getenv("MODEL_ENDPOINT")
    doc_model_api_key = os.getenv("MODEL_API_KEY")

    # Load the config file for different statement types
    env_prep.load_statement_config(config_path)

    # Prompt user to select statement type
    statement_type, selected_env_var = env_prep.select_statement_type()

    # Set the corresponding MODEL_ID variable from .env
    model_id = env_prep.set_model_id(selected_env_var)

    # Initialize the Azure Document Analysis Client
    doc_ai_utils = DocAIUtils()
    doc_ai_client = doc_ai_utils.initialise_analysis_client(
        doc_model_endpoint, doc_model_api_key, model_id
    )

    all_transactions = []
    all_summaries = []
    all_table_data = []

    print(f"Analysis has begun.\nNumber of files remaining: {files_to_go}.\n")

    csv_utils = CSVUtils()

    for document_path in glob.glob(os.path.join(files_to_process_folder, "*.pdf")):
        # Analyse the document
        original_document_name = basename(document_path)

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

    print(f"Writing extracted data to file...\n")
    csv_utils.write_transactions_and_summaries_to_excel(
        all_transactions,
        all_summaries,
        statement_set_name,
        "extracted-data.xlsx",
        table_data=all_table_data,
    )
    print(
        f"Extracted data written to the file 'extracted-data.xlsx' in {os.path.basename(statement_set_name)}.\n"
    )

    print("All done!")


if __name__ == "__main__":
    main()
