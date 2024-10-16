# preprocess.py

import os
import argparse
from prep_env import EnvironmentPrep
from pdf_processor import PDFProcessor
from count_pdfs import PDFCounter

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='''PDF Preprocessing Script.
        
        This script splits PDF files containing multiple statements into individual files to prepare them for processing. 
        It creates a folder within the --input folder based on the --name given.
        Within this folder it creates necessary folders, counts PDFs before and after splitting them, saves the counts to Excel files,
        and stores the split files.''',
        
        epilog='''Example: python src/preprocess.py --input PATH/TO/PDFS --name statement_run_1'''
    )

    
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Path to the input folder containing PDFs that need to be split.'
        )
    
    parser.add_argument(
        '-n', '--name',
        type=str,
        required=True,
        help='Name of the pre-process run - the folder created within the input folder will be named after this.'
        )
    
    args = parser.parse_args()
    
    input_dir = args.input
    output_folder = input_dir # Output folder for preprocessed PDFs will be created inside the given input folder
    name = args.name
    
    # Create necessary folders
    env_prep = EnvironmentPrep()
    (
        statement_set_path,
        ready_for_analysis,
        manual_splitting_folder,
        analysed_files_folder,
    ) = env_prep.create_folders(name, output_folder)
    
    # Count input PDFs
    pdf_counter = PDFCounter()
    (
        detailed_data_before,
        summary_data_before,
        total_pre_files,
        total_pre_pages,
    ) = pdf_counter.process_pdf_count([input_dir])
    
    # Save pre-split counts
    pdf_counter.save_to_excel(
        detailed_data_before, summary_data_before, statement_set_path, "pre-split-counts.xlsx"
    )
    
    # Process PDFs
    pdf_processor = PDFProcessor()
    pdf_processor.process_all_pdfs(
        input_dir,
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
