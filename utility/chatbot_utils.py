import os
import sys
import pymongo
import certifi
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from prompts import CONTEXTUALIZE_Q_SYSTEM_PROMPT, QA_SYSTEM_PROMPT
from utility.config import (
    EMBEDDING_MODEL,
    GROQ_MODEL,
    MONGODB_URI,
    MONGODB_DB,
    MONGODB_COLLECTION
)

load_dotenv()

# Chroma persist directory (relative to this file)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIRECTORY = os.path.join(SCRIPT_DIR, "chroma_db")

def load_api_key():
    """Loads the API keys from the .env file."""
    google_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    if not google_key:
        print("Warning: GOOGLE_API_KEY not found. Embeddings may not work.")
    if not groq_key:
        print("Error: GROQ_API_KEY not found. Please set it in your .env file.")
        sys.exit(1)
    return google_key, groq_key

def initialize_components(api_key, persist_directory):
    """Initializes and returns the LLM, vector_store, and MongoDB collection."""
    google_key, groq_key = api_key if isinstance(api_key, tuple) else (api_key, os.getenv("GROQ_API_KEY"))
    
    if not os.path.exists(persist_directory):
        print(f"Error: Chroma DB directory not found at {persist_directory}")
        sys.exit(1)

    try:
        # Use GROQ for LLM (free tier friendly)
        llm = ChatGroq(model=GROQ_MODEL, api_key=groq_key)
        # Use Google for embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=google_key)
        vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    except Exception as e:
        print(f"Error initializing AI components: {e}")
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
        # Try text search first
        results = list(collection.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(3))

        # If no results and query contains "recent" or "latest", fetch the newest documents
        if not results and any(word in query.lower() for word in ["recent", "latest", "new", "accident"]):
            print(f"[DEBUG] Text search failed, fetching most recent documents...")
            results = list(collection.find({}).sort("accident_date", -1).limit(3))
            
        if not results:
             print(f"[DEBUG] No matching documents found in MongoDB.")
             return []

        contexts = []
        for doc in results:
            # Handle best_practices which might be list of dicts or strings
            best_practices = doc.get('best_practices', [])
            if best_practices and isinstance(best_practices[0], dict):
                best_practices_str = ', '.join(str(bp.get('description', bp)) for bp in best_practices)
            else:
                best_practices_str = ', '.join(str(bp) for bp in best_practices) if best_practices else 'N/A'
            
            context_str = f"""
Real-time Report ID: {doc.get('report_id')}
Mine: {doc.get('mine_details', {}).get('name')}, {doc.get('mine_details', {}).get('owner')}
Accident Date: {doc.get('accident_date')}
Cause: {doc.get('incident_details', {}).get('brief_cause')}
Summary: {doc.get('summary')}
Best Practices/How to Avert: {best_practices_str}
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
