
import os
import re
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class FindCauseCodeTool:
    """A tool to find the most relevant cause code from a dedicated vector store."""

    def __init__(self):
        self.name = "find_cause_code"
        self.description = "Finds the most similar cause code for a given brief cause by searching a specialized vector database."
        self.vector_store = self._load_vector_store()

    def _load_vector_store(self):
        db_dir = "cause_code_db"
        if not os.path.exists(db_dir):
            print(f"[ERROR] Cause code database not found at '{db_dir}'. This tool will not work.")
            return None
        
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004", 
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
            return Chroma(persist_directory=db_dir, embedding_function=embeddings)
        except Exception as e:
            print(f"[ERROR] Failed to load cause code vector store: {e}")
            return None

    def use(self, brief_cause: str) -> str:
        """Performs similarity search on the cause code DB and extracts the code."""
        if not self.vector_store or not brief_cause:
            return ""

        print(f"Searching for cause code for: '{brief_cause}'")
        try:
            # Find the single most similar document in the cause_code_db
            results = self.vector_store.similarity_search(brief_cause, k=1)

            if not results:
                print("No similar cause description found in the cause code database.")
                return ""

            # The content of the most similar document
            page_content = results[0].page_content
            print(f"Most similar document content: '{page_content}'")

            # Use a robust regex to find a 3 or 4 digit code
            match = re.search(r"Code: (\d+)", page_content)
            
            if match:
                cause_code = match.group(1)
                print(f"Successfully extracted cause code: {cause_code}")
                return cause_code
            else:
                print("Could not extract a numeric code from the document.")
                return ""

        except Exception as e:
            print(f"[ERROR] An exception occurred in FindCauseCodeTool: {e}")
            return ""
