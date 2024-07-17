from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os

def initialise_analysis_client(endpoint, api_key, doc_model_id):
    """
    Initialises the Document Intelligence Client.

    Args:
        endpoint (str): The endpoint URL for the Document Intelligence service.
        api_key (str): The API key for authentication.
        doc_model_id (str): The ID of the document model to be used.

    Returns:
        DocumentAnalysisClient (obj): The initialized Document Intelligence Client.

    Raises:
        None

    """
    print("Initialising Document Intelligence Client...\n")
    credential = AzureKeyCredential(api_key)
    client = DocumentAnalysisClient(endpoint=endpoint, credential=credential)
    print(f"Document Intelligence Client established with Endpoint: {endpoint}.\nUsing {doc_model_id}.\nPreparing to extract data...\n\n")
    return client
    

def analyse_document(client, model_id, document_path):
    """
    Analyses a document using the specified client and model ID.

    Args:
        client (obj): The client object used to interact with the document analysis service.
        model_id (str): The ID of the model to be used for document analysis.
        document_path (str): The path to the document file to be analysed.

    Returns:
        obj: The result of the document analysis.

    Raises:
        Exception: If an error occurs during the analysis process.
    """
    print(f"Analysing:\n{os.path.basename(document_path)}.\n\n")
    try:
        with open(document_path, "rb") as document:
            poller = client.begin_analyze_document(model_id=model_id, document=document)
            result = poller.result()
        print(f"Analysed:\n{os.path.basename(document_path)}.\n")
    except Exception as e:
        print(f"Error analysing {os.path.basename(document_path)}: {e}")
        result = None
    #print(f"debug - result: {result}")
    return result

def analyse_layout_document(client, document_path):
    """
    Analyses a document using a pre-built layout model.
    This is used when the prebuilt-layout model is called.
    It is not invoked for other models.

    Args:
        client: The client object for the Document Analysis service.
        document_path: The path to the document file to be analyzed.

    Returns:
        The analysis result if successful, None otherwise.
    """
    print(f"Analysing with pre-built layout model: {os.path.basename(document_path)}.\n\n")
    try:
        with open(document_path, "rb") as document:
            poller = client.begin_analyze_document("prebuilt-layout", document=document)
            result = poller.result()
        print(f"Analysed: {os.path.basename(document_path)}.\n")
    except Exception as e:
        print(f"Error analysing {os.path.basename(document_path)}: {e}")
        result = None
    return result

def extract_table_data(results):
    """
    Extracts table data from the layout model results and structures them into rows.
    This is used when the prebuilt-layout model is called.
    It is not invoked for other models.

    Parameters:
    - results: The layout model results containing table data.

    Returns:
    - tables: A list of tuples, where each tuple contains the table index and the structured table data.
              The structured table data is a list of rows, where each row is a list of cell contents.

    Example:
    >>> results = ...
    >>> tables = extract_table_data(results)
    >>> print(tables)
    [(0, [['Cell 1', 'Cell 2'], ['Cell 3', 'Cell 4']]), (1, [['Cell 5', 'Cell 6'], ['Cell 7', 'Cell 8']])]
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
                current_row = [''] * table.column_count  # Initialize row with empty strings
                current_row_index = cell.row_index
            current_row[cell.column_index] = cell.content
        if current_row:
            table_data.append(current_row)
        tables.append((table_idx, table_data))

    return tables

"""
def process_analysis_results(results):
    # This function is not currently in use. Instead results from the analyse_document() function are passed to csv_utils functions as arguments.
    # TO-DO: Consider re organising csv_utils functions...
    extracted_data = []
    for analyzed_document in results.documents:
        print(f"Document Type: {analyzed_document.doc_type}")
        document_data = {"doc_type": analyzed_document.doc_type, "fields": {}}
        for name, field in analyzed_document.fields.items():
            value = field.value if field.value else field.content
            print(f"{name}: {value}")  # Print each field name and value
            document_data["fields"][name] = value
        extracted_data.append(document_data)
    return extracted_data
"""

