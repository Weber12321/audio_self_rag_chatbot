from typing import List, TypedDict
from src.services.llm import EvalLLMService
from langchain_core.messages import BaseMessage
from langchain_core.prompt_values import ChatPromptValue
from langgraph.graph import StateGraph, END


class SupervisorAgent:
    """
    A supervisor agent which can evaluate the chat history with given scenarios.
    """

    class SupervisorState(TypedDict):
        """State for the Supervisor agent"""

        chat_history: List[BaseMessage]
        feedback: str

    def __init__(self, scenarios_description: str = None):
        """Initialize the Supervisor agent with Open AI"""
        if not scenarios_description:
            scenarios_description = ""

        self.scenarios_description = scenarios_description
        self.llm_service = EvalLLMService(
            scenarios_description=self.scenarios_description
        )
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow for the supervisor agent."""
        # Create workflow
        workflow = StateGraph(self.SupervisorState)

        # Add nodes
        workflow.add_node("evaluate", self.evaluate)

        # Define edges
        workflow.add_edge("evaluate", END)
        workflow.set_entry_point("evaluate")

        return workflow

    def evaluate(self, state: SupervisorState) -> SupervisorState:
        """Evaluate the chat history with the given scenarios."""
        # Get the chat history
        chat_history = state["chat_history"]
        prompt_values = ChatPromptValue(messages=chat_history)
        # Generate feedback using the LLM service
        feedback = self.llm_service.eval_chain.invoke(
            {
                "chat_history": prompt_values.to_string(),
            }
        )

        # Update the state with the feedback
        state["feedback"] = feedback

        return state
