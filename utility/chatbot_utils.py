import os
import sys
import pymongo
import certifi
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from prompts import CONTEXTUALIZE_Q_SYSTEM_PROMPT, QA_SYSTEM_PROMPT
from utility.config import (
    EMBEDDING_MODEL,
    LLM_MODEL,
    MONGODB_URI,
    MONGODB_DB,
    MONGODB_COLLECTION
)

load_dotenv()

# Chroma persist directory (relative to this file)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIRECTORY = os.path.join(SCRIPT_DIR, "chroma_db")

def load_api_key():
    """Loads the Google API Key from the .env file."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found. Please set it in your .env file.")
        sys.exit(1)
    return api_key

def initialize_components(api_key, persist_directory):
    """Initializes and returns the LLM, vector_store, and MongoDB collection."""
    if not os.path.exists(persist_directory):
        print(f"Error: Chroma DB directory not found at {persist_directory}")
        sys.exit(1)

    try:
        llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=api_key)
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
        vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    except Exception as e:
        print(f"Error initializing Google AI components: {e}")
        sys.exit(1)

    try:
        if not MONGODB_URI:
            print("Error: MONGODB_URI not found in environment.")
            sys.exit(1)

        # Use SSL only for cloud MongoDB (mongodb+srv or mongodb.net)
        is_cloud_mongo = "mongodb+srv" in MONGODB_URI or "mongodb.net" in MONGODB_URI
        if is_cloud_mongo:
            mongo_client = pymongo.MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
        else:
            mongo_client = pymongo.MongoClient(MONGODB_URI)
        
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[MONGODB_DB]
        mongo_collection = mongo_db[MONGODB_COLLECTION]
        print("--- Components Initialized (Chroma & MongoDB) ---")
        return llm, vector_store, mongo_collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)

def create_manual_chains(llm):
    """Creates the two simple chains for re-writing and answering questions."""
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

async def get_standalone_question(chain, chat_history, query):
    if not chat_history:
        return query
    return await chain.ainvoke({"input": query, "chat_history": chat_history})

def retrieve_from_chroma(vector_store, query):
    print(f"[DEBUG] Retrieving from ChromaDB (PDFs)...")
    return vector_store.similarity_search_with_relevance_scores(query, k=5)

def retrieve_from_mongodb(collection, query):
    print(f"[DEBUG] Retrieving from MongoDB (Real-time)...")
    try:
        results = collection.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(3)

        contexts = []
        for doc in results:
            context_str = f"""
Real-time Report ID: {doc.get('report_id')}
Mine: {doc.get('mine_details', {}).get('name')}, {doc.get('mine_details', {}).get('owner')}
Accident Date: {doc.get('accident_date')}
Cause: {doc.get('incident_details', {}).get('brief_cause')}
Summary: {doc.get('summary')}
Best Practices/How to Avert: {', '.join(doc.get('best_practices', []))}
Verification: {doc.get('verification', {}).get('status')}
Source: {doc.get('source_url')}
"""
            contexts.append(context_str)
        return contexts
    except Exception as e:
        print(f"Error querying MongoDB: {e}")
        return []

def format_docs(docs):
    """Helper function to format retrieved LangChain documents into a string."""
    return "\n\n".join(doc.page_content for doc in docs)
