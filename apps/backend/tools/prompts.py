from backend.services.prompts import RETRIEVAL_SYSTEM_PROMPT, QUERY_REWRITE_PROMPT


def create_senario_retrivel_prompt(senario_description):
    """
    Create a prompt for the retriever agent based on the provided scenario description.
    """
    return RETRIEVAL_SYSTEM_PROMPT.format(senario=senario_description)


def create_query_rewrite_prompt(senario_description):
    """
    Create a prompt for the query rewrite agent based on the provided scenario description.
    """
    return QUERY_REWRITE_PROMPT.format(senario=senario_description)
