import os
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Union


def create_google_embedding():
    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("GOOGLE_GENERATIVE_EMBEDDING", "models/text-embedding-004"),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
    )


def count_tokens(text: str) -> int:
    pass


def create_summarization_with_plaintext():
    """Use langchain to create a summarization chain for the text."""
    pass


def check_directory_exists() -> bool:
    """Check if a directory exists.

    Args:
        directory (str): The path to the directory to check.

    Returns:
        bool: True if the directory exists, False otherwise.
    """
    directory = os.getenv("VECTORSTORE_PATH", "fixtures/vector_db")

    return os.path.exists(directory)


def create_index_with_text(file_objects):
    """Use FAISS and langchain to create an index for the vector store."""
    if check_directory_exists():
        print("Directory already exists. Exiting...")
        return

    semantic_chunker = SemanticChunker(
        create_google_embedding(), breakpoint_threshold_type="percentile"
    )

    all_splits = []

    # Process each markdown file
    for file_path in file_objects:
        semantic_chunks = semantic_chunker.create_documents(
            [d.page_content for d in documents]
        )
    if not all_splits:
        raise ValueError("No documents were processed from the markdown files.")

    # Further split by characters
    final_splits = text_splitter.split_documents(all_splits)

    # Create vector store
    vector_store = FAISS.from_documents(final_splits, OpenAIEmbeddings())

    # Save the vector store locally
    save_path = os.getenv("VECTORSTORE_PATH", "fixtures/vector_db")
    vector_store.save_local(save_path)
    print(f"Vector store saved to {save_path}")


def retrieve(query: str) -> Union[List[str] | str]:
    """Retrieve relevant documents from the vector store based on the query.
    Args:
        query (str): The search query.
    Returns:
        List[str]: A list of relevant document contents.
    """
    vectorstore = FAISS.load_local(
        os.getenv("VECTORSTORE_PATH", "fixtures/vector_db"),
        GoogleGenerativeAIEmbeddings(
            model=os.getenv("GOOGLE_GENERATIVE_EMBEDDING", "textembedding-gecko"),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        ),
        allow_dangerous_deserialization=True,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    docs = retriever.get_relevant_documents(query)
    if not docs:
        return "No relevant documents found."
    return [doc.page_content for doc in docs]
