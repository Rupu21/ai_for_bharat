import boto3
import time
from langchain.llms.bedrock import Bedrock
from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings

input_data_urls = ["https://s2.q4cdn.com/299287126/files/doc_financials/2024/ar/Amazon-com-Inc-2023-Annual-Report.pdf",
        "https://s2.q4cdn.com/299287126/files/doc_financials/2023/ar/Amazon-2022-Annual-Report.pdf",
        "https://s2.q4cdn.com/299287126/files/doc_financials/2022/ar/Amazon-2021-Annual-Report.pdf",
        "https://s2.q4cdn.com/299287126/files/doc_financials/2021/ar/Amazon-2020-Annual-Report.pdf",
        "https://s2.q4cdn.com/299287126/files/doc_financials/2020/ar/2019-Annual-Report.pdf"]

output_folder_path="data/sec-10-k"
knowledge_base_name = 'end-to-end-demo-2'
knowledge_base_description = "Knowledge Base for end to end project"
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

TEXT_GENERATION_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
EVALUATION_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
# Reranker model: there are two reranker models available at launch
AMAZON_RERANKER_MODEL_ID = "amazon.rerank-v1:0"
COHERE_RERANKER_MODEL_ID = "cohere.rerank-v3-5:0"


bedrock_client = boto3.client('bedrock-runtime')
llm_for_evaluation = ChatBedrock(model_id="anthropic.claude-3-sonnet-20240229-v1:0", client=bedrock_client)
bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", client=bedrock_client)

implicit_model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
chunking_strategy = 'FIXED_SIZE'
# Get the current timestamp
current_time = time.time()
# Format the timestamp as a string
timestamp_str = time.strftime("%Y%m%d%H%M%S", time.localtime(current_time))[-7:]
# Create the suffix using the timestamp
suffix = f"{timestamp_str}"
suffix = '10101'
s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
session = boto3.session.Session(region_name='us-west-2')
region_name = session.region_name

account_id = sts_client.get_caller_identity()["Account"]
bedrock_agent_client = boto3.client('bedrock-agent')
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime') 


model_arn = f'arn:aws:bedrock:{region_name}::foundation-model/{model_id}'

implicit_model_arn = f'arn:aws:bedrock:{region_name}::foundation-model/{implicit_model_id}'
bucket_name = f'{knowledge_base_name}-{suffix}'
kb_data_source=[{"type": "S3", "bucket_name": bucket_name}]






