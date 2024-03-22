import fitz  # PyMuPDF
import re

def find_document_starts(pdf_path):
    """
    Scans through the PDF to find pages that start with "1 of x" pattern,
    indicating the beginning of a new document.
    
    :param pdf_path: Path to the PDF file to be processed.
    :return: A list of page numbers where new documents start.
    """
    doc_starts = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page_text = doc.load_page(page_num).get_text()
        if re.search(r'\b1 of \d+', page_text):
            doc_starts.append(page_num)

    doc.close()
    return doc_starts

def split_pdf(pdf_path, output_folder, doc_starts):
    """
    Splits the PDF into multiple documents based on the starting page numbers
    provided in doc_starts.
    
    :param pdf_path: Path to the PDF file to be split.
    :param output_folder: Folder where the split PDFs will be saved.
    :param doc_starts: A list of page numbers indicating where new documents start.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    for i, start_page in enumerate(doc_starts):
        # Determine the end page for the current document segment
        end_page = doc_starts[i + 1] if i + 1 < len(doc_starts) else total_pages
        output_path = f"{output_folder}/document_{i + 1}.pdf"

        # Create a new PDF with the pages for the current document segment
        new_doc = fitz.open()
        for page_num in range(start_page, end_page):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        new_doc.save(output_path)
        new_doc.close()

    doc.close()
