# src/pdf_processor.py

import re
from pathlib import Path
import shutil
import fitz  # PyMuPDF
import os


class PDFProcessor:
    def __init__(self):
        pass

    def process_all_pdfs(self, input_folder, output_folder, manual_processing_folder):
        """
        Processes all PDF files in a given folder, splitting them into separate documents based on identified patterns.

        Args:
            input_folder (str): The folder containing the PDF files to process.
            output_folder (str): The folder where the split PDFs will be saved.
            manual_processing_folder (str): The folder where the PDF files without a known pattern will be moved.
        """
        print(f"Splitting files in {input_folder} and saving individual documents to {output_folder}...\n")
        for pdf_file in Path(input_folder).glob("*.pdf"):
            pdf_path = str(pdf_file)
            doc_type = self.detect_document_type(pdf_path)

            if doc_type == "standard_statement":
                doc_starts = self.find_standard_statement_starts(pdf_path)
            elif doc_type == "bom_statement":
                doc_starts = self.find_bom_statement_starts(pdf_path)
            elif doc_type == "bendigo_statement":
                doc_starts = self.find_bendigo_statement_starts(pdf_path)
            else:
                doc_starts = None

            if doc_starts:
                self.split_pdf(pdf_path, output_folder, doc_starts)
                print(f"{os.path.basename(pdf_file)} has been processed and split accordingly.\n")
            else:
                print(
                    f"Could not identify document pattern for {os.path.basename(pdf_file)}, moving to manual processing folder.\n"
                )
                shutil.copy(pdf_path, manual_processing_folder)
                manifest_path = os.path.join(manual_processing_folder, "manifest-of-unsplit-files.txt")
                with open(manifest_path, "a") as manifest_file:
                    manifest_file.write(f"{pdf_file.stem}\n")

        print(f"Splitting complete.\n\n")

    def detect_document_type(self, pdf_path):
        """
        Detects the type of a PDF document based on its content.

        Parameters:
        pdf_path (str): The path to the PDF document.

        Returns:
        str: The detected document type. Possible values are 'bendigo_statement',
             'bom_statement', 'standard_statement', or 'unknown'.
        """
        doc = fitz.open(pdf_path)
        first_pages_text = "".join(
            [doc.load_page(i).get_text() for i in range(min(12, len(doc)))]
        )  # Analyze the first 9 pages

        if "Bendigo" in first_pages_text:
            doc.close()
            print("Bendigo Bank statement detected.")
            return "bendigo_statement"

        elif "FREEDOM" in first_pages_text:
            doc.close()
            print("Bank of Melbourne OR St. George statement detected.")
            return "bom_statement"

        elif re.search(r"\b1 of \d", first_pages_text):
            doc.close()
            print("Standard statement detected.")
            return "standard_statement"

        doc.close()
        return "unknown"

    def find_standard_statement_starts(self, pdf_path):
        """
        Standard function for statements that have '1 of x' pattern.
        Identifies the starting pages of documents within a PDF file.

        Args:
            pdf_path (str): The file path of the PDF to be processed.

        Returns:
            list: A list of page numbers where new documents start.
        """
        doc_starts = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page_text = doc.load_page(page_num).get_text()
            if re.search(r"\b1 of \d+", page_text):
                doc_starts.append(page_num)
        doc.close()
        return doc_starts

    def find_bendigo_statement_starts(self, pdf_path):
        """
        Identifies the starting pages of documents within a PDF file based on 'Statement Number'.

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
            match = re.search(r"Statement number\s+(\d+)", page_text)
            if match:
                statement_number = int(match.group(1))
                if statement_number != current_statement:
                    if current_statement is not None:
                        statement_starts[current_statement]["end"] = page_num - 1
                    current_statement = statement_number
                    statement_starts[statement_number] = {"start": page_num}
            elif "Continued overleaf..." not in page_text and current_statement is not None:
                statement_starts[current_statement]["end"] = page_num
                current_statement = None

        # Ensure the last statement is closed if it doesn't end explicitly
        if current_statement and "end" not in statement_starts[current_statement]:
            statement_starts[current_statement]["end"] = len(doc) - 1

        doc.close()
        return statement_starts

    def find_bom_statement_starts(self, pdf_path):
        """
        Identifies the starting pages of Bank of Melbourne and St. George statements.

        Args:
            pdf_path (str): The file path of the PDF to be processed.

        Returns:
            list: A list of page numbers where new documents start.
        """
        doc_starts = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page_text = doc.load_page(page_num).get_text()
            if re.search(r"\(page\s+1 of \d+\)", page_text):
                doc_starts.append(page_num)
        doc.close()
        return doc_starts

    def split_pdf(self, pdf_path, output_folder, doc_starts):
        """
        Splits a PDF into multiple documents based on the starting pages of each document.

        Args:
            pdf_path (str): The file path of the PDF to be split.
            output_folder (str): The folder where the split PDFs will be saved.
            doc_starts (list or dict): A list or dictionary of page numbers where new documents start.
        """
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pdf_name = Path(pdf_path).stem

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
                start_page = pages["start"]
                end_page = pages["end"]
                output_path = f"{output_folder}/{pdf_name}_statement_{statement}.pdf"
                new_doc = fitz.open()
                for page_num in range(start_page, end_page + 1):  # '+1' to include end page
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                new_doc.save(output_path)
                new_doc.close()

        doc.close()
