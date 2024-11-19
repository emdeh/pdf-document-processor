# src/doc_ai_utils.py

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from utils import Logger
import os


class DocAIUtils:
    def __init__(self):
        self.logger = Logger.get_logger(self.__class__.__name__, log_to_file=True)

    def initialise_analysis_client(self, endpoint, api_key, doc_model_id):
        """
        Initializes the Document Intelligence Client.

        Args:
            endpoint (str): The endpoint URL for the Document Intelligence service.
            api_key (str): The API key for authentication.
            doc_model_id (str): The ID of the document model to be used.

        Returns:
            DocumentAnalysisClient: The initialized Document Intelligence Client.
        """
        self.logger.info("Initializing Document Intelligence Client...\n")
        credential = AzureKeyCredential(api_key)
        client = DocumentAnalysisClient(endpoint=endpoint, credential=credential)
        self.logger.info(
            "Document Intelligence Client established with Endpoint: %s.\nUsing %s.\nPreparing to extract data...\n\n",
            endpoint,
            doc_model_id
        )
        return client

    def analyse_document(self, client, model_id, document_path):
        """
        Analyzes a document using the specified client and model ID.

        Args:
            client (DocumentAnalysisClient): The client object used to interact with the document analysis service.
            model_id (str): The ID of the model to be used for document analysis.
            document_path (str): The path to the document file to be analyzed.

        Returns:
            AnalysisResult: The result of the document analysis.
        """
        self.logger.info(
            "Analyzing:\n%s.\n\n",
            os.path.basename(document_path)
        )
        try:
            with open(document_path, "rb") as document:
                poller = client.begin_analyze_document(model_id=model_id, document=document)
                result = poller.result()
            self.logger.info(
                "Analyzed:\n%s.\n",
                os.path.basename(document_path)
            )
        except Exception as e:
            self.logger.error(
                "Error analyzing %s: %s",
                os.path.basename(document_path),
                e
            )
            result = None
        return result

    def analyse_layout_document(self, client, document_path):
        """
        Analyzes a document using a pre-built layout model.

        Args:
            client (DocumentAnalysisClient): The client object for the Document Analysis service.
            document_path (str): The path to the document file to be analyzed.

        Returns:
            AnalysisResult: The analysis result if successful, None otherwise.
        """
        self.logger.info(
            "Analyzing with pre-built layout model: %s.\n\n",
            os.path.basename(document_path)
        )
        try:
            with open(document_path, "rb") as document:
                poller = client.begin_analyze_document("prebuilt-layout", document=document)
                result = poller.result()
            self.logger.info(
                "Analyzed: %s.\n",
                os.path.basename(document_path)
            )
        except Exception as e:
            self.logger.error(
                "Error analyzing %s: %s",
                os.path.basename(document_path),
                e
            )
            result = None
        return result

    def extract_table_data(self, results):
        """
        Extracts table data from the layout model results and structures them into rows.

        Parameters:
        - results (AnalysisResult): The layout model results containing table data.

        Returns:
        - tables: A list of tuples, where each tuple contains the table index and the structured table data.
        """
        tables = []

        for table_idx, table in enumerate(results.tables):
            table_data = []
            current_row_index = -1
            row = []
            for cell in sorted(table.cells, key=lambda c: (c.row_index, c.column_index)):
                if cell.row_index > current_row_index:
                    if row:
                        table_data.append(row)
                    row = []
                    current_row_index = cell.row_index
                row.append(cell.content)
            if row:
                table_data.append(row)
            tables.append((table_idx, table_data))

        return tables

    def extract_all_text(self, results):
            """
            Used by raw_process.py to extract all text content from the analysis results.
            
            Extracts all text content from the analysis results.

            Args:
                results (AnalysisResult): The analysis results containing text content.

            Returns:
                str: A string containing all the text content from the document.
            """
            all_text = []
            for page in results.pages:
                for line in page.lines:
                    all_text.append(line.content)
            # Join all text lines into a single string
            extracted_text = '\n'.join(all_text)
            return extracted_text