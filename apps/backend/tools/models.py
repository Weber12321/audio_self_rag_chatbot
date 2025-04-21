import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI


def create_google_embedding():
    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("GOOGLE_GENERATIVE_EMBEDDING", "models/text-embedding-004"),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
    )


def create_google_model():
    return ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_GENERATIVE_MODEL", "gemini-2.0-flash"),
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )
