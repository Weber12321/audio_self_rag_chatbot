from typing import Dict, List
import asyncio

from src.utils.redis_handler import RedisHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from src.agents.rag_agent import SelfRAGWorkflow


def convert_to_langchain_messages(messages: List[Dict]) -> List[BaseMessage]:
    """Convert the session state messages to langchain message objects"""
    lc_messages = []
    for message in messages:
        if message["role"] == "user":
            lc_messages.append(HumanMessage(content=message["content"]))
        elif message["role"] == "assistant":
            lc_messages.append(AIMessage(content=message["content"]))
    return lc_messages


async def call_agent(initial_state, agents):
    """Call the agent with the initial state"""
    state = await agents.workflow.ainvoke(initial_state)
    return state["messages"][-1].content


if __name__ == "__main__":
    prompt = "請問你能幫我找一些關於人工智慧的資料嗎？"
    agents = SelfRAGWorkflow()
    RedisHandler.set_current_key("長榮海運病毒手冊")
    initial_state = {
        "messages": convert_to_langchain_messages(
            [{"role": "user", "content": prompt}]
        ),
        "max_generation": 2,
        "docs": [],
        "is_retrieval_related": False,
        "validated_docs": [],
        "response": "",
        "response_validated": None,
        "query_rewritten": False,
        "rewritten_query": "",
    }

    print("Starting the workflow...")

    async def main():
        # Create a task so it runs in the background
        agent_task = asyncio.create_task(
            call_agent(initial_state=initial_state, agents=agents)
        )

        # This will run immediately, not waiting for the task to complete
        print("print something while the workflow is running")

        # Now wait for the task to complete and get its result
        result = await agent_task

        if result:
            print("Async workflow execution finished")
            print(f"Result: {result}")

        return result

    asyncio.run(main())
