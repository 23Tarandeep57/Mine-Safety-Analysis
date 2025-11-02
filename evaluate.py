# evaluate.py
import os
import sys
import time
import math
import random
import traceback
import argparse
from multiprocessing import freeze_support

from dotenv import load_dotenv
from datasets import Dataset
import pandas as pd

from ragas import evaluate
from ragas.metrics import Faithfulness, ResponseRelevancy, ContextPrecision
# from ragas.llms import LangchainLLMWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.run_config import RunConfig

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Try to import Chroma from langchain_chroma (new package) if available,
# otherwise fall back to langchain_community.vectorstores.Chroma (deprecated).
# try:
#     from langchain_chroma import Chroma
# except Exception:
#     from langchain_community.vectorstores import Chroma
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from prompts import CONTEXTUALIZE_Q_SYSTEM_PROMPT, QA_SYSTEM_PROMPT

# -------------------- CONFIG --------------------
# PERSIST_DIRECTORY = "./chroma_db"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIRECTORY = os.path.join(SCRIPT_DIR, "chroma_db")
EMBEDDING_MODEL = "models/text-embedding-004"
LLM_MODEL = "models/gemini-pro-latest"

# Rate-limit/retry settings
MAX_RETRIES = 6
BASE_BACKOFF = 5.0         # base seconds for exponential backoff
MIN_DELAY_BETWEEN_CALLS = 3   # seconds - ensure gap between remote calls

# Cache file for LLM results to avoid repeated calls
CACHE_PATH = "results_cache.jsonl"
# ------------------------------------------------

_last_llm_call_time = 0.0

# -------------------- Utilities --------------------
def _rate_limit_sleep():
    """Ensure at least MIN_DELAY_BETWEEN_CALLS between LLM calls."""
    global _last_llm_call_time
    now = time.time()
    elapsed = now - _last_llm_call_time
    if elapsed < MIN_DELAY_BETWEEN_CALLS:
        time.sleep(MIN_DELAY_BETWEEN_CALLS - elapsed)
    _last_llm_call_time = time.time()

def _invoke_with_retries(callable_fn, *args, **kwargs):
    """
    Generic retry wrapper for LLM and retriever calls. Implements exponential backoff
    and retries quota-like / transient errors.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _rate_limit_sleep()
            return callable_fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            is_quota = ("quota" in msg) or ("resourceexhausted" in msg) or ("429" in msg) or ("exceeded" in msg)
            if is_quota and attempt < MAX_RETRIES:
                backoff = BASE_BACKOFF * (2 ** (attempt - 1))
                jitter = backoff * 0.1 * (random.random() - 0.5)
                delay = max(1.0, backoff + jitter)
                print(f"[retry] quota error detected. attempt {attempt}/{MAX_RETRIES}. sleeping {delay:.1f}s and retrying...")
                time.sleep(delay)
                continue
            # non-quota or final attempt: surface the exception
            print(f"[error] Call failed on attempt {attempt}: {e}")
            traceback.print_exc()
            raise

def load_api_key():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment.")
        sys.exit(1)
    return api_key

def initialize_components(api_key, persist_directory):
    if not os.path.exists(persist_directory):
        print(f"Error: Chroma DB directory not found at {persist_directory}")
        sys.exit(1)

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=api_key,
        max_retries=MAX_RETRIES
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
        max_retries=MAX_RETRIES
    )
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 8, "fetch_k": 20})
    return llm, retriever, embeddings

def create_manual_chains(llm):
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QA_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            ("system", "Context:\n{context}"),
        ]
    )
    qa_chain = qa_prompt | llm | StrOutputParser()

    return contextualize_q_chain, qa_chain

def format_docs(docs):
    # join retrieved docs for the QA system prompt
    return "\n\n".join(doc.page_content for doc in docs)

# -------------------- Eval data --------------------
eval_data = {
    'question': [
        "How many people were killed at Tapin North in 2018?",
        "What could have averted the 29 December 2016 Rajmahal OCP disaster?"
        "What is the capital of India?",
    ],
    'ground_truth': [
        "The major accident at Tapin North on 21 July 2018 killed 4 people.",
        "The accident could have been averted if: 1. no work was done against geological disturbances, 2. the OB dump had been removed by de-capping, 3. no men were deployed when cracks were visible, and 4. special care had been taken in the geologically disturbed area."
        "I do not know. My knowledge is limited to Indian mining accident records from 2016-2022.",
    ]
}
eval_dataset = Dataset.from_dict(eval_data)

# -------------------- RAG pipeline --------------------
def run_rag_pipeline_once(example, contextualize_q_chain, qa_chain, retriever):
    """
    Single-run pipeline. Uses passed chain/retriever objects directly (no pickling).
    """
    query = example['question']
    chat_history = []
    standalone_question = query
    # contextualize question (with retries)
    # try:
    #     standalone_question = _invoke_with_retries(contextualize_q_chain.invoke, {
    #         "input": query,
    #         "chat_history": chat_history
    #     })
    # except Exception as e:
    #     return {"question": query, "answer": f"ERROR: contextualize failed: {e}", "contexts": []}

    # retrieve docs (wrap retriever invoke)
    try:
        docs = _invoke_with_retries(retriever.invoke, standalone_question)
    except Exception as e:
        return {"question": query, "answer": f"ERROR: retriever failed: {e}", "contexts": []}

    contexts = [doc.page_content for doc in docs]

    # answer using QA chain (with retries)
    try:
        answer = _invoke_with_retries(qa_chain.invoke, {
            "input": query,
            "chat_history": chat_history,
            "context": format_docs(docs)
        })
    except Exception as e:
        return {"question": query, "answer": f"ERROR: qa failed: {e}", "contexts": contexts}

    return {"question": query, "answer": answer, "contexts": contexts}

# -------------------- Main --------------------
def main(use_cache: bool = False, clear_cache: bool = False):
    # handle cache flags
    if clear_cache and os.path.exists(CACHE_PATH):
        os.remove(CACHE_PATH)
        print(f"Cleared cache {CACHE_PATH}")

    api_key = load_api_key()
    llm, retriever, embeddings = initialize_components(api_key, PERSIST_DIRECTORY)
    contextualize_q_chain, qa_chain = create_manual_chains(llm)

    # If use_cache is True and cached results exist, load and skip LLM calls
    if use_cache and os.path.exists(CACHE_PATH):
        print(f"Loading cached results from {CACHE_PATH} ...")
        df = pd.read_json(CACHE_PATH, lines=True)
        results_df = df
    else:
        print("Running RAG pipeline on test questions (serial, rate-limited)...")

        # Serial loop — avoids pickling issues entirely
        results = []
        for i, example in enumerate(eval_dataset):
            print(f"[{i+1}/{len(eval_dataset)}] Query: {example['question']}")
            try:
                res = run_rag_pipeline_once(example, contextualize_q_chain, qa_chain, retriever)
            except Exception as e:
                res = {"question": example['question'], "answer": f"ERROR: unexpected: {e}", "contexts": []}
            print(f" -> Answer: {res['answer'][:200]}")  # print first 200 chars
            results.append(res)

            # Save incremental cache only if user asked to use_cache
            if use_cache:
                tmp_df = pd.DataFrame(results)
                tmp_df.to_json(CACHE_PATH, orient="records", lines=True)

        results_df = pd.DataFrame(results)

    # Prepare dataset for ragas evaluate: combine eval_dataset with results (align by question)
    merged_df = []
    base_df = eval_dataset.to_pandas()

    for _, row in base_df.iterrows():
        q = row['question']
        gt = row.get('ground_truth', "")
        match = results_df[results_df['question'] == q]
        if not match.empty:
            ans = match.iloc[0].get('answer', "")
            contexts = match.iloc[0].get('contexts', [])
        else:
            ans = ""
            contexts = []
        merged_df.append({
            "user_input": q,
            "ground_truth": gt,
            "answer": ans,
            "contexts": contexts
        })

    ragas_input_df = pd.DataFrame(merged_df)
    results_dataset = Dataset.from_pandas(ragas_input_df)

    # Wrap LLMs/embeddings for ragas
    gemini_llm_wrapper = LangchainLLMWrapper(llm)
    gemini_embeddings_wrapper = LangchainEmbeddingsWrapper(embeddings)

    print("Running Ragas evaluation...")

    print("Setting ragas.settings.max_workers = 1 to run serially.")
    
    serial_run_config = RunConfig(max_workers=1)

    faithfulness_metric = Faithfulness()
    relevancy_metric = ResponseRelevancy()
    precision_metric = ContextPrecision()

    result = evaluate(
        dataset=results_dataset,
        metrics=[
            faithfulness_metric,
            relevancy_metric,
            precision_metric,
        ],
        llm=gemini_llm_wrapper,
        embeddings=gemini_embeddings_wrapper,
        run_config=serial_run_config
    )

    print("Evaluation Complete. Results:")
    result_df = result.to_pandas()
    print(result_df)
    result_df.to_csv("ragas_evaluation_results.csv", index=False)
    print("Saved ragas_evaluation_results.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument("--use-cache", action="store_true", help="Load and save incremental cache (results_cache.jsonl)")
    parser.add_argument("--clear-cache", action="store_true", help="Delete cache file before running")
    args = parser.parse_args()

    freeze_support()
    main(use_cache=args.use_cache, clear_cache=args.clear_cache)
