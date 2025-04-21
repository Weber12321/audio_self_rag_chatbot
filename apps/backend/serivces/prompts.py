RETRIEVAL_SYSTEM_PROMPT = """

"""

CHUNK_RELEVANCE_PROMPT = """
You are an AI document validator who determines if a document is semantically relevant to a query.

Query: {query}

Document: {document}

Is this document relevant to the query? Analyze the document's content and the query carefully.
Answer with true if relevant or false if not relevant. Then provide a brief explanation of your reasoning.
Answer:
"""

RAG_RESPONSE_PROMPT = """
You are an AI assistant helping users with their questions.

User Query: {query}

Relevant Documentation:
{documents}

Based on the provided documentation, please give a detailed and accurate response to the query.
Include specific information from the documentation when relevant.
If the documentation doesn't fully answer the query, supplement with your general knowledge.
Answer:
"""

RESPONSE_VALIDATION_PROMPT = """
You are an AI response validator.

Query: {query}

Generated Response: {response}

Does the response adequately answer the query? Consider:
1. Does it address all parts of the question?
2. Is it accurate based on the information available?
3. Is it complete, or are there important aspects missing?

Answer with true if the response is adequate, or false if it needs improvement.
Answer:
"""

QUERY_REWRITE_PROMPT = """
"""
