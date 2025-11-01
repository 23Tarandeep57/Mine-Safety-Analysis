import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
# from langchain.chains import create_history_aware_retriever, create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain

# PERSIST_DIRECTORY = "./chroma_db"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIRECTORY = os.path.join(SCRIPT_DIR, "chroma_db")
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
    
    "Based on the provided context, your tasks are to: "
    "1. Answer specific queries about accident details, locations, timelines, types, and machinery involved. "
    "2. Identify and highlight potential safety hazards, trends, or patterns. "
    "3. Suggest potential root causes for incidents if they are mentioned in the text. "
    "4. If the user's query implies a compliance or hazard check, analyze the context to provide relevant data."
    
    "If the answer is not found in the provided context, you must state that the "
    "information is not available in the retrieved records. "
    "Be precise, analytical, and focused on safety."
)

def load_api_key():
    """Loads the Google API Key from the .env file."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found. Please set it in your .env file.")
        sys.exit(1)
    return api_key

def initialize_components(api_key, persist_directory):
    """Initializes and returns the LLM, embeddings, and retriever."""
    
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
    
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 8, "fetch_k": 20})
    
    print("--- Components Initialized ---")
    return llm, retriever

def create_manual_chains(llm):
    """
    Creates the two simple chains for re-writing
    and answering questions.
    """
    
    # 1. Chain to re-write the question
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()
    
    # 2. Chain to answer the question
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QA_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            ("system", "Context:\n{context}"), # Add context here
        ]
    )
    
    qa_chain = qa_prompt | llm | StrOutputParser()
    
    return contextualize_q_chain, qa_chain

def format_docs(docs):
    """Helper function to format retrieved documents into a string."""
    return "\n\n".join(doc.page_content for doc in docs)

# def start_chat_session(llm, retriever, contextualize_q_chain, qa_chain):
#     """Starts the interactive chat loop with the user."""
    
#     print("--- Chatbot is ready. Type 'exit' to quit. ---")
    
#     chat_history = []

#     while True:
#         try:
#             # --- RAG TRIAD (INPUT) ---
#             query = input("You: ")
#             if query.lower() == 'exit':
#                 print("Chatbot: Goodbye!")
#                 break
            
#             # --- RAG TRIAD LOGGING (Original Query) ---
#             print("\n" + "="*70)
#             print(f"TRIAD 1: Original Query: {query}")
            
#             chain_input = {"input": query, "chat_history": chat_history}
            
#             # --- RAG TRIAD LOGGING (Contextualized Question) ---
#             standalone_question = contextualize_q_chain.invoke(chain_input)
#             print(f"TRIAD 2: Standalone (Retriever) Question: {standalone_question}")

#             # --- RAG TRIAD LOGGING (Retrieved Context) ---
#             documents = retriever.invoke(standalone_question)
#             context = format_docs(documents)
#             print("\n--- TRIAD 3: Retrieved Context ---")
#             print(context)
#             print("----------------------------------\n")
            
#             # Call the final answering chain
#             answer = qa_chain.invoke({
#                 "input": query,
#                 "chat_history": chat_history,
#                 "context": context
#             })
            
#             # --- RAG TRIAD LOGGING (Final Answer) ---
#             print(f"Chatbot: {answer}")
#             print("="*70 + "\n")
            
#             # Update history
#             chat_history.append(HumanMessage(content=query))
#             chat_history.append(AIMessage(content=answer))
        
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             break

def start_chat_session(llm, retriever, contextualize_q_chain, qa_chain):
    """Starts the interactive chat loop with the user."""
    
    print("--- Chatbot is ready. Type 'exit' to quit. ---")
    
    chat_history = []

    while True:
        try:
            query = input("You: ")
            if query.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break
            
            # --- MANUAL RAG FLOW ---
            
            # 1. Create the input dictionary
            chain_input = {"input": query, "chat_history": chat_history}
            
            # 2. Call the first chain to get a standalone question
            standalone_question = contextualize_q_chain.invoke(chain_input)
            
            # 3. Call the retriever manually with that question
            documents = retriever.invoke(standalone_question)
            
            # 4. Format the retrieved documents
            context = format_docs(documents)
            
            # 5. Call the final answering chain
            answer = qa_chain.invoke({
                "input": query,
                "chat_history": chat_history,
                "context": context
            })
            
            # 6. Print the answer and update history
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
        llm, retriever = initialize_components(api_key, PERSIST_DIRECTORY)
        contextualize_q_chain, qa_chain = create_manual_chains(llm)
        start_chat_session(llm, retriever, contextualize_q_chain, qa_chain)
    
    except Exception as e:
        print(f"A critical error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()