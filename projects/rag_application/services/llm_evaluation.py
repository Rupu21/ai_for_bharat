import config
import pandas as pd
import time
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_correctness

metrics = [answer_correctness]

questions = [
    "How many jobs did Amazon create in 2020, and what was its total global workforce after this expansion?",
    "How does the 2023 net sales mix reflect Amazon's global priorities and strategic investments across segments?"
]

ground_truths = [
    "Amazon added 500,000 jobs in 2020, bringing its total workforce to approximately 1.3 million employees worldwide.",
    "Amazon's 2023 net sales mix highlights its global priorities, with North America contributing 61%, International 23%, and AWS 16% of total sales."
]


class llmEvaluation:
    def __init__(self, kb_id):
        self.kb_id = kb_id
        self.region = config.region_name
        self.bedrock_agent_client = config.bedrock_agent_client
        self.bedrock_agent_runtime_client = config.bedrock_agent_runtime_client

        self.TEXT_GENERATION_MODEL_ID = config.TEXT_GENERATION_MODEL_ID
        self.AMAZON_RERANKER_MODEL_ID = config.AMAZON_RERANKER_MODEL_ID

        self.bedrock_embeddings = config.bedrock_embeddings
        self.llm_for_evaluation = config.llm_for_evaluation

    def retrieve_and_generate(self, query, reranker_model=None, metadata_filters=None):
        region = self.region

        retrieval_config = {
            "vectorSearchConfiguration": {
                "numberOfResults": 30 if reranker_model else 3
            }
        }

        if reranker_model:
            retrieval_config["vectorSearchConfiguration"]["rerankingConfiguration"] = {
                "type": "BEDROCK_RERANKING_MODEL",
                "bedrockRerankingConfiguration": {
                    "modelConfiguration": {
                        "modelArn":
                            f'arn:aws:bedrock:{region}::foundation-model/{reranker_model}'
                    },
                    "numberOfRerankedResults": 3
                }
            }

            if metadata_filters:
                retrieval_config["vectorSearchConfiguration"]["rerankingConfiguration"][
                    "bedrockRerankingConfiguration"]["metadataConfiguration"] = {
                        "selectionMode": "SELECTIVE",
                        "selectiveModeConfiguration": {
                            "fieldsToInclude": [{"fieldName": "year"}]
                        }
                }

        start = time.time()
        response = self.bedrock_agent_runtime_client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": self.kb_id,
                    "modelArn":
                        f'arn:aws:bedrock:{region}::foundation-model/{self.TEXT_GENERATION_MODEL_ID}',
                    "retrievalConfiguration": retrieval_config,
                },
            }
        )
        print(f"[Response] : {response['output']['text']}\n")
        print(f"[Time] : {time.time() - start}s\n")
        return response

    def prepare_eval_dataset(self, questions, ground_truths,
                             reranker_model=None, metadata_filters=None):

        answers = []
        contexts = []

        print("Using KB:", self.kb_id)

        for query in questions:
            response = self.retrieve_and_generate(
                query=query,
                reranker_model=reranker_model,
                metadata_filters=metadata_filters
            )

            answers.append(response["output"]["text"])

            context_group = []
            for citation in response.get("citations", []):
                for ref in citation.get("retrievedReferences", []):
                    if "content" in ref and "text" in ref["content"]:
                        context_group.append(ref["content"]["text"])

            contexts.append(context_group)
            time.sleep(5)

        return Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        })

    def evaluation_driver(self):

        # ---------------- WITHOUT RERANKER ----------------
        ds_no_rerank = self.prepare_eval_dataset(
            questions, ground_truths, reranker_model=None
        )
        print("Prepared dataset without reranker")

        eval_no_rerank = evaluate(
            dataset=ds_no_rerank,
            metrics=metrics,
            llm=self.llm_for_evaluation,
            embeddings=self.bedrock_embeddings
        )
        df_no_rerank = eval_no_rerank.to_pandas()

        # ---------------- WITH RERANKER ----------------
        ds_rerank = self.prepare_eval_dataset(
            questions, ground_truths, reranker_model=self.AMAZON_RERANKER_MODEL_ID
        )
        print("Prepared dataset with reranker")

        eval_rerank = evaluate(
            dataset=ds_rerank,
            metrics=metrics,
            llm=self.llm_for_evaluation,
            embeddings=self.bedrock_embeddings
        )
        df_rerank = eval_rerank.to_pandas()

        # ---------------- WITH METADATA FILTERS ----------------
        ds_meta = self.prepare_eval_dataset(
            questions, ground_truths,
            reranker_model=self.AMAZON_RERANKER_MODEL_ID,
            metadata_filters=True
        )
        print("Prepared dataset with metadata filters")

        eval_meta = evaluate(
            dataset=ds_meta,
            metrics=metrics,
            llm=self.llm_for_evaluation,
            embeddings=self.bedrock_embeddings
        )
        df_meta = eval_meta.to_pandas()

        # ---------------- COMPARISON ----------------
        comparison = pd.DataFrame({
            "question": df_no_rerank["question"],
            "without_reranker": df_no_rerank["answer"],
            "with_reranker": df_rerank["answer"],
            "with_metadata": df_meta["answer"],
            "correct_no_rerank": df_no_rerank["answer_correctness"],
            "correct_rerank": df_rerank["answer_correctness"],
            "correct_meta": df_meta["answer_correctness"],
        })
        print(comparison)
        return comparison
