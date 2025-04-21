from services.llm import RAGLLMService


if __name__ == "__main__":
    # Initialize RAGLLMService
    rag_llm_service = RAGLLMService(session_id="test_session")

    # Example query
    query = "What is the capital of France?"

    # Run the RAG agent with the query
    response = rag_llm_service.rag_agent.invoke(query=query)

    # Print the response
    print(response)
