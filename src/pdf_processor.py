import re
from pathlib import Path
import shutil
import fitz  # PyMuPDF
import os

def process_all_pdfs(input_folder, output_folder, manual_processing_folder):
    """
    Processes all PDF files in a given folder, splitting them into separate documents based on identified patterns.

    This function iterates over all PDF files in the input folder and identifies the document type and the starting pages
    of documents within each PDF. It then splits the PDF files into separate documents and saves them to the specified
    output folder. If a known pattern is not found, the PDF file is moved to the manual processing folder.

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
        elif doc_type == 'bom_statement':
            doc_starts = find_bom_statement_starts(pdf_path)
        elif doc_type == 'bendigo_statement':
            doc_starts = find_bendigo_statement_starts(pdf_path)
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

def detect_document_type(pdf_path):
    """
    Detects the type of a PDF document based on its content.

    Parameters:
    pdf_path (str): The path to the PDF document.

    Returns:
    str: The detected document type. Possible values are 'bendigo_statement',
         'bom_statement', 'standard_statement', or 'unknown'.
    """
    doc = fitz.open(pdf_path)
    first_pages_text = ''.join([doc.load_page(i).get_text() for i in range(min(9, len(doc)))])  # Analyze the first 9 pages

    if "Bendigo" in first_pages_text:
        doc.close()
        print("Bendigo Bank statement detected.")
        return 'bendigo_statement'
    
    elif "FREEDOM" in first_pages_text:
        doc.close()
        print("Bank of Melbourne OR St. George statement detected.")
        return 'bom_statement'
    
    elif re.search(r'\b1 of \d', first_pages_text):
        doc.close()
        print("Standard statement detected.")
        return 'standard_statement'
    
    doc.close()
    return 'unknown'

def find_standard_statement_starts(pdf_path):
    """
    Standard function for statements that have '1 of x' pattern.
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

def find_bendigo_statement_starts(pdf_path):
    """
    New function for Bendigo Bank statements that don't have '1 of x' pattern.
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

def find_bom_statement_starts(pdf_path):
    """
    TO-DO: Still not working perfectly - for Bank of Melbourne and St. George statements.
    
    Identifies the starting pages of documents within a PDF file.
    
    This function scans through each page of a PDF file looking for a specific
    pattern '(page 1 of x)' which denotes the beginning of a new document. It collects
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
        if re.search(r'\(page\s+1 of \d+\)', page_text): # works better??
            doc_starts.append(page_num)

        # if re.search(r'Statement No\.\s+(\d+)\s*\((page\s+1 of \d+)\)', page_text): # works kinda

    # Close the PDF after processing.
    doc.close()
    
    return doc_starts

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
  