# Description: This file contains utility functions to interact with Azure Blob Storage.
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import json

# Function to get the Blob Service Client
def get_blob_service_client(blob_account_url, blob_credential):
    return BlobServiceClient(account_url=blob_account_url, credential=blob_credential)

# Function to list blobs in a container
def list_blobs(blob_service_client, blob_container_name, path_prefix=''):
    container_client = blob_service_client.get_container_client(blob_container_name)
    return container_client.list_blobs(name_starts_with=path_prefix)

# Function to read blob content
def read_blob_content(client, container_name, blob_name):
    try:
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        blob_content = blob_client.download_blob().readall()
        text_content = blob_content.decode('utf-8')
        print(f"Decoded text content for {blob_name}: {text_content[:100]}")
        content = json.loads(text_content)
        return content
    except Exception as e:
        print(f"Failed to read blob content for {blob_name}: {e}")
        return None