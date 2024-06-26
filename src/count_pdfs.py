import pandas as pd
import fitz  # PyMuPDF
import os
from pathlib import Path

def count_pdf_pages(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            return len(doc)
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return 0

def process_pdf_count(folders):

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









