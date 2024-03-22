import re
from pathlib import Path
import fitz  # PyMuPDF

def find_document_starts(pdf_path):
    """
    Identifies the starting pages of documents within a PDF file.
    
    This function scans through each page of a PDF file looking for a specific
    pattern ('1 of x') which denotes the beginning of a new document. It collects
    and returns the page numbers where new documents start.
    
    Args:
        pdf_path (str): The file path of the PDF to be processed.
        
    Returns:
        list: A list of page numbers where new documents start.
    """
    # Initialize a list to hold the starting pages of documents.
    doc_starts = []
    
    # Open the PDF file for processing.
    doc = fitz.open(pdf_path)
    
    # Iterate through each page in the PDF.
    for page_num in range(len(doc)):
        # Extract text from the current page.
        page_text = doc.load_page(page_num).get_text()
        
        # If the '1 of x' pattern is found, append the page number to the list.
        if re.search(r'\b1 of \d+', page_text):
            doc_starts.append(page_num)
    
    # Close the PDF after processing.
    doc.close()
    
    return doc_starts

def split_pdf(pdf_path, output_folder, doc_starts):
    """
    Splits a PDF into multiple documents based on the starting pages of each document.
    
    For each segment identified by the starting pages, a new PDF file is created
    in the specified output folder. The new files are named using the original
    PDF's name with a suffix indicating the document segment.
    
    Args:
        pdf_path (str): The file path of the PDF to be split.
        output_folder (str): The folder where the split PDFs will be saved.
        doc_starts (list): A list of page numbers where new documents start.
    """
    # Open the original PDF file.
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    pdf_name = Path(pdf_path).stem

    # Iterate through each document start page to split the PDF.
    for i, start_page in enumerate(doc_starts):
        # Determine the end page for the current document segment.
        end_page = doc_starts[i + 1] if i + 1 < len(doc_starts) else total_pages
        # Construct the output file path for the current segment.
        output_path = f"{output_folder}/{pdf_name}_statement_{i + 1}.pdf"
        
        # Create a new PDF for the current segment.
        new_doc = fitz.open()
        for page_num in range(start_page, end_page):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        # Save the new PDF segment.
        new_doc.save(output_path)
        new_doc.close()
    # Close the original PDF.
    doc.close()

def process_all_pdfs(input_folder, output_folder):
    """
    Processes all PDF files in a given folder, splitting them into separate documents.
    
    This function iterates over all PDF files in the input folder, identifies the
    starting pages of documents within each PDF, and splits them into separate PDF files.
    The new PDF files are saved to the specified output folder.
    
    Args:
        input_folder (str): The folder containing the PDF files to process.
        output_folder (str): The folder where the split PDFs will be saved.
    """
    # Iterate through each PDF file in the input folder.
    for pdf_file in Path(input_folder).glob('*.pdf'):
        pdf_path = str(pdf_file)
        # Find the starting pages of documents within the PDF.
        doc_starts = find_document_starts(pdf_path)
        if doc_starts:
            # Split the PDF into separate documents.
            split_pdf(pdf_path, output_folder, doc_starts)
        else:
            # Print a message if no '1 of x' pattern is found.
            print(f"No '1 of x' pattern found in {pdf_file.name}, skipping file.")
