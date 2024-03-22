import os
from dotenv import load_dotenv
from pdf_processor import process_all_pdfs

# Load env variables from .env file
load_dotenv()

if __name__ == "__main__":
    input_folder = os.getenv("INPUT_FOLDER")
    output_folder = os.getenv("OUTPUT_FOLDER")
    process_all_pdfs(input_folder, output_folder)