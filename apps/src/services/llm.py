import uuid
from langchain_core.chat_history import InMemoryChatMessageHistory
from pydantic import BaseModel, Field

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from src.tools.prompts import (
    create_query_rewrite_prompt,
    create_scenarios_retrivel_prompt,
    create_scenarios_supervisor_prompt,
)
from src.services.prompts import *
from src.tools.models import create_google_model
from src.tools.vector_store import retrieve


class DocumentGrader(BaseModel):
    """Grade the relevance of document with the given context"""

    binary_score: str = Field(
        description="Give a binary score to represent if the given document is related to the given query, true for related and false for not related"
    )


class ResponseGrader(BaseModel):
    """Grade the relevance of query with the given response from rag"""

    binary_score: str = Field(
        description="Give a binary score to represent if the given response is related to the given query, true for related and false for not related"
    )


class RAGLLMService:
    def __init__(self, session_id: str = None, scenarios_description: str = None):
        """Initialize the LLM service with Open AI"""
        if not scenarios_description:
            scenarios_description = ""

        self.retrieval_system_prompt = create_scenarios_retrivel_prompt(
            scenarios_description
        )
        self.query_rewrite_prompt = create_query_rewrite_prompt(scenarios_description)
        if not session_id:
            session_id = str(uuid.uuid4())
        self.memory = InMemoryChatMessageHistory(session_id=session_id)
        self.llm = create_google_model()
        self.rag_agent = self._create_retriever_agent()
        self.document_validation_chain = self._create_validation_chain()
        self.rag_response_chain = self._create_rag_response_chain()
        self.response_validation_chain = self._create_response_validation_chain()
        self.query_rewrite_chain = self._create_query_rewriter_chain()

    def _create_retriever_agent(self):
        """Create a retriever for the LLM"""

        tools = [retrieve]

        agent_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.retrieval_system_prompt.strip(),
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{query}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, agent_prompt)

        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: self.memory,
            input_messages_key="query",
            history_messages_key="chat_history",
        )

        return agent_with_chat_history

    def _create_validation_chain(self):
        """Create a validation chain for the LLM"""
        structured_llm_document_grader = self.llm.with_structured_output(DocumentGrader)
        validation_prompt_template = PromptTemplate.from_template(
            CHUNK_RELEVANCE_PROMPT
        )
        return validation_prompt_template | structured_llm_document_grader

    def _create_rag_response_chain(self):
        """Create a response generator for the RAG LLM"""
        response_prompt = PromptTemplate.from_template(RAG_RESPONSE_PROMPT)
        return response_prompt | self.llm | StrOutputParser()

    def _create_response_validation_chain(self):
        """Create a response validation chain for the LLM"""
        structured_llm_response_grader = self.llm.with_structured_output(ResponseGrader)
        response_validation_prompt_template = PromptTemplate.from_template(
            RESPONSE_VALIDATION_PROMPT
        )
        return response_validation_prompt_template | structured_llm_response_grader

    def _create_query_rewriter_chain(self):
        """Create a query rewriter for the LLM"""
        # Placeholder for actual query rewriting logic
        rewrite_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.query_rewrite_prompt.strip()),
                ("human", "{query}"),
            ]
        )

        return rewrite_prompt | self.llm | StrOutputParser()


class EvalLLMService:

    def __init__(self, scenarios_description: str = None):
        """Initialize the LLM service with Open AI"""
        if not scenarios_description:
            scenarios_description = ""
        self.llm = create_google_model()
        self.system_prompt = create_scenarios_supervisor_prompt(scenarios_description)
        self.eval_chain = self._create_eval_chain()

    def _create_eval_chain(self):
        """
        Build the agent with the given chat history and scenarios description.
        """

        return self.system_prompt | self.llm | StrOutputParser()
