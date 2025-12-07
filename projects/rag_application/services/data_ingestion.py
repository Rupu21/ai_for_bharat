import boto3
import requests
import os
import json
import re
import config    # works in SageMaker
from utils.knowledge_base import BedrockKnowledgeBase

def download_file(url, filepath):
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    response = requests.get(url)

    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {filepath}")
    else:
        print(f"Failed to download {url}. Status: {response.status_code}")


class DataIngestion:
    def __init__(self):
        self.bucket_name = config.bucket_name
        self.region = config.region_name
        self.s3_client = boto3.client("s3", region_name=self.region)
        self.input_data_urls = config.input_data_urls
        self.output_folder_path = config.output_folder_path

        # Compute project root (one level above service/)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.full_output_path = os.path.join(self.project_root, self.output_folder_path)
        self.knowledge_base_metadata = None
        self.kb_id_metadata = None
        

    def create_bucket(self):
        try:
            print(f"Bucket name {self.bucket_name}")
            self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.region}
                )
            print(f"Bucket created: {self.bucket_name}")
        except Exception as e:
            print("Error:", e.response["Error"]["Message"])
            
    def upload_file(self):
        for root, dirs, files in os.walk(self.full_output_path):
            for file in files:
                if not file.startswith('.DS_Store'):
                    file_to_upload = os.path.join(root, file)
                    print(f"uploading file {file_to_upload} to {self.bucket_name}")
                    self.s3_client.upload_file(file_to_upload,self.bucket_name,file)
                    print("Uploaded")

                    
    def download_data(self):
        # Build the full absolute path outside service/
        

        for url in self.input_data_urls:
            filename = url.split("/")[-1]
            filepath = os.path.join(self.full_output_path, filename)
            download_file(url, filepath)

    def create_knowledge_base(self):
        self.knowledge_base_metadata = BedrockKnowledgeBase(
            kb_name=f'{config.knowledge_base_name}-{config.suffix}',
            kb_description=config.knowledge_base_description,
            data_sources=config.kb_data_source, 
            chunking_strategy=config.chunking_strategy, 
            suffix=config.suffix
        )
    def data_ingestion_kb(self):
        self.knowledge_base_metadata.start_ingestion_job()
        self.kb_id_metadata = self.knowledge_base_metadata.get_knowledge_base_id()
        return self.kb_id_metadata
        
    def create_meta_data(self):
        for filename in os.listdir(self.full_output_path):
            if not filename.startswith('.DS_Store'):
                # Define the metadata dictionary
                metadata ={}
                filename= f'{self.full_output_path}/{filename}'
                print(filename)
                # Create metadata
                metadata["company"] = "Amazon"
                metadata["ticker"] = "AMZN"
                metadata["year"] = re.search(r'\d+', filename.split('/')[-1]).group(0)
    
                # Create a JSON object
                json_data = {"metadataAttributes": metadata}
    
                # print(json_data)
    
                # Write the JSON object to a file
                with open(f"{filename.replace('.pdf', '.pdf.metadata.json')}", "w") as f:
                    json.dump(json_data, f)
