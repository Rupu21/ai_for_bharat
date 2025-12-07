import boto3
import requests
import os
import json
import re
import config 
from utils import all_prompt
class llmCaller:
    def __init__(self, kb_id):
        self.bucket_name = config.bucket_name
        self.region = config.region_name
        self.s3_client = boto3.client("s3", region_name=self.region)
        self.kb_id = kb_id
        self.bedrock_agent_client = config.bedrock_agent_client
        self.bedrock_agent_runtime_client = config.bedrock_agent_runtime_client
        # self.model_arn = config.model_arn
        self.implicit_model_arn = config.implicit_model_arn
        self.reranker_model = config.AMAZON_RERANKER_MODEL_ID
        self.TEXT_GENERATION_MODEL_ID = config.TEXT_GENERATION_MODEL_ID

    def retrieve_doc(self, query):
        response = self.bedrock_agent_runtime_client.retrieve(
            knowledgeBaseId=self.kb_id, 
            nextToken='string',
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults":10,
                    } 
                },
            retrievalQuery={
                "text": query
            }
        )
        return response

    def retrieve_and_generate(self, query, max_results=5,
                              prompt_template=all_prompt.default_prompt):
        response = self.bedrock_agent_runtime_client.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.implicit_model_arn, 
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': max_results,
                                }
                            },
                        'generationConfiguration': {
                                'promptTemplate': {
                                    'textPromptTemplate': prompt_template
                                }
                            }
                        }
                    }
                )
        return response

        
    def retrieve_and_generate_imp(self, query, max_results=5,
                              prompt_template=all_prompt.default_prompt):
        response = self.bedrock_agent_runtime_client.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.implicit_model_arn, 
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': max_results,
                                 "implicitFilterConfiguration": {
                                        "metadataAttributes":[
                                            {
                                                "key": "year",
                                                "type": "NUMBER",
                                                "description": "The year in which the document is about."
                                            },
                                            {
                                                "key": "company",
                                                "type": "STRING",
                                                "description": "The company name the document is describing. Possible ude ['Amazon']"
                                            },
                                            {
                                                "key": "ticker",
                                                "type": "STRING",
                                                "description": "The ticker name of the company. Possible values include ['AMZN']"
                                            }
                                        ],
                                        "modelArn": self.implicit_model_arn
                                    }
                                }
                            },
                        'generationConfiguration': {
                                'promptTemplate': {
                                    'textPromptTemplate': prompt_template
                                }
                            }
                        }
                    }
                )
        return response

    def retrieve_doc_implicit(self, query):
        response = self.bedrock_agent_runtime_client.retrieve(
            knowledgeBaseId=self.kb_id, 
            nextToken='string',
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults":10,
                    "implicitFilterConfiguration": {
                            "metadataAttributes":[
                                {
                                    "key": "year",
                                    "type": "NUMBER",
                                    "description": "The year in which the document is about."
                                },
                                {
                                    "key": "company",
                                    "type": "STRING",
                                    "description": "The company name the document is describing. Possible values include ['Amazon']"
                                },
                                {
                                    "key": "ticker",
                                    "type": "STRING",
                                    "description": "The ticker name of the company. Possible values include ['AMZN']"
                                }
                            ],
                            "modelArn": "arn:aws:bedrock:{}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0".format(self.region)
                        },
                    } 
                },
            retrievalQuery={
                "text": query
            }
        )
        return response

    def retrieve_and_generate_reranker(self, query, max_results=30,
                              prompt_template=all_prompt.default_prompt):
        response = self.bedrock_agent_runtime_client.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.TEXT_GENERATION_MODEL_ID, 
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': max_results,
                                        "rerankingConfiguration":{
                                         "type": "BEDROCK_RERANKING_MODEL",
                                            "bedrockRerankingConfiguration": {
                                                "modelConfiguration": {
                                                    "modelArn": f'arn:aws:bedrock:{self.region}::foundation-model/{self.reranker_model}',
                                                },
                                            "numberOfRerankedResults": 3
                                            }
                                        }
                                    }
            
                            },
                        'generationConfiguration': {
                                'promptTemplate': {
                                    'textPromptTemplate': prompt_template
                                }
                            }
                        }
                    }
                )
        return response
