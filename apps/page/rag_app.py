from src.utils.redis_handler import RedisHandler
import streamlit as st
import os
import redis
import sys

# Add the project root to the path to import from apps.backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from apps.src.tools.vector_store import (
    create_index_with_file_objects,
    retrieve,
    check_directory_exists,
)

st.set_page_config(page_title="PDF RAG System", page_icon="📚", layout="wide")


@st.cache_resource
def get_redis_vector_search_connection():
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=1,
            decode_responses=True,  # Automatically decode response bytes to strings
        )
        return r
    except Exception as e:
        st.error(f"Failed to connect to Redis: {e}")
        return None


def main():
    st.title("📚 文件管理系統")
    st.write("上傳 PDF 文件並使用查詢系統進行查詢。")

    # redis handler
    redis_handler = RedisHandler(redis_connection=get_redis_vector_search_connection())
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["建立向量資料庫", "向量查詢系統"])

    with tab1:
        st.header("創建向量資料庫")

        # File uploader for multiple PDF files
        uploaded_files = st.file_uploader(
            "Upload PDF documents", type=["pdf"], accept_multiple_files=True
        )

        name_of_db = st.text_input("Enter a name for the vector database")

        if uploaded_files:
            st.write(f"📄 {len(uploaded_files)} files uploaded")

            # Display uploaded filenames
            for file in uploaded_files:
                st.text(f"- {file.name} ({round(file.size/1024, 1)} KB)")

        # Button to create vector database
        if st.button(
            "Create Vector Database", disabled=not uploaded_files or not name_of_db
        ):
            with st.spinner(
                "Creating vector database... This may take a while depending on the number and size of documents."
            ):
                try:
                    # Process the uploaded files
                    create_index_with_file_objects(name_of_db, uploaded_files)
                    redis_handler.set_value(name_of_db, name_of_db)
                    st.success("✅ Vector database created successfully!")
                    # Force refresh to update vector_store_exists status
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error creating vector database: {str(e)}")

    with tab2:
        st.header("向量查詢")

        # Select existing vector database
        db_name = st.selectbox(
            "Select an existing vector database", redis_handler.get_all_keys()
        )
        RedisHandler.set_current_key(db_name)
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
