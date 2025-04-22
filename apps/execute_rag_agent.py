import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

from backend.services.llm import RAGLLMService


if __name__ == "__main__":

    senario_description = """<input your scenario description here>"""

    # Initialize RAGLLMService
    rag_llm_service = RAGLLMService(
        session_id="test_session", senario_description=senario_description
    )

    # Example query
    query1 = "<your query>？"

    # Run the RAG agent with the query
    response1 = rag_llm_service.rag_agent.invoke(
        {"query": query1},
        config={"configurable": {"session_id": "test_session"}},
    )

    print("-" * 10)
    # Print the response
    print(f"Query: {query1}")
    print("Response:")
    print(response1)
    print("-" * 10)
    query2 = "<your extra>？"

    response2 = rag_llm_service.rag_agent.invoke(
        {"query": query2},
        config={"configurable": {"session_id": "test_session"}},
    )
    print(f"Query: {query1}")
    print("Response:")
    print(response2)
