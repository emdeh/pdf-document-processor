import pandas as pd
import fitz  # PyMuPDF
import os
from pathlib import Path

def count_pdf_pages(pdf_path):
    """
    Counts the number of pages in a PDF document.

    Args:
        pdf_path (str): The path to the PDF document.

    Returns:
        int: The number of pages in the PDF document. Returns 0 if there was an error processing the document.
    """
    try:
        with fitz.open(pdf_path) as doc:
            return len(doc)
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return 0

def process_pdf_count(folders):
    """
    Process the count of PDF files and pages in the given folders.
    This function takes a list of folder paths or a single folder path and counts the number of PDF files
    and pages in each folder. It returns detailed data for each PDF file, summary data for each folder,
    and the total number of PDF files and pages across all folders.

    Args:
        folders (list or str): A list of folder paths or a single folder path.

    Returns:
            tuple: A tuple containing the following:
                    - detailed_data (list): A list of lists containing detailed data for each PDF file.
                        Each inner list contains the folder path, PDF file name, and number of pages.
                    - summary_data (list): A list of lists containing summary data for each folder.
                        Each inner list contains the folder path, number of PDF files, and total number of pages.
                    - total_files (int): The total number of PDF files across all folders.
                    - total_pages (int): The total number of pages across all PDF files.
    """

    # If folders is not a list, make it a list
    if not isinstance(folders, list):
        folders = [folders]

    detailed_data = []
    summary_data = []
    total_files = 0
    total_pages = 0

    for folder in folders:
        print(f"Counting files and pages in {os.path.basename(folder)}...\n")

        # Ensure folder is a Path object for easier manipulation
        folder_path = Path(folder)
        folder_files = 0
        folder_pages = 0

        # Iterate only files directly in the given folder
        for pdf_file in folder_path.glob('*.pdf'):
            pdf_path = str(pdf_file)
            pages = count_pdf_pages(pdf_path)
            folder_files += 1
            folder_pages += pages
            detailed_data.append([folder, pdf_file.name, pages])

        summary_data.append([folder, folder_files, folder_pages])
        total_files += folder_files
        total_pages += folder_pages

    summary_data.append(['Total', total_files, total_pages])

    return detailed_data, summary_data, total_files, total_pages

def save_to_excel(detailed_data, summary_data, output_excel_path, output_filename):
    """
    Saves the detailed and summary data to an Excel file.

    Args:
        detailed_data (list): A list of tuples containing the detailed data.
            Each tuple should have the following elements:
            - Folder (str): The folder name.
            - Document Name (str): The document name.
            - Total Pages (int): The total number of pages in the document.
        summary_data (list): A list of tuples containing the summary data.
            Each tuple should have the following elements:
            - Folder (str): The folder name.
            - Number of Documents (int): The number of documents in the folder.
            - Total Pages (int): The total number of pages in the folder.
        output_excel_path (str): The path to the output Excel file.
        output_filename (str): The name of the output Excel file.

    Returns:
        None
    """
    detailed_df = pd.DataFrame(detailed_data, columns=['Folder', 'Document Name', 'Total Pages'])
    summary_df = pd.DataFrame(summary_data, columns=['Folder', 'Number of Documents', 'Total Pages'])

    output_file_path = os.path.join(output_excel_path, output_filename)

    # Check if the file already exists
    if os.path.exists(output_file_path):
        # Append data to the existing file
        with pd.ExcelWriter(output_file_path, engine='openpyxl', mode='a', if_sheet_exists='new') as writer:
            detailed_df.to_excel(writer, sheet_name='Pages Per Document', index=False, header=True)
            summary_df.to_excel(writer, sheet_name='Summary', index=False, header=True)
        print(f"Data appended to the file '{os.path.basename(output_filename)}' in {os.path.basename(output_excel_path)}.")

    else:
        # Create a new file
        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            detailed_df.to_excel(writer, sheet_name='Pages Per Document', index=False, header=True)
            summary_df.to_excel(writer, sheet_name='Summary', index=False, header=True)
        print(f"New file '{output_filename}' created in {os.path.basename(output_excel_path)}.")
        print(f"Data written to the file '{os.path.basename(output_filename)}' in {os.path.basename(output_excel_path)}.\n")









