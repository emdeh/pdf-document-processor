import os
import glob
from os.path import basename
from dotenv import load_dotenv
from pdf_processor import process_all_pdfs
from count_pdfs import process_folders, save_to_excel
# from azure_blob_utils import get_blob_service_client, list_blobs, read_blob_content, upload_analysis_results_to_blob
from csv_utils import parse_results_to_csv, create_output_file, extract_static_info, process_transactions
from doc_ai_utils import initialise_analysis_client, analyse_document

# Load env variables from .env file
load_dotenv()

if __name__ == "__main__":
    input_folder = os.getenv("INPUT_FOLDER")
    output_folder = os.getenv("OUTPUT_FOLDER")
    pre_process_count = os.getenv("PDF_COUNT_PRE_OUTPUT_FILE")
    post_process_count = os.getenv("PDF_COUNT_POST_OUTPUT_FILE")
    #blob_acount_url = os.getenv("BLOB_ACCOUNT_URL")
    #blob_credential = os.getenv("SAS_TOKEN")
    csv_output = os.getenv("CSV_OUTPUT_FILE")
    #blob_container_name = os.getenv("CONTAINER_NAME")
    #storage_connection_string = os.getenv("STORAGE_CONNECTION_STRING")
    doc_model_endpoint = os.getenv("MODEL_ENDPOINT")
    doc_model_api_key = os.getenv("MODEL_API_KEY")
    doc_model_id = os.getenv("MODEL_ID")

    # Count input PDFs
    print(f"Counting files and pages in {input_folder}...\n")
    detailed_data_before, summary_data_before = process_folders([input_folder])
    save_to_excel(detailed_data_before,summary_data_before,pre_process_count)
    print(f"Saved pre-splitting count to {pre_process_count}.\n\n")
  
    # Process all PDFs to split them into separate statements
    print(f"Splitting files in {input_folder} and saving individual statements to {output_folder}...\n")
    process_all_pdfs(input_folder, output_folder)
    print(f"Splitting complete.\n\n")

    # Count processed PDFs
    print(f"Counting files and pages of split statements saved to {output_folder}...\n")
    detailed_data_after, summary_data_after = process_folders([output_folder])
    save_to_excel(detailed_data_after,summary_data_after,post_process_count)
    print(f"Saved post-splitting count to {post_process_count}.\n\n")

    # Initialise the Azure Document Analysis Client
    print("Initialising Document Intelligence Client...\n")
    doc_ai_client = initialise_analysis_client(doc_model_endpoint,doc_model_api_key)
    print(f"Document Intelligence Client {doc_ai_client} ready at endpoint {doc_model_endpoint}.\n Preparing to extract data...\n")

    # Create file to write transaction data to
    create_output_file(csv_output)
    print(f"Created {csv_output} to save extracted transaction data...\n\nProceeding to analysis...\n\n")

    for document_path in glob.glob(os.path.join(output_folder, '*.pdf')):
        # Analyse the document
        print(f"Analysing {document_path}...\n")
        original_document_name = basename(document_path)
        results = analyse_document(doc_ai_client, doc_model_id, document_path)
        print(f"Analysed {document_path}...\n")

        # Process the results
        print("Processing extracted data...\n")
        static_info = extract_static_info(results, original_document_name)
        transactions = process_transactions(results)

        print("Data extraction processed!\n")
            
        # Extract results to the CSV.
        print(f"Parsing transaction details from {document_path} to {csv_output}...\n")
        parse_results_to_csv(static_info, transactions, csv_output)
        print("Parsing complete! moving on...\n")

        # Get original document name
        # TO DO - issue with serialising results output to upload to storage

        # print("Preparing documents for storage...\n")
        # original_document_name = basename(document_path).replace('.pdf', '')
        # blob_name = f"{original_document_name}.json"
        # print(f"{original_document_name} renamed to {blob_name}...\n")

        # Write results to blob storage (initialises the connection as well)
        # TO DO - issue with serialising JSON output to upload to storage
        
        # print(f"Writing {blob_name} to storage...\n")
        # upload_analysis_results_to_blob(storage_connection_string, blob_container_name, blob_name, # extracted_data)
        # print(f"{blob_name} written to Blob Container: {container_name}...\n")

    

    # Initialize the Azure Blob Service Client.
    # TO DO - issue with serialising results output to upload to storage
        
    # print(f"Creating BlobServiceClient with SAS Token: {blob_credential}...\n\n")
    # blob_service_client = get_blob_service_client(blob_acount_url, blob_credential)
    # print(f"Successfully connected to the Azure Storage account: {blob_acount_url} with service client: {blob_service_client}...\n")
    
    # List blobs
    # TO DO - issue with serialising results output to upload to storage
        
    # print("Listing blobs...\n")
    # blobs_list = list_blobs(blob_service_client, blob_container_name)

    # blobs_list = list(list_blobs(blob_service_client, blob_container_name))
    # print(f"Found {len(blobs_list)} blobs...\n")
    
    # Read blob content
    # TO DO - issue with serialising results output to upload to storage
        
    # print("Reading blob content..\n")
    # for blob in blobs_list:
    #    print(f"Processing {blob.name}...\n")
    #
    #   results_content = read_blob_content(blob_service_client, blob_container_name, blob.name)

        # Check if results_content is not None
    #    if results_content:
            # Call parse_results_to_csv function if "Not None" to process the results content and append to CSV file.

  