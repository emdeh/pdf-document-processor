# src/pdf_processor.py

import re
from pathlib import Path
import shutil
import fitz  # PyMuPDF
import os
import pytesseract
from PIL import Image
import io
import yaml
from utils import Logger
import unicodedata

class PDFProcessor:
    def __init__(self):
        with open("config/type_models.yaml", "r") as file:
            self.config = yaml.safe_load(file)
        # Verify the structure of self.config
        if not isinstance(self.config, dict) or 'statement_types' not in self.config:
            raise ValueError("The YAML file is not correctly formatted. Expected a key 'statement_types' at the top level.")
        
        # Set the Tesseract command path if necessary
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        
        # Set up logger
        self.logger = Logger.get_logger(self.__class__.__name__, log_to_file=True)
        
    def process_all_pdfs(self, input_folder, output_folder, manual_processing_folder, type_name):
        """
        Processes all PDF files in a given folder, splitting them into separate documents based on identified patterns.
        Identified paterns are defined in the YAML configuration file, which is loaded with the argument `type_name`.

        Args:
            input_folder (str): The folder containing the PDF files to process.
            output_folder (str): The folder where the split PDFs will be saved.
            manual_processing_folder (str): The folder where the PDF files without a known pattern will be moved.
            type_name (str): The type of document to process.
        """
        self.logger.info(
            "Splitting files in %s and saving individual documents to %s...", 
            input_folder, 
            output_folder
        )
        for pdf_file in Path(input_folder).glob("*.pdf"):
            pdf_path = str(pdf_file)
            is_machine_readable = self.is_pdf_machine_readable(pdf_path)

            if is_machine_readable:
                doc_starts = self.get_doc_starts_by_type(pdf_path, type_name)
            else:
                self.logger.info(
                    "%s is scanned. Performing OCR to extract text.", 
                    os.path.basename(pdf_file)
                )
                doc_starts = self.get_doc_starts_by_type(pdf_path, type_name, use_ocr=True)

            if doc_starts:
                self.split_pdf(pdf_path, output_folder, doc_starts)
                self.logger.info(
                    "%s has been processed and split accordingly.", 
                    os.path.basename(pdf_file)
                )
            else:
                self.logger.warning(
                    "Could not identify document pattern for %s, moving to manual processing folder.", 
                    os.path.basename(pdf_file)
                )
                shutil.copy(pdf_path, manual_processing_folder)
                manifest_path = os.path.join(manual_processing_folder, "manifest-of-unsplit-files.txt")
                with open(manifest_path, "a") as manifest_file:
                    manifest_file.write(f"{pdf_file.stem}\n")

        self.logger.info("Splitting complete.")

    def get_config_for_type(self, statement_type):
        """
        Retrieves the configuration for a specific statement type from the YAML config.

        Args:
            statement_type (str): The type of the statement to look for.

        Returns:
            dict: The configuration dictionary for the statement type if found, otherwise None.
        """
        for statement in self.config['statement_types']:
            if statement['type_name'] == statement_type:
                return statement
        return None
    
    def get_doc_starts_by_type(self, pdf_path, doc_type, use_ocr=False):
        config = self.get_config_for_type(doc_type)

        if config:
            return self.find_statement_starts(pdf_path, config, use_ocr)
        else:
            return None
        
    def _normalise_for_footer(self, text: str) -> str:
        t = unicodedata.normalize("NFKC", text)
        t = re.sub(r"\s+", " ", t)
        t = t.replace(" 0f ", " of ")
        t = re.sub(r"(?<=page)\s*[|I]\b", " 1", t, flags=re.IGNORECASE)
        return t
    
    def _extract_footer_text(self, page, prefer_ocr: bool = False) -> str:
        # Bottom strip (8–10% of page height)
        rect = page.rect
        footer_h = max(80, int((rect.y1 - rect.y0) * 0.10))
        clip = fitz.Rect(rect.x0, rect.y1 - footer_h, rect.x1, rect.y1)

        if not prefer_ocr:
            # Try vector text first in the footer region
            try:
                t = page.get_text("text", clip=clip).strip()
            except TypeError:
                # Older PyMuPDF: fallback without "text" arg
                t = page.get_text(clip=clip).strip()
            if t:
                return t

        # OCR the footer at ~300 DPI for better accuracy
        mat = fitz.Matrix(4, 4)  # ~288 DPI; good enough
        pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        # Try a layout-capable PSM, then single-line if needed
        text = pytesseract.image_to_string(img, lang="eng", config="--oem 1 --psm 6").strip()
        if not text:
            text = pytesseract.image_to_string(img, lang="eng", config="--oem 1 --psm 7").strip()
        return text

        
    def find_statement_starts(self, pdf_path, config, use_ocr=False):
        """
        Identifies the starting pages of statements within a PDF file based on a regex pattern or a specific phrase.

        Args:
            pdf_path (str): The file path of the PDF to be processed.
            config (dict): A dictionary containing information on how to identify statement starts.
            use_ocr (bool): Whether to use OCR for text extraction.

        Returns:
            list or dict: A list of page numbers where new documents start or a dictionary with start/end pages.
        """
        doc = fitz.open(pdf_path)
        # Determine whether we're working with start/end pairs or simple start pages
        statement_starts = {} if config.get('split_type') == 'start_end' else []
        current_statement = None

        # Extract relevant configuration information
        start_pattern = config.get('start_pattern')
        start_phrase = config.get('start_phrase')
        must_not_contain = config.get('must_not_contain')

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = self.extract_text_from_page(page, use_ocr)

            if start_pattern:
                # 1) Try full-page text
                page_text = self.extract_text_from_page(page, use_ocr)  # as you had
                page_text_norm = self._normalise_for_footer(page_text)
                match = re.search(start_pattern, page_text_norm, flags=re.IGNORECASE | re.UNICODE)

                # 2) If not found, try footer (text layer)
                if not match:
                    footer_text = self._extract_footer_text(page, prefer_ocr=False)
                    footer_norm = self._normalise_for_footer(footer_text)
                    match = re.search(start_pattern, footer_norm, flags=re.IGNORECASE | re.UNICODE)

                # 3) If still not found, OCR just the footer
                if not match:
                    footer_text_ocr = self._extract_footer_text(page, prefer_ocr=True)
                    footer_norm_ocr = self._normalise_for_footer(footer_text_ocr)
                    match = re.search(start_pattern, footer_norm_ocr, flags=re.IGNORECASE | re.UNICODE)

                if match:
                    if isinstance(statement_starts, dict):
                        statement_id = page_num
                        if match.lastindex:
                            g1 = match.group(1)
                            if g1 and g1.isdigit():
                                statement_id = int(g1)
                        if statement_id != current_statement:
                            if current_statement is not None:
                                statement_starts[current_statement]["end"] = page_num - 1
                            current_statement = statement_id
                            statement_starts[statement_id] = {"start": page_num}
                    else:
                        statement_starts.append(page_num)
                    continue
 
            # Check for specific start phrase match
            if start_phrase and start_phrase in page_text:
                # If working with start/end pairs
                if isinstance(statement_starts, dict):
                    statement_number = page_num
                    if statement_number != current_statement:
                        if current_statement is not None:
                            # Set the end for the current statement before moving on to a new one
                            statement_starts[current_statement]["end"] = page_num - 1
                        current_statement = statement_number
                        statement_starts[statement_number] = {"start": page_num}
                else:
                    # For simple page start case, append page number to the list
                    statement_starts.append(page_num)

            # Check for text that must NOT be present to determine the end of a statement
            if must_not_contain and must_not_contain not in page_text and current_statement is not None:
                # Close off the current statement if the "must_not_contain" condition is met
                statement_starts[current_statement]["end"] = page_num
                current_statement = None

        # Ensure the last statement is closed if it doesn't end explicitly
        if isinstance(statement_starts, dict) and current_statement is not None and "end" not in statement_starts[current_statement]:
            statement_starts[current_statement]["end"] = len(doc) - 1

        doc.close()
        return statement_starts

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
            text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')

        return text