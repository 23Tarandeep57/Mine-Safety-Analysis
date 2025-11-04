
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv()
PDF_PATH = "cause_codes.pdf"
CHROMA_DB_DIR = "cause_code_db"
EMBEDDING_MODEL = "models/text-embedding-004"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- SCRIPT ---
def main():
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in .env file.")
        return

    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found at {PDF_PATH}")
        return

    print(f"Loading PDF: {PDF_PATH}")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()

    print(f"Splitting {len(documents)} pages into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    print(f"Creating ChromaDB vector store with {len(splits)} chunks...")
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
    vector_store = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    print(f"\n--- ChromaDB for Cause Codes Created ---")
    print(f"Vector store created at: {CHROMA_DB_DIR}")
    print(f"Number of documents: {vector_store._collection.count()}")

if __name__ == "__main__":
    main()
