import os
from dotenv import load_dotenv
from pdf_processor import find_document_starts, split_pdf

# Load env variables from .env file
load_dotenv()

if __name__ == "__main__":
    pdf_path = os.getenv("PDF_PATH")
    output_folder = os.getenv("OUTPUT_FOLDER")
    doc_starts = find_document_starts(pdf_path)
    split_pdf(pdf_path, output_folder, doc_starts)
    