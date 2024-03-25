import os
from dotenv import load_dotenv
from pdf_processor import process_all_pdfs
from count_pdfs import process_folders, save_to_excel
from azure_blob_utils import get_blob_service_client, list_blobs, read_blob_content
from csv_utils import parse_json_to_csv, create_output_file, extract_static_info

# Load env variables from .env file
load_dotenv()

if __name__ == "__main__":
    input_folder = os.getenv("INPUT_FOLDER")
    output_folder = os.getenv("OUTPUT_FOLDER")
    pre_process_count = os.getenv("PDF_COUNT_PRE_OUTPUT_FILE")
    post_process_count = os.getenv("PDF_COUNT_POST_OUTPUT_FILE")
    blob_acount_url = os.getenv("ACCOUNT_URL")
    blob_credential = str(os.getenv("SAS_TOKEN"))
    csv_output = os.getenv("CSV_OUTPUT_FILE")
    blob_container_name = os.getenv("CONTAINER_NAME")
    json_sanity_test = os.getenv("TEST_JSON")

    # Count input PDFs
    detailed_data_before, summary_data_before = process_folders([input_folder])
    save_to_excel(detailed_data_before,summary_data_before,pre_process_count)
    print(f"Saved pre-processing count to {pre_process_count}.\n\n")
  
    # Process all PDFs to split them into separate statements
    process_all_pdfs(input_folder, output_folder)
    print(f"Split all files located in {input_folder} and saved them into individual statements in the {output_folder} folder.\n\n")

    # Count processed PDFs
    detailed_data_after, summary_data_after = process_folders([output_folder])
    save_to_excel(detailed_data_after,summary_data_after,post_process_count)
    print(f"Saved post-processing count to {post_process_count}.\n\n")

    # TO DO - Implement argparse to make features modular and independent.
    create_output_file(csv_output)
    print(f"Created {csv_output} to save transaction data.\n\n")

    # Initialize the Azure Blob Service Client.
    print(f"Creating BlobServiceClient with SAS Token: {blob_credential}.\n\n")
    blob_service_client = get_blob_service_client(blob_acount_url, blob_credential)
    print(f"Successfully connect to the Azure Storage account: {blob_acount_url} with service client: {blob_service_client}.")
    
    # List blobs
    print("Listing blobs...")
    blobs_list = list_blobs(blob_service_client, blob_container_name)

    blobs_list = list(list_blobs(blob_service_client, blob_container_name))
    print(f"Found {len(blobs_list)} blobs. Filtering JSON files...")
    
    json_blobs_list = [
    blob for blob in blobs_list 
    if blob.name.endswith('.pdf.labels.json') and not ("fields" in blob.name or "ocr" in blob.name or blob.name.endswith('.pdf'))
    ]
    
    print(f"Filtered down {len(json_blobs_list)} JSON blobs for processing.")

    # Read blob content
    for blob in json_blobs_list:
        print(f"Processing {blob.name}")

        json_content = read_blob_content(blob_service_client, blob_container_name, blob.name)

        #Check if json_content is not None
        if json_content:
            # Call parse_json_to_csv function if "Not None" to process the JSON content and append to CSV file.

            static_info = extract_static_info(json_content)
            # Extract JSON to the CSV.
            parse_json_to_csv(json_content, csv_output, static_info)
        else:
            print(f"Failed to read content from {blob.name}")    