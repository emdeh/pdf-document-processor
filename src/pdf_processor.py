import re
from pathlib import Path
import shutil
import fitz  # PyMuPDF
import os

def process_all_pdfs(input_folder, output_folder, manual_processing_folder): # new core process_all_pdfs function
    """
    Processes all PDF files in a given folder, splitting them into separate documents based on identified patterns.

    This function iterates over all PDF files in the input folder, identifies the
    document type and the starting pages of documents within each PDF, and splits
    them into separate PDF files. The new PDF files are saved to the specified output folder.
    If no known pattern is found, the PDF file is moved to the manual processing folder.

    Args:
        input_folder (str): The folder containing the PDF files to process.
        output_folder (str): The folder where the split PDFs will be saved.
        manual_processing_folder (str): The folder where the PDF files without a known pattern will be moved.
    """
    print(f"Splitting files in {input_folder} and saving individual documents to {output_folder}...\n")
    # Iterate through each PDF file in the input folder
    for pdf_file in Path(input_folder).glob('*.pdf'):
        pdf_path = str(pdf_file)
        # Detect document type based on the initial pages content
        doc_type = detect_document_type(pdf_path)

        if doc_type == 'standard_statement':
            doc_starts = find_standard_statement_starts(pdf_path)
        elif doc_type == 'statement_numbers':
            doc_starts = find_statement_numbers_starts(pdf_path)
        else:
            doc_starts = None

        if doc_starts:
            # Split the PDF into separate documents.
            split_pdf(pdf_path, output_folder, doc_starts)
            print(f"{os.path.basename(pdf_file)} has been processed and split accordingly.\n")
        else:
            # Copy the PDF file to the manual processing folder if can't be split.
            print(f"Could not identify document pattern for {os.path.basename(pdf_file)}, moving to manual processing folder.\n")
            shutil.copy(pdf_path, manual_processing_folder)
            # Create or update a manifest file for the unsplit files.
            manifest_path = os.path.join(manual_processing_folder, "manifest-of-unsplit-files.txt")
            with open(manifest_path, 'a') as manifest_file:
                manifest_file.write(f"{pdf_file.stem}\n")

    print(f"Splitting complete.\n\n")

def detect_document_type(pdf_path): # Function used to detect document type to determine which find function to use
    doc = fitz.open(pdf_path)
    first_pages_text = ''.join([doc.load_page(i).get_text() for i in range(min(3, len(doc)))])  # Analyze the first 3 pages

    if "Bendigo" in first_pages_text:
        doc.close()
        print("Bendigo Bank statement detected.")
        return 'statement_numbers'
    elif re.search(r'\b1 of \d+', first_pages_text):
        doc.close()
        print("Standard statement detected.")
        return 'standard_statement'
    doc.close()
    return 'unknown'

def find_standard_statement_starts(pdf_path): # Standard function for statements that have '1 of x' pattern
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

def find_statement_numbers_starts(pdf_path): # New function for Bendigo Bank statements that don't have '1 of x' pattern
    """
    Identifies the starting pages of documents within a PDF file based on 'Statement Number'
    and checks for the ending with 'Continued overleaf...' absence.

    This function scans through each page of a PDF file looking for a unique 'Statement Number X'
    pattern which denotes the beginning of a new document. It also identifies the end of a document
    when 'Continued overleaf...' is not present on a page that follows a started document.
    
    Args:
        pdf_path (str): The file path of the PDF to be processed.
        
    Returns:
        dict: A dictionary with keys as the statement number and values as dictionaries
              containing 'start' and 'end' pages for each document.
    """
    doc = fitz.open(pdf_path)
    statement_starts = {}
    current_statement = None

    for page_num in range(len(doc)):
        page_text = doc.load_page(page_num).get_text()
        match = re.search(r'Statement number\s+(\d+)', page_text)
        if match:
            statement_number = int(match.group(1))
            if statement_number != current_statement:
                if current_statement is not None:
                    statement_starts[current_statement]['end'] = page_num - 1
                current_statement = statement_number
                statement_starts[statement_number] = {'start': page_num}
        elif "Continued overleaf..." not in page_text and current_statement is not None:
            statement_starts[current_statement]['end'] = page_num
            current_statement = None

    # Ensure the last statement is closed if it doesn't end explicitly
    if current_statement and 'end' not in statement_starts[current_statement]:
        statement_starts[current_statement]['end'] = len(doc) - 1

    doc.close()
    return statement_starts

def split_pdf(pdf_path, output_folder, doc_starts): # new splitting function
    """
    Splits a PDF into multiple documents based on the starting pages of each document.
    This function can handle both lists of page numbers (from find_standard_statement_starts)
    and dictionaries of page numbers with start and end pages (from find_statement_numbers_starts).

    Args:
        pdf_path (str): The file path of the PDF to be split.
        output_folder (str): The folder where the split PDFs will be saved.
        doc_starts (list or dict): A list or dictionary of page numbers where new documents start.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    pdf_name = Path(pdf_path).stem

    # Check if doc_starts is a list or a dictionary and adjusts the processing logic accordingly.
    if isinstance(doc_starts, list):
        # Handle list of starts (standard document starts)
        for i, start_page in enumerate(doc_starts):
            end_page = doc_starts[i + 1] if i + 1 < len(doc_starts) else total_pages
            output_path = f"{output_folder}/{pdf_name}_document_{i + 1}.pdf"
            new_doc = fitz.open()
            for page_num in range(start_page, end_page):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            new_doc.save(output_path)
            new_doc.close()

    elif isinstance(doc_starts, dict):
        # Handle dictionary of starts and ends (statement numbers starts)
        for statement, pages in doc_starts.items():
            start_page = pages['start']
            end_page = pages['end']
            output_path = f"{output_folder}/{pdf_name}_statement_{statement}.pdf"
            new_doc = fitz.open()
            for page_num in range(start_page, end_page + 1):  # '+1' to include end page
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            new_doc.save(output_path)
            new_doc.close()

    doc.close()
  