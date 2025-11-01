import os
import sys
import pymongo
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma # <-- 1. Correct import
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# -------------------- CONFIG --------------------
# --- Chroma Config ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIRECTORY = os.path.join(SCRIPT_DIR, "chroma_db") # <-- 2. Absolute path
EMBEDDING_MODEL = "models/text-embedding-004"
LLM_MODEL = "models/gemini-pro-latest"

# --- MongoDB Config ---
load_dotenv()
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
MONGO_DB_NAME = "mines_safety"             # <-- !! UPDATE THIS !!
MONGO_COLLECTION_NAME = "dgms_reports" # <-- !! UPDATE THIS !!
# ------------------------------------------------

# --- System Prompts ---
CONTEXTUALIZE_Q_SYSTEM_PROMPT = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

QA_SYSTEM_PROMPT = (
    "You are a 'Digital Mine Safety Officer,' an expert AI assistant. "
    "Your knowledge base consists of Indian mining accident records from DGMS (including Coal 2016-2022 and Non-Coal 2015) " # <-- Updated scope
    "AND real-time data from a live database."
    
    "You must use ONLY the following pieces of retrieved context to answer the user's question. "
    "The context is separated into 'PDF Context' (historical data) and 'Real-time Data' (live updates)."
    
    "Do not use any outside knowledge or make assumptions."

    "--- Your Tasks ---"
    "Based on the provided context, your tasks are to: "
    "1. Answer specific queries about accident details, locations, timelines, types, and machinery involved. "
    "2. Identify and highlight potential safety hazards, trends, or patterns. "
    "3. Suggest potential root causes for incidents ('Had...' statements) if they are mentioned in the text. "
    
    "4. **CRITICAL TASK: When you describe an accident or a general cause (like 'Fall of Roof' or 'Dumpers'),**"
    "   **you MUST check the context for an associated 'Cause Code' (e.g., Code: 0111, Code: 0335).**"
    "   **If a code is present, include it in your answer in parentheses, like this: Fall of Roof (Code: 0111).**"
    
    "--- Your Response Rules ---"
    "If the answer is not found in the provided context, you must state that the "
    "information is not available in the retrieved records. "
    "Be precise, analytical, and focused on safety."
)
# ------------------------------------------------

def load_api_key():
    """Loads the Google API Key from the .env file."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found. Please set it in your .env file.")
        sys.exit(1)
    return api_key

def initialize_components(api_key, persist_directory):
    """Initializes and returns the LLM, retriever, and MongoDB collection."""
    
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
    
    # --- ChromaDB Vector Store ---
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # --- 3. Use MMR Retriever ---
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20} # Returns 5 best docs
    )
    
    # --- 4. Initialize MongoDB Client ---
    try:
        if not MONGO_CONNECTION_STRING:
            print("Error: MONGO_CONNECTION_STRING not found in .env file.")
            sys.exit(1)
        
        mongo_client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
        # Ping server to verify connection
        mongo_client.admin.command('ping') 
        mongo_db = mongo_client[MONGO_DB_NAME]
        mongo_collection = mongo_db[MONGO_COLLECTION_NAME]
        print("--- Components Initialized (Chroma & MongoDB) ---")
        return llm, retriever, mongo_collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)
    # ---------------------------------

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

def format_docs(docs):
    """Helper function to format retrieved LangChain documents into a string."""
    return "\n\n".join(doc.page_content for doc in docs)

def retrieve_from_mongodb(collection, query_text: str, k: int = 3) -> list[str]:
    """
    Retrieves the top k relevant documents from MongoDB as formatted strings.
    """
    if collection is None:
        return []
    try:
        # Use $text search on the compound index
        results = collection.find(
            {"$text": {"$search": query_text}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(k)

        contexts = []
        for doc in results:
            # Format the full JSON into a readable context block
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

def start_chat_session(llm, retriever, mongo_collection, contextualize_q_chain, qa_chain):
    """Starts the interactive chat loop with the user."""
    
    print("--- Chatbot is ready. Type 'exit' to quit. ---")
    
    chat_history = []

    while True:
        try:
            query = input("You: ")
            if query.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break
            
            # --- HYBRID RAG FLOW ---
            
            chain_input = {"input": query, "chat_history": chat_history}
            
            if chat_history:
                standalone_question = contextualize_q_chain.invoke(chain_input)
            else:
                standalone_question = query
            
            print(f"[DEBUG] Retrieving from ChromaDB (PDFs)...")
            chroma_docs = retriever.invoke(standalone_question)
            
            print(f"[DEBUG] Retrieving from MongoDB (Real-time)...")
            mongo_contexts = retrieve_from_mongodb(mongo_collection, standalone_question, k=3)
            
            # Format and Combine the context
            chroma_context_str = format_docs(chroma_docs)
            mongo_context_str = "\n\n".join(mongo_contexts)
            
            combined_context = (
                f"--- PDF Context (Historical) ---\n{chroma_context_str}\n\n"
                f"--- Real-time Data (Live) ---\n{mongo_context_str}"
            )
            # ---------------------------
            
            answer = qa_chain.invoke({
                "input": query,
                "chat_history": chat_history,
                "context": combined_context
            })
            
            print(f"Chatbot: {answer}")
            
            chat_history.append(HumanMessage(content=query))
            chat_history.append(AIMessage(content=answer))
        
        except Exception as e:
            print(f"An error occurred: {e}")
            break

def main():
    """Main function to run the chatbot."""
    try:
        api_key = load_api_key()
        llm, retriever, mongo_collection = initialize_components(api_key, PERSIST_DIRECTORY)
        contextualize_q_chain, qa_chain = create_manual_chains(llm)
        start_chat_session(llm, retriever, mongo_collection, contextualize_q_chain, qa_chain)
    
    except Exception as e:
        print(f"A critical error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()