# preprocess.py

import os
import argparse
from prep_env import EnvironmentPrep
from pdf_processor import PDFProcessor
from count_pdfs import PDFCounter

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='PDF Preprocessing Script')
    parser.add_argument('--input_folder', type=str, required=True, help='Path to the input folder containing PDFs')
    parser.add_argument('--output_folder', type=str, required=True, help='Path to the output folder for preprocessed PDFs')
    parser.add_argument('--statement_set_name', type=str, required=True, help='Name of the statement set')
    args = parser.parse_args()
    
    input_folder = args.input_folder
    output_folder = args.output_folder
    statement_set_name = args.statement_set_name
    
    # Create necessary folders
    env_prep = EnvironmentPrep()
    (
        statement_set_path,
        ready_for_analysis,
        manual_splitting_folder,
        analysed_files_folder,
    ) = env_prep.create_folders(statement_set_name, output_folder)
    
    # Count input PDFs
    pdf_counter = PDFCounter()
    (
        detailed_data_before,
        summary_data_before,
        total_pre_files,
        total_pre_pages,
    ) = pdf_counter.process_pdf_count([input_folder])
    
    # Save pre-split counts
    pdf_counter.save_to_excel(
        detailed_data_before, summary_data_before, statement_set_path, "pre-split-counts.xlsx"
    )
    
    # Process PDFs
    pdf_processor = PDFProcessor()
    pdf_processor.process_all_pdfs(
        input_folder,
        ready_for_analysis,
        manual_splitting_folder,
    )
    
    # Count processed PDFs
    (
        detailed_data_after,
        summary_data_after,
        total_post_files,
        total_post_pages,
    ) = pdf_counter.process_pdf_count([ready_for_analysis])
    
    # Save post-split counts
    pdf_counter.save_to_excel(
        detailed_data_after, summary_data_after, statement_set_path, "post-split-counts.xlsx"
    )
    
    # Output directories and files can be used by the processing script

if __name__ == "__main__":
    main()
