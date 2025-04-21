import os
from apps.backend.tools.models import create_google_embedding, create_google_model
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Union
from langchain_community.document_loaders import PyPDFLoader
from io import BytesIO


def count_tokens(text: str) -> int:
    llm = create_google_model()
    return llm.get_num_tokens(text)


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


def create_index_with_file_objects(file_objects):
    """Use FAISS and langchain to create an index for the vector store."""
    if check_directory_exists():
        print("Directory already exists. Exiting...")
        return

    embeddings_function = create_google_embedding()
    semantic_chunker = SemanticChunker(
        embeddings_function, breakpoint_threshold_type="percentile"
    )

    all_splits = []

    # Process each file
    for file_obj in file_objects:
        # Handle PDF files using PyPDFLoader
        if hasattr(file_obj, "name") and file_obj.name.lower().endswith(".pdf"):
            # Convert streamlit uploaded file to bytes
            pdf_bytes = BytesIO(file_obj.getvalue())

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
