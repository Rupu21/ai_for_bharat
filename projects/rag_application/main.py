# main.py

import os
import logging
from services.data_ingestion import DataIngestion
from services.llm_caller import llmCaller
from services.permission_update import permissionUpdate
from services.llm_evaluation import llmEvaluation
from services.cloudwatch_logger import BedrockCloudWatchLogger
from functools import wraps

# =======================
# Setup Beautiful Local Logger
# =======================
LOG_FILE = "logs/project.log"
os.makedirs("logs", exist_ok=True)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler = logging.FileHandler(LOG_FILE)
handler.setFormatter(formatter)
# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger("ProjectLogger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console_handler)

def log_function(func):
    """Decorator to log function entry and exit."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"START: {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"END: {func.__name__}")
        return result
    return wrapper

# =======================
# Workflow Functions
# =======================

@log_function
def run_data_ingestion():
    di = DataIngestion()
    di.download_data()
    di.create_bucket()
    di.create_knowledge_base()
    di.create_meta_data()
    di.upload_file()
    kb_id = di.data_ingestion_kb()  # kb_id returned from this function
    logger.info(f"Knowledge Base ID obtained: {kb_id}")
    return di, kb_id

@log_function
def setup_cloudwatch(kb_id):
    cw_logger = BedrockCloudWatchLogger(kb_id=kb_id)
    log_group_name = "/aws/bedrock/invokemodel"
    cw_logger.enable_bedrock_logging(log_group_name)
    logger.info(f"CloudWatch logging enabled for log group: {log_group_name}")
    return cw_logger

@log_function
def run_llm_calls(kb_id, query):
    llm_call = llmCaller(kb_id=kb_id)
    permissionUpdate(kb_id=kb_id)

    logger.info(f"Basic LLM Relevent DOC Running ...")
    response_basic = llm_call.retrieve_doc(query=query)
    for num, chunk in enumerate(response_basic['retrievalResults'], 1):
        logger.info(f"Chunk {num}: {chunk['content']['text']}")
        logger.info(f"Location: {chunk['location']}")
        logger.info(f"Score: {chunk['score']}")
        logger.info(f"Metadata: {chunk['metadata']}")
    logger.info(f"Basic LLM Ans Finding Running ...")
    response_basic_ans = llm_call.retrieve_and_generate(query=query)
    logger.info(f"Basic LLM output: {response_basic_ans['output']['text']}")

    logger.info(f"Implicit LLM Relevent DOC Finding Running...")
    response_retrieve = llm_call.retrieve_doc_implicit(query=query)
    for num, chunk in enumerate(response_retrieve['retrievalResults'], 1):
        logger.info(f"Chunk {num}: {chunk['content']['text']}")
        logger.info(f"Location: {chunk['location']}")
        logger.info(f"Score: {chunk['score']}")
        logger.info(f"Metadata: {chunk['metadata']}")
    logger.info(f"Implicit LLM Ans Finding Running ...")
    response_imp = llm_call.retrieve_and_generate_imp(query=query)
    logger.info(f"Implicit LLM output: {response_imp['output']['text']}")

    response_reranker = llm_call.retrieve_and_generate_reranker(query=query)
    logger.info(f"Reranker LLM output: {response_reranker['output']['text']}")
    return llm_call

@log_function
def run_evaluation(kb_id):
    eval_llm = llmEvaluation(kb_id=kb_id)
    eval_df = eval_llm.evaluation_driver()
    os.makedirs("data", exist_ok=True)
    eval_path = os.path.join("data", "eval_df.csv")
    eval_df.to_csv(eval_path, index=False)
    logger.info(f"Evaluation results saved to {eval_path}")
    return eval_df

@log_function
def get_filter_generation_output(cw_logger, user_query):
    results = cw_logger.get_filter_generation_output(user_query)
    logger.info(f"CloudWatch filter generation output for query '{user_query}': {results}")
    return results

# =======================
# Main Function
# =======================
def main():
    # 1. Define the query
    QUERY = "How many jobs did Amazon create in 2020, and what was its total global workforce after this expansion?"

    # 2. Run Data Ingestion first and get kb_id
    # di, KB_ID = run_data_ingestion()
    # print("KB_ID",KB_ID)
    # KB_ID =input("Re-enter KB_ID")
    # # # 3. Setup CloudWatch logging
    # cw_logger = setup_cloudwatch(KB_ID)
    # # 4. Run LLM calls
    # run_llm_calls(KB_ID, query=QUERY)

    # # 5. Run Evaluation
    # run_evaluation(KB_ID)

    # # 6. Show CloudWatch logs for this query
    # get_filter_generation_output(cw_logger, user_query=QUERY)

    # logger.info("=== All Steps Completed Successfully ===")
    # print("All steps completed successfully! Check logs/project.log for details.")
    logger.info("Demo")

if __name__ == "__main__":
    main()
