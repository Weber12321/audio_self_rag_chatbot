import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI


def create_google_embedding():
    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("GOOGLE_GENERATIVE_EMBEDDING", "models/text-embedding-004"),
        google_api_key="AIzaSyCle6jmFfSjUcUr-D15ieqd-ZOFeKAdOWc",
    )


def create_google_model():
    return ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_GENERATIVE_MODEL", "gemini-2.0-flash"),
        google_api_key="AIzaSyCle6jmFfSjUcUr-D15ieqd-ZOFeKAdOWc",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )
