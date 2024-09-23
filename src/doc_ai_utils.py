# src/doc_ai_utils.py

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os


class DocAIUtils:
    def __init__(self):
        pass

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
        print("Initializing Document Intelligence Client...\n")
        credential = AzureKeyCredential(api_key)
        client = DocumentAnalysisClient(endpoint=endpoint, credential=credential)
        print(
            f"Document Intelligence Client established with Endpoint: {endpoint}.\nUsing {doc_model_id}.\nPreparing to extract data...\n\n"
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
        print(f"Analyzing:\n{os.path.basename(document_path)}.\n\n")
        try:
            with open(document_path, "rb") as document:
                poller = client.begin_analyze_document(model_id=model_id, document=document)
                result = poller.result()
            print(f"Analyzed:\n{os.path.basename(document_path)}.\n")
        except Exception as e:
            print(f"Error analyzing {os.path.basename(document_path)}: {e}")
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
        print(f"Analyzing with pre-built layout model: {os.path.basename(document_path)}.\n\n")
        try:
            with open(document_path, "rb") as document:
                poller = client.begin_analyze_document("prebuilt-layout", document=document)
                result = poller.result()
            print(f"Analyzed: {os.path.basename(document_path)}.\n")
        except Exception as e:
            print(f"Error analyzing {os.path.basename(document_path)}: {e}")
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
            current_row = []
            current_row_index = -1
            for cell in table.cells:
                if cell.row_index != current_row_index:
                    if current_row:
                        table_data.append(current_row)
                    current_row = [""] * table.column_count  # Initialize row with empty strings
                    current_row_index = cell.row_index
                current_row[cell.column_index] = cell.content
            if current_row:
                table_data.append(current_row)
            tables.append((table_idx, table_data))

        return tables
