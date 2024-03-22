import os
from dotenv import load_dotenv
from pdf_processor import process_all_pdfs
from count_pdfs import process_folders, save_to_excel, count_pdf_pages

# Load env variables from .env file
load_dotenv()

if __name__ == "__main__":
    input_folder = os.getenv("INPUT_FOLDER")
    output_folder = os.getenv("OUTPUT_FOLDER")
    pre_process_count = os.getenv("PDF_COUNT_PRE_OUTPUT_FILE")
    post_process_count = os.getenv("PDF_COUNT_POST_OUTPUT_FILE")

    # Count input PDFs
    detailed_data_before, summary_data_before = process_folders([input_folder])
    save_to_excel(detailed_data_before,summary_data_before,pre_process_count)
  
    # Process all PDFs to split them into separate statements
    process_all_pdfs(input_folder, output_folder)

    # Count processed PDFs
    detailed_data_after, summary_data_after = process_folders([output_folder])
    save_to_excel(detailed_data_after,summary_data_after,post_process_count)


    