from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

class SearchCauseCodeDBTool:
    def __init__(self):
        self.name = "search_cause_code_db"
        self.description = "Searches the cause code database for a given query."
        self.vector_store = self._load_vector_store()

    def _load_vector_store(self):
        db_dir = "cause_code_db"
        if not os.path.exists(db_dir):
            print(f"Error: Cause code database not found at {db_dir}")
            return None
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=os.getenv("GOOGLE_API_KEY"))
        return Chroma(persist_directory=db_dir, embedding_function=embeddings)

    def use(self, query: str) -> str:
        print(f"Searching cause code database for: {query}")
        if not self.vector_store:
            print("Cause code vector store not available.")
            return ""

        try:
            results = self.vector_store.similarity_search(query, k=3)
            if results:
                return "\n\n".join([doc.page_content for doc in results])
            else:
                return "No results found."
        except Exception as e:
            print(f"Error searching cause code database: {e}")
            return ""
