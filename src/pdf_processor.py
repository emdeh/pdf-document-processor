import fitz  # PyMuPDF
import re
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def find_document_starts(pdf_path):
    doc_starts = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page_text = doc.load_page(page_num).get_text()
        if re.search(r'\b1 of \d+', page_text):
            doc_starts.append(page_num)
    doc.close()
    return doc_starts

def split_pdf(pdf_path, output_folder, doc_starts):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    pdf_name = Path(pdf_path).stem

    for i, start_page in enumerate(doc_starts):
        end_page = doc_starts[i + 1] if i + 1 < len(doc_starts) else total_pages
        output_path = f"{output_folder}/{pdf_name}_statement_{i + 1}.pdf"
        new_doc = fitz.open()
        for page_num in range(start_page, end_page):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        new_doc.save(output_path)
        new_doc.close()
    doc.close()

def process_all_pdfs(input_folder, output_folder):
    for pdf_file in Path(input_folder).glob('*.pdf'):
        pdf_path = str(pdf_file)
        doc_starts = find_document_starts(pdf_path)
        if doc_starts:
            split_pdf(pdf_path, output_folder, doc_starts)
        else:
            print(f"No '1 of x' pattern found in {pdf_file.name}, skipping file.")
