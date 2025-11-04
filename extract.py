import os
import sys
import glob
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_community.vectorstores import Chroma
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

print(f"Loading all PDFs from: {DATA_DIR}\n")
#load all pdfs
pdf_paths = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
if not pdf_paths:
    print(f"Error: No PDF files found in {DATA_DIR}")
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

#split documents
print("\nSplitting text into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=400,
    length_function=len,
    is_separator_regex=False,
)
chunks = text_splitter.split_documents(all_pages)
print(f"Split into {len(chunks)} chunks.")

if chunks:
    print("\n--- Example Chunk (First 500 chars) ---")
    print(chunks[0].page_content[:500])
    
    print("\n--- Metadata of the first chunk ---")
    print(chunks[0].metadata)
else:
    print("No chunks were created. Check your document and splitter settings.")

#Initialize Embeddings
print("\nInitializing Gemini embedding model...")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=api_key
)

#Create and Persist Vector Store
print("Creating vector store with Chroma...")
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=PERSIST_DIRECTORY  # Use the absolute path
)


print(f"\nSuccessfully created vector store.")
print(f"Total vectors stored: {vector_store._collection.count()}")


# loader = PyPDFLoader(pdf_path)
# pages = loader.load() 
# print(f"Successfully loaded {len(pages)} pages.")

# print("\nSplitting text into chunks...")

# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,
#     chunk_overlap=200,
#     length_function=len,
#     is_separator_regex=False,
# )

# chunks = text_splitter.split_documents(pages)

# print(f"Split into {len(chunks)} chunks.")

# if chunks:
#     print("\n--- Example Chunk (First 500 chars) ---")
#     print(chunks[0].page_content[:500])
    
#     print("\n--- Metadata of the first chunk ---")
#     print(chunks[0].metadata)
# else:
#     print("No chunks were created. Check your document and splitter settings.")


# print("\nInitializing Gemini embedding model...")
# embeddings = GoogleGenerativeAIEmbeddings(
#     model="models/text-embedding-004",
#     google_api_key=api_key
# )

# print("Creating vector store with Chroma...")
# vector_store = Chroma.from_documents(
#     documents=chunks,
#     embedding=embeddings,
#     persist_directory=PERSIST_DIRECTORY  # Directory to save the DB
# )

# print(f"\nSuccessfully created vector store.")
# print(f"Total vectors stored: {vector_store._collection.count()}")