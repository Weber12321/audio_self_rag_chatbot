from io import BytesIO
from typing import operator, List, Sequence, Optional, TypedDict, Annotated
import uuid

from langchain_core.messages import BaseMessage, AIMessage
from src.services.llm import RAGLLMService
from langgraph.graph import StateGraph, END


class SelfRAGWorkflow:
    class SelfRAGState(TypedDict):
        """State for the Self-RAG workflow"""

        messages: Annotated[
            Sequence[BaseMessage], operator.add
        ]  # List of chat messages
        docs: List[str] | str  # Retrieved documents
        is_retrieval_related: bool  # Whether the query is related to retrieval
        validated_docs: List[str]  # Documents that passed validation
        response: str = ""  # Generated response
        response_validated: Optional[bool] = None  # Whether response passed validation
        max_generation: int = 2  # Maximum number of retries
        query_rewritten: bool = False  # Whether query was rewritten
        rewritten_query: str = ""  # Rewritten query if any

    def __init__(self, session_id: str = None, scenarios_description: str = None):
        """Initialize the Self-RAG workflow with Open AI"""
        if not scenarios_description:
            scenarios_description = ""
        if not session_id:
            session_id = str(uuid.uuid4())

        self.session_id = session_id
        self.llm_service = RAGLLMService(
            session_id=self.session_id, scenarios_description=scenarios_description
        )

        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow for the self-RAG agent.

        It should be retrieve_or_respond -> validate_docs(for each document) -> generate_response -> validate_response -> query_rewrite -> generate_final_response.
        If it fails in validate_docs, namely no doc related, it should go back to retrieve_or_respond keep retriving and skip the top_k, max retries twice and if still fails, go to query_rewrite.
        If it fails in validate_response, it should go to query_rewrited.
        """
        # Create workflow
        workflow = StateGraph(self.SelfRAGState)

        # Add nodes
        workflow.add_node("retrieve_or_respond", self.retrieve_or_respond)
        workflow.add_node("validate_docs", self.validate_docs)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("validate_response", self.validate_response)
        workflow.add_node("query_rewrite", self.query_rewrite)
        workflow.add_node("final_response", self.final_response)

        # Define conditional edges
        workflow.add_conditional_edges(
            "retrieve_or_respond", self.check_retrieval_related
        )
        workflow.add_conditional_edges("validate_docs", self.check_validate_docs)
        workflow.add_conditional_edges("validate_response", self.check_max_generation)

        workflow.add_edge("generate_response", "validate_response")
        workflow.add_edge("final_response", END)
        # Set entry point
        workflow.set_entry_point("retrieve_or_respond")

        return workflow.compile()

    def retrieve_or_respond(self, state):
        """An agent which decide to retrieve relevant documents based on the query or reply the LLM answer directly"""
        # Extract the query from the latest human message
        response = self.llm_service.rag_agent.invoke(
            {"query": state["messages"][-1].content},
            config={"configurable": {"session_id": self.session_id}},
        )
        if isinstance(response["output"], str):
            state["is_retrieval_related"] = False
        else:
            state["is_retrieval_related"] = True
        state["docs"] = response["output"]
        return state

    def check_retrieval_related(self, state):
        """Check if the query is related to retrieval"""
        # Check if the query is related to retrieval
        if state["is_retrieval_related"]:
            return "validate_docs"
        else:
            return "final_response"

    def validate_docs(self, state):
        """Validate the retrieved documents is related to the query, keep the related documents and remove the unrelated documents"""
        query = state["messages"][-1].content
        docs = state["docs"]
        validated_docs = []

        for doc in docs:
            response = self.llm_service.document_validation_chain.invoke(
                {"query": query, "document": doc}
            ).binary_score

            # Check if document is validated as relevant
            if response.strip().lower() == "true":
                validated_docs.append(doc)

        # Update the state with validated documents
        state["validated_docs"] = validated_docs

        return state

    def check_validate_docs(self, state):
        """Check if the validated documents are empty or not"""
        # Check if the validated documents are empty
        if not state["validated_docs"]:
            return "query_rewrite"
        else:
            return "generate_response"

    def generate_response(self, state):
        """Generate a response based on the query and validated retrieved documents"""
        is_response_validated = state.get("response_validated")
        if is_response_validated is not None and is_response_validated == False:
            state["max_generation"] += 1

        query = state["messages"][-1].content
        validated_docs = state["validated_docs"]

        # Generate response using the validated documents
        docs_content = "\n\n".join(
            [f"Document {i+1}:\n{doc}" for i, doc in enumerate(validated_docs)]
        )

        # Update the state with the generated response
        state["response"] = self.llm_service.rag_response_chain.invoke(
            {
                "query": query,
                "documents": docs_content,
            }
        )

        return state

    def validate_response(self, state):
        """Validate the generated response twice with LLM response and query"""
        query = state["messages"][-1].content
        response = state["response"]
        response = self.llm_service.response_validation_chain.invoke(
            {
                "query": query,
                "response": response,
            }
        ).binary_score

        # Consider the response valid only if both validations pass
        if response.strip().lower() == "true":
            state["response_validated"] = True
        else:
            state["response_validated"] = False

        return state

    def check_max_generation(self, state):
        if state["response_validated"]:
            return "final_response"
        else:
            if state["max_generation"] >= 2:
                return "query_rewrite"
            else:
                return "generate_response"

    def query_rewrite(self, state: SelfRAGState):
        """Rewrite the query if it failed in the previous stage"""

        new_query = self.llm_service.query_rewrite_chain.invoke(
            {"query": state["messages"][-1].content}
        )
        new_query = (
            "對不起，我無法查詢或整理您的問題，建議您將問題改寫以下新問法並再次查詢: \n"
            + new_query
        )
        # Update state
        state["query_rewritten"] = True
        state["rewritten_query"] = new_query

        return state

    def final_response(self, state):
        """Generate the final response based on the rewritten query"""
        # Generate final response using the rewritten query
        if state["response"]:
            state["messages"] = [AIMessage(content=state["response"])]
        elif state["docs"]:
            state["messages"] = [AIMessage(content=state["docs"])]
        return state
