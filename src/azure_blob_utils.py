# Description: This file contains utility functions to interact with Azure Blob Storage.
from azure.storage.blob import BlobServiceClient, BlobClient
from dotenv import load_dotenv
import json
from utils import Logger



# Function to get the Blob Service Client
def get_blob_service_client(blob_account_url, blob_credential):
    return BlobServiceClient(account_url=blob_account_url, credential=blob_credential)

# Function to list blobs in a container
def list_blobs(blob_service_client, blob_container_name, path_prefix=''):
    container_client = blob_service_client.get_container_client(blob_container_name)
    return container_client.list_blobs(name_starts_with=path_prefix)

# Function to read blob content
def read_blob_content(client, container_name, blob_name):
    # Instantiate logger
    logger = Logger.get_logger("azure_blobs_utils", log_to_file=True)
    try:
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        blob_content = blob_client.download_blob().readall()
        text_content = blob_content.decode('utf-8')
        logger.info(
            "Decoded text content for %s: %s", 
            blob_name,
            text_content[:100]
        )
        content = json.loads(text_content)
        return content
    except Exception as e:
        logger.error(
            "Failed to read blob content for %s: %s", 
            blob_name, 
            e
        )
        return None
    

def upload_analysis_results_to_blob(storage_connection_string, container_name, blob_name, content):
    """
    Upload analysis results to Azure Blob Storage as a JSON file.

    :param storage_connection_string: Connection string to the Azure Storage account
    :param container_name: Name of the container where the blob will be uploaded
    :param blob_name: Name of the blob (file) to create
    :param content: Content to be uploaded, typically a dictionary
    """
    # Convert the content (dict) to a JSON string
    json_content = json.dumps(content, indent=2)

    # Initialize a BlobClient
    blob_client = BlobClient.from_connection_string(conn_str=storage_connection_string, container_name=container_name, blob_name=blob_name)

    # Upload the content
    blob_client.upload_blob(json_content, overwrite=True)
