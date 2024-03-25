from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

def initialise_analysis_client(endpoint, api_key):
    credential = AzureKeyCredential(api_key)
    client = DocumentAnalysisClient(endpoint=endpoint, credential=credential)
    return client

def analyse_document(client, model_id, document_path):
    with open(document_path, "rb") as document:
        poller = client.begin_analyze_document(model_id=model_id, document=document)
        result = poller.result()
    return result

def process_analysis_results(results):
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

