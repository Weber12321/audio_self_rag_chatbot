import streamlit as st
import os
import sys

# Add the project root to the path to import from apps.backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from apps.backend.tools.vector_store import (
    create_index_with_file_objects,
    retrieve,
    check_directory_exists,
)

st.set_page_config(page_title="PDF RAG System", page_icon="📚", layout="wide")


def main():
    st.title("📚 PDF RAG System")
    st.write(
        "Upload PDFs to create a vector database, then ask questions about your documents."
    )

    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["Create Vector DB", "Query Documents"])

    with tab1:
        st.header("Create Vector Database")

        # Check if vector store already exists
        vector_store_exists = check_directory_exists()
        if vector_store_exists:
            st.warning("⚠️ Vector database already exists. You can query it directly.")

        # File uploader for multiple PDF files
        uploaded_files = st.file_uploader(
            "Upload PDF documents", type=["pdf"], accept_multiple_files=True
        )

        if uploaded_files:
            st.write(f"📄 {len(uploaded_files)} files uploaded")

            # Display uploaded filenames
            for file in uploaded_files:
                st.text(f"- {file.name} ({round(file.size/1024, 1)} KB)")

        # Button to create vector database
        if st.button(
            "Create Vector Database", disabled=vector_store_exists or not uploaded_files
        ):
            with st.spinner(
                "Creating vector database... This may take a while depending on the number and size of documents."
            ):
                try:
                    # Process the uploaded files
                    create_index_with_file_objects(uploaded_files)
                    st.success("✅ Vector database created successfully!")
                    # Force refresh to update vector_store_exists status
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error creating vector database: {str(e)}")

    with tab2:
        st.header("Query Your Documents")

        # Check if vector store exists
        if not check_directory_exists():
            st.warning(
                "⚠️ No vector database found. Please create one first in the 'Create Vector DB' tab."
            )
            st.stop()

        # Text area for query input
        query = st.text_area("Enter your question about the documents:", height=100)

        # Button to perform search
        if st.button("Search", disabled=not query):
            with st.spinner("Searching for relevant information..."):
                try:
                    results = retrieve(query)

                    st.subheader("Search Results:")
                    if isinstance(results, str):
                        st.info(results)
                    else:
                        for i, result in enumerate(results, 1):
                            with st.expander(f"Result {i}"):
                                st.write(result)
                except Exception as e:
                    st.error(f"❌ Error during search: {str(e)}")


if __name__ == "__main__":
    main()
