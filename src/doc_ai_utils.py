from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os

def initialise_analysis_client(endpoint, api_key, doc_model_id):
    print("Initialising Document Intelligence Client...\n")
    credential = AzureKeyCredential(api_key)
    client = DocumentAnalysisClient(endpoint=endpoint, credential=credential)
    print(f"Document Intelligence Client established with Endpoint: {endpoint}.\nUsing {doc_model_id}.\nPreparing to extract data...\n\n")
    return client
    

def analyse_document(client, model_id, document_path):
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

