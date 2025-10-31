import json
import re
from datetime import datetime, timezone
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from .config import GROQ_API_KEY, GROQ_MODEL

_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        _llm_instance = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0.3)
    return _llm_instance

summary_prompt = PromptTemplate(
    input_variables=["report_text"],
    template=(
        "You are a mine safety analysis expert. Summarize this Fatal Accident Report "
        "in 4–6 concise bullet points focusing on: type of incident, root cause, location, "
        "and recommended preventive measures.\n\nReport:\n{report_text}"
    ),
)
