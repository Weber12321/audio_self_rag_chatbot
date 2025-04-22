from src.services.prompts import (
    RETRIEVAL_SYSTEM_PROMPT,
    QUERY_REWRITE_PROMPT,
    SUPERVISOR_PROMPT,
)


def create_scenarios_retrivel_prompt(scenarios_description):
    """
    Create a prompt for the retriever agent based on the provided scenario description.
    """
    return RETRIEVAL_SYSTEM_PROMPT.format(scenarios=scenarios_description)


def create_scenarios_supervisor_prompt(scenarios_description):
    """
    Create a prompt for the supervisor agent based on the provided scenario description.
    """
    return SUPERVISOR_PROMPT.format(
        scenarios=scenarios_description, chat_history="{chat_history}"
    )


def create_query_rewrite_prompt(scenarios_description):
    """
    Create a prompt for the query rewrite agent based on the provided scenario description.
    """
    return QUERY_REWRITE_PROMPT.format(scenarios=scenarios_description)
