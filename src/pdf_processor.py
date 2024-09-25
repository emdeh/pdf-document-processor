# src/pdf_processor.py

import re
from pathlib import Path
import shutil
import fitz  # PyMuPDF
import os
import pytesseract
from PIL import Image
import io


class PDFProcessor:
    def __init__(self):
        # Set the Tesseract command path if necessary
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
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
            is_machine_readable = self.is_pdf_machine_readable(pdf_path)

            if is_machine_readable:
                # Proceed with existing logic
                doc_type = self.detect_document_type(pdf_path)
                doc_starts = self.get_doc_starts_by_type(pdf_path, doc_type)
            else:
                print(f"{os.path.basename(pdf_file)} is scanned. Performing OCR to extract text.\n")
                # Use OCR to extract text
                doc_type = self.detect_document_type(pdf_path, use_ocr=True)
                doc_starts = self.get_doc_starts_by_type(pdf_path, doc_type, use_ocr=True)

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

    def detect_document_type(self, pdf_path, use_ocr=False):
        """
        Detects the type of a PDF document based on its content.

        Parameters:
            pdf_path (str): The path to the PDF document.
            use_ocr (bool): Whether to use OCR for text extraction.

        Returns:
            str: The detected document type. Possible values are 'bendigo_statement',
                'bom_statement', 'standard_statement', or 'unknown'.
        """
        doc = fitz.open(pdf_path)
        first_pages_text = ""
        for i in range(min(12, len(doc))):
            page = doc.load_page(i)
            page_text = self.extract_text_from_page(page, use_ocr)
            first_pages_text += page_text

        doc.close()

        if "Bendigo" in first_pages_text:
            print("Bendigo Bank statement detected.")
            return "bendigo_statement"

        elif "FREEDOM" in first_pages_text:
            print("Bank of Melbourne OR St. George statement detected.")
            return "bom_statement"

        elif re.search(r"\b1 of \d", first_pages_text):
            print("Standard statement detected.")
            return "standard_statement"
        
        elif "WELCOME TO YOUR ANZ ACCOUNT AT A GLANCE" in first_pages_text:
            print("ANZ statement detected.")
            return "anz_statement"
        
        elif "Westpac" in first_pages_text:
            print("Westpac statement detected.")
            return "westpac_statement"

        return "unknown"

    def find_standard_statement_starts(self, pdf_path, use_ocr=False):
        """
        Identifies the starting pages of standard statements within a PDF file.

        Args:
            pdf_path (str): The file path of the PDF to be processed.
            use_ocr (bool): Whether to use OCR for text extraction.

        Returns:
            list: A list of page numbers where new documents start.
        """
        doc_starts = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = self.extract_text_from_page(page, use_ocr)
            if re.search(r"\b1 of \d+", page_text):
                doc_starts.append(page_num)
        doc.close()
        return doc_starts

    def find_bendigo_statement_starts(self, pdf_path, use_ocr=False):
        """
        Identifies the starting pages of documents within a PDF file based on 'Statement Number'.

        Args:
            pdf_path (str): The file path of the PDF to be processed.
            use_ocr (bool): Whether to use OCR for text extraction.

        Returns:
            dict: A dictionary with keys as the statement number and values as dictionaries
                containing 'start' and 'end' pages for each document.
        """
        doc = fitz.open(pdf_path)
        statement_starts = {}
        current_statement = None

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = self.extract_text_from_page(page, use_ocr)
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


        # Ensure the last statement is closed if it doesn't end explicitly
        if current_statement and "end" not in statement_starts[current_statement]:
            statement_starts[current_statement]["end"] = len(doc) - 1

        doc.close()
        return statement_starts

    def find_bom_statement_starts(self, pdf_path, use_ocr=False):
        """
        Identifies the starting pages of Bank of Melbourne and St. George statements.

        Args:
            pdf_path (str): The file path of the PDF to be processed.
            use_ocr (bool): Whether to use OCR for text extraction.

        Returns:
            list: A list of page numbers where new documents start.
        """
        doc_starts = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = self.extract_text_from_page(page, use_ocr)
            if re.search(r"\(page\s+1 of \d+\)", page_text):
                doc_starts.append(page_num)
        doc.close()
        return doc_starts
    
    def find_westpac_statement_starts(self, pdf_path, use_ocr=False):
        """
        Identifies the starting pages of Westpac Group statements based on the pattern
        "STATEMENT NO. X PAGE 1 OF Y".

        Args:
            pdf_path (str): The file path of the PDF to be processed.
            use_ocr (bool): Whether to use OCR for text extraction.

        Returns:
            list: A list of page numbers where new documents start.
        """
        doc_starts = []
        doc = fitz.open(pdf_path)

        # Define regex pattern
        statement_pattern = r"STATEMENT\s+NO\.\s+\d+\s+PAGE\s+1\s+OF\s+\d+"

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = self.extract_text_from_page(page, use_ocr)
            
            # Search for the statement pattern
            if re.search(statement_pattern, page_text, re.IGNORECASE):
                doc_starts.append(page_num)
        
        doc.close()
        return doc_starts
    
    def find_anz_statement_starts(self, pdf_path, use_ocr=False):
        """
        Identifies the starting pages of ANZ statements within a PDF file.

        Args:
            pdf_path (str): The file path of the PDF to be processed.
            use_ocr (bool): Whether to use OCR for text extraction.

        Returns:
            list: A list of page numbers where new documents start.
        """
        doc_starts = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = self.extract_text_from_page(page, use_ocr)
            if "WELCOME TO YOUR ANZ ACCOUNT AT A GLANCE" in page_text:
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
                new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
                new_doc.save(output_path)
                new_doc.close()

        elif isinstance(doc_starts, dict):
            # Handle dictionary of starts and ends (statement numbers starts)
            for statement, pages in doc_starts.items():
                start_page = pages["start"]
                end_page = pages["end"]
                output_path = f"{output_folder}/{pdf_name}_statement_{statement}.pdf"
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
                new_doc.save(output_path)
                new_doc.close()

        doc.close()

    def is_pdf_machine_readable(self, pdf_path):
        """
        Checks if the PDF is machine-readable by attempting to extract text from the first page.

        Args:
            pdf_path (str): The path to the PDF file.

        Returns:
            bool: True if the PDF is machine-readable, False if it is scanned (image-based).
        """
        doc = fitz.open(pdf_path)
        first_page = doc.load_page(0)
        text = first_page.get_text().strip()
        doc.close()
        # If text is empty or very short, assume it's scanned
        return len(text) > 20  # Adjust threshold as needed

    def get_doc_starts_by_type(self, pdf_path, doc_type, use_ocr=False):
        if doc_type == "standard_statement":
            return self.find_standard_statement_starts(pdf_path, use_ocr)
        elif doc_type == "bom_statement":
            return self.find_bom_statement_starts(pdf_path, use_ocr)
        elif doc_type == "westpac_statement":
            return self.find_westpac_statement_starts(pdf_path, use_ocr)
        elif doc_type == "bendigo_statement":
            return self.find_bendigo_statement_starts(pdf_path, use_ocr)
        elif doc_type == "anz_statement":
            return self.find_anz_statement_starts(pdf_path, use_ocr)
        else:
            return None
        
    def extract_text_from_page(self, page, use_ocr=False):
        """
        Extracts text from a PDF page, using OCR if specified or if no text is found.

        Args:
            page (fitz.Page): The PDF page object.
            use_ocr (bool): Whether to force OCR extraction.

        Returns:
            str: The extracted text from the page.
        """
        text = page.get_text().strip()
        if not text or use_ocr:
            # Perform OCR
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(image)
        return text

