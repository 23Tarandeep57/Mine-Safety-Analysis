import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

pdf_path = r"C:\Users\mahim\cl_hack\data\sanket0404_2024.pdf"
print(f"Loading PDF: {pdf_path}\n")

loader = PyPDFLoader(pdf_path)
pages = loader.load() 
print(f"Successfully loaded {len(pages)} pages.")

print("\nSplitting text into chunks...")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

chunks = text_splitter.split_documents(pages)

print(f"Split into {len(chunks)} chunks.")

# if chunks:
#     print("\n--- Example Chunk (First 500 chars) ---")
#     print(chunks[0].page_content[:500])
    
#     print("\n--- Metadata of the first chunk ---")
#     print(chunks[0].metadata)
# else:
#     print("No chunks were created. Check your document and splitter settings.")
print("\nInitializing Gemini embedding model...")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=api_key
)

print("Creating vector store with Chroma...")
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"  # Directory to save the DB
)

print(f"\nSuccessfully created vector store.")
print(f"Total vectors stored: {vector_store._collection.count()}")