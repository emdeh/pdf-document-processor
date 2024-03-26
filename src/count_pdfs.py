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

def process_folders(folders):
    detailed_data = []
    summary_data = []

    for folder in folders:
        # Ensure folder is a Path object for easier manipulation
        folder_path = Path(folder)
        total_pdfs = 0
        total_pages = 0

        # Iterate only files directly in the given folder
        for pdf_file in folder_path.glob('*.pdf'):
            pdf_path = str(pdf_file)
            pages = count_pdf_pages(pdf_path)
            total_pdfs += 1
            total_pages += pages
            detailed_data.append([folder, pdf_file.name, pages])

        summary_data.append([folder, total_pdfs, total_pages])

    return detailed_data, summary_data

def save_to_excel(detailed_data, summary_data, output_csv_path, output_filename):
    detailed_df = pd.DataFrame(detailed_data, columns=['Folder', 'Document Name', 'Total Pages'])
    summary_df = pd.DataFrame(summary_data, columns=['Folder', 'Number of Documents', 'Total Pages'])

    output_file_path = os.path.join(output_csv_path, output_filename)
    with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
        detailed_df.to_excel(writer, sheet_name='Pages Per Document', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
