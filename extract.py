"""
PDF Document Extraction and Vector Store Creation

This script processes PDF files from the data directory, extracts text,
splits into chunks, and stores in a ChromaDB vector database for RAG retrieval.
"""

import os
import sys
import glob
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env file.")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
PERSIST_DIRECTORY = os.path.join(SCRIPT_DIR, "chroma_db")

# Embedding configuration
EMBEDDING_MODEL = "models/text-embedding-004"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 400


def load_pdfs(data_dir: str) -> list:
    """Load all PDFs from the data directory."""
    print(f"Loading all PDFs from: {data_dir}\n")
    pdf_paths = glob.glob(os.path.join(data_dir, "*.pdf"))
    
    if not pdf_paths:
        print(f"Error: No PDF files found in {data_dir}")
        sys.exit(1)
    
    all_pages = []
    for pdf_path in pdf_paths:
        print(f"Processing: {os.path.basename(pdf_path)}...")
        try:
            loader = UnstructuredPDFLoader(pdf_path, mode="paged", strategy="ocr_only")
            pages = loader.load()
            all_pages.extend(pages)
            print(f"-> Loaded {len(pages)} pages.")
        except Exception as e:
            print(f"Error loading {pdf_path}: {e}")
    
    print(f"\nSuccessfully loaded a total of {len(all_pages)} pages from {len(pdf_paths)} documents.")
    return all_pages


def split_documents(pages: list, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list:
    """Split documents into chunks for embedding."""
    print("\nSplitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(pages)
    print(f"Split into {len(chunks)} chunks.")
    
    if chunks:
        print("\n--- Example Chunk (First 500 chars) ---")
        print(chunks[0].page_content[:500])
        print("\n--- Metadata of the first chunk ---")
        print(chunks[0].metadata)
    else:
        print("No chunks were created. Check your document and splitter settings.")
    
    return chunks


def create_vector_store(chunks: list, api_key: str, persist_directory: str) -> Chroma:
    """Create and persist the Chroma vector store."""
    print("\nInitializing Gemini embedding model...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key
    )

    print("Creating vector store with Chroma...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    print(f"\nSuccessfully created vector store.")
    print(f"Total vectors stored: {vector_store._collection.count()}")
    return vector_store


def main():
    """Main entry point for PDF extraction and vector store creation."""
    pages = load_pdfs(DATA_DIR)
    chunks = split_documents(pages)
    create_vector_store(chunks, api_key, PERSIST_DIRECTORY)


if __name__ == "__main__":
    main()