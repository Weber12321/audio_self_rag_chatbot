import logging
import os
from src.utils.redis_handler import RedisHandler
from src.tools.models import create_google_embedding
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from typing import List, Union
from langchain_community.document_loaders import PyPDFLoader


def check_directory_exists(key: str) -> bool:
    """Check if a directory exists.

    Args:
        directory (str): The path to the directory to check.

    Returns:
        bool: True if the directory exists, False otherwise.
    """
    directory = os.getenv("VECTORSTORE_PATH", "fixtures/vector_db")

    return os.path.exists(os.path.join(directory, key))


def create_index_with_file_objects(key, file_objects):
    """Use FAISS and langchain to create an index for the vector store."""
    if check_directory_exists(key):
        print("Directory already exists. Exiting...")
        return
    logging.info("Creating index with file objects...")
    embeddings_function = create_google_embedding()
    semantic_chunker = SemanticChunker(
        embeddings_function, breakpoint_threshold_type="percentile"
    )

    all_splits = []
    logging.info("Processing files...")
    # Process each file
    for file_obj in file_objects:
        # Handle PDF files using PyPDFLoader
        if hasattr(file_obj, "name") and file_obj.name.lower().endswith(".pdf"):

            # Save temporarily to use with PyPDFLoader
            temp_path = f"temp_{file_obj.name}"
            with open(temp_path, "wb") as f:
                f.write(file_obj.getvalue())

            try:
                # Use PyPDFLoader to load and parse the PDF
                loader = PyPDFLoader(temp_path)
                documents = loader.load()

                # Create semantic chunks
                semantic_chunks = semantic_chunker.create_documents(
                    [d.page_content for d in documents]
                )
                all_splits.extend(semantic_chunks)
                print(f"Processed {file_obj.name}, added {len(semantic_chunks)} chunks")
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    if not all_splits:
        raise ValueError("No documents were processed from the files.")

    # Create vector store
    vector_store = FAISS.from_documents(all_splits, embeddings_function)

    # Save the vector store locally
    save_path = os.path.join(os.getenv("VECTORSTORE_PATH", "fixtures/vector_db"), key)

    vector_store.save_local(save_path)
    print(f"Vector store saved to {save_path}")


@tool("retrieve", return_direct=True)
def retrieve(query: str) -> Union[List[str] | str]:
    """Retrieve relevant documents from the vector store based on the query.
    Args:
        query (str): The search query.
    Returns:
        List[str]: A list of relevant document contents.
    """
    if RedisHandler.get_current_key is None:
        raise ValueError(
            "No vector store key found. Please create a vector store first."
        )

    vectorstore = FAISS.load_local(
        os.path.join(
            os.getenv("VECTORSTORE_PATH", "fixtures/vector_db"),
            RedisHandler.get_current_key,
        ),
        create_google_embedding(),
        allow_dangerous_deserialization=True,
    )

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": int(os.getenv("RETRIEVAL_NUMBER", 3))}
    )

    docs = retriever.get_relevant_documents(query)
    if not docs:
        return "No relevant documents found."
    return [doc.page_content for doc in docs]
