import os
import sys
from dotenv import load_dotenv
from datasets import Dataset
import pandas as pd

from ragas import evaluate
from ragas.metrics import (
    Faithfulness,      
    ResponseRelevancy, 
    ContextPrecision,  
)
from ragas.llms import LangchainLLMWrapper  

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

PERSIST_DIRECTORY = "./chroma_db"
EMBEDDING_MODEL = "models/text-embedding-004"
LLM_MODEL = "models/gemini-pro-latest"

CONTEXTUALIZE_Q_SYSTEM_PROMPT = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

QA_SYSTEM_PROMPT = (
    "You are a 'Digital Mine Safety Officer,' an expert AI assistant. "
    "Your knowledge base consists ONLY of Indian mining accident records "
    "from the Directorate General of Mines Safety (DGMS) from 2016-2022."
    "You must use ONLY the following pieces of retrieved context to answer the user's question. "
    "Do not use any outside knowledge or make assumptions."
    "If the answer is not found in the provided context, you must state that the "
    "information is not available in the retrieved records. "
    "Be precise, analytical, and focused on safety."
)


def load_api_key():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found.")
        sys.exit(1)
    return api_key

def initialize_components(api_key, persist_directory):
    if not os.path.exists(persist_directory):
        print(f"Error: Chroma DB directory not found at {persist_directory}")
        sys.exit(1)
    
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=api_key
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key
    )
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    retriever = vector_store.as_retriever()
    
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
    return "\n\n".join(doc.page_content for doc in docs)

eval_data = {
    'question': [
        "How many people were killed at Tapin North in 2018?",
        "What could have averted the 2016 Rajmahal OCP disaster?",
        "What is the capital of India?",
    ],
    'ground_truth': [
        "The major accident at Tapin North on 21 July 2018 killed 4 people.",
        "The accident could have been averted if: 1. no work was done against geological disturbances, 2. the OB dump had been removed by de-capping, 3. no men were deployed when cracks were visible, and 4. special care had been taken in the geologically disturbed area.",
        "I do not know. My knowledge is limited to Indian mining accident records from 2016-2022.",
    ]
}
eval_dataset = Dataset.from_dict(eval_data)

api_key = load_api_key()
llm, retriever, embeddings = initialize_components(api_key, PERSIST_DIRECTORY) # Get embeddings
contextualize_q_chain, qa_chain = create_manual_chains(llm)

def run_rag_pipeline(query_dict):
    query = query_dict['question']
    chat_history = [] 
    
    standalone_question = contextualize_q_chain.invoke({
        "input": query, 
        "chat_history": chat_history
    })
    
    docs = retriever.invoke(standalone_question)
    contexts = [doc.page_content for doc in docs]
    
    answer = qa_chain.invoke({
        "input": query,
        "chat_history": chat_history,
        "context": format_docs(docs)
    })
    
    return {
        "answer": answer,
        "contexts": contexts
    }

print("Running RAG pipeline on test questions...")
results_dataset = eval_dataset.map(run_rag_pipeline)

gemini_llm_wrapper = LangchainLLMWrapper(llm)
gemini_embeddings_wrapper = LangchainLLMWrapper(embeddings)

print("Running Ragas evaluation...")

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
    embeddings=gemini_embeddings_wrapper
)

print("Evaluation Complete. Results:")
result_df = result.to_pandas()
print(result_df)

result_df.to_csv("ragas_evaluation_results.csv", index=False)