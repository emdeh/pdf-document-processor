# Not in use
'''
import pandas as pd
from pathlib import Path
from tabula import read_pdf

def pdf_tables_to_csv(input_folder, output_csv_path):
    # Ensure the output CSV file exists or create it with headers
    if not Path(output_csv_path).exists():
        pd.DataFrame(columns=['FileName', 'Data']).to_csv(output_csv_path, index=False, encoding='utf-8')
    
    # Iterate through all PDF files in the input folder
    for pdf_file in Path(input_folder).glob('*.pdf'):
        # Extract tables from the PDF
        tables = read_pdf(str(pdf_file), pages="all", multiple_tables=True, lattice=True)
        
        # Check if any tables were found
        if tables:
            for table in tables:
                # Convert the table (DataFrame) to a CSV string
                csv_data = table.to_csv(index=False, header=False, encoding='utf-8')
                # Append the file name and CSV data to the output CSV file
                with open(output_csv_path, 'a', encoding='utf-8') as f:
                    pd.DataFrame({'FileName': [pdf_file.stem], 'Data': [csv_data]}).to_csv(f, index=False, header=False)
'''