# app/services/ner_service.py
import pandas as pd

from typing import Dict

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from backend.serivces.prompts import RETRIEVAL_SYSTEM_PROMPT
from backend.tools.models import create_google_model
from backend.tools.vector_store import retrieve


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
    def __init__(self):
        """Initialize the LLM service with Open AI"""
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
                    RETRIEVAL_SYSTEM_PROMPT.strip(),
                ),
                ("human", "{query}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(self.llm, tools, agent_prompt)

        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    def _create_validation_chain(self):
        """Create a validation chain for the LLM"""
        structured_llm_document_grader = self.llm.with_structured_output(DocumentGrader)
        validation_prompt = """
        You are an AI document validator who determines if a document is semantically relevant to a query.
        
        Query: {query}
        
        Document: {document}
        
        Is this document relevant to the query? Analyze the document's content and the query carefully.
        Answer with true if relevant or false if not relevant. Then provide a brief explanation of your reasoning.
        Answer:
        """
        validation_prompt_template = PromptTemplate.from_template(validation_prompt)
        return validation_prompt_template | structured_llm_document_grader

    def _create_rag_response_chain(self):
        """Create a response generator for the RAG LLM"""
        response_template = """
        You are an AI assistant helping users with their questions.
        
        User Query: {query}
        
        Relevant Documentation:
        {documents}
        
        Based on the provided documentation, please give a detailed and accurate response to the query.
        Include specific information from the documentation when relevant.
        If the documentation doesn't fully answer the query, supplement with your general knowledge.
        Answer:
        """

        response_prompt = PromptTemplate.from_template(response_template)
        return response_prompt | self.llm | StrOutputParser()

    def _create_response_validation_chain(self):
        """Create a response validation chain for the LLM"""
        structured_llm_response_grader = self.llm.with_structured_output(ResponseGrader)
        response_validation_prompt = """
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

        response_validation_prompt_template = PromptTemplate.from_template(
            response_validation_prompt
        )
        return response_validation_prompt_template | structured_llm_response_grader

    def _create_query_rewriter_chain(self):
        """Create a query rewriter for the LLM"""
        # Placeholder for actual query rewriting logic
        rewrite_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一個問題改寫的助理，請參考以下文檔內容，並針對使用者輸入的問題進行改寫。請注意改寫的問題不可以完全偏離原本問題的語意。

                    內容：
                    這份文件詳細列出了 KEYPO 平台目前提供的 API 功能。每個大標題代表一支獨立的 API，並解釋其運作邏輯。主要功能涵蓋：
                    監測與通知：
                    警報信：可自訂時間、頻率，針對關鍵字主題發送 Email 警報。
                    AI 分析與報告：
                    GPT 報告：利用大型語言模型自動生成輿情分析報告，包含聲量、關鍵字、概念分析等。
                    資料呈現與視覺化：
                    文章列表：展示相關文章詳細資訊（來源、情緒、互動數等），具備篩選、排序、編修功能。
                    聲量趨勢/資料分佈/傳播趨勢：以圖表視覺化呈現聲量隨時間變化、來源佔比、跨頻道傳播路徑。
                    熱門趨勢分析：
                    熱門關鍵字/HashTag/頻道/排行榜/熱詞網路：分析找出最受關注的關鍵字（結合詞頻與權重）、標籤、頻道（依聲量/情緒分類）、文章（依互動數）及關聯詞彙網絡。
                    意見領袖與社群分析：
                    關鍵領袖/人群發文領袖/人群熱門頻道/文章：識別具影響力的作者 (KOL) 及特定受眾關注的領袖、頻道與文章。
                    網路好感度/社群活躍度/網路互動力：分析整體情緒走向、社群討論熱度及互動數變化。
                    進階功能與工具：
                    啟用多維度/關鍵字風暴/探索概念：進行更深層次的關鍵字關聯比較、找出顯著詞彙、探索語意概念群。
                    競品比較：跨主題比較聲量、好感度、社群活躍度等多項指標。
                    報告下載：一鍵生成包含多種分析面向的綜合報告。
                    篩選/排除：提供強大的資料篩選（聚焦）與排除特定頻道、文章的功能。
                    總體來說，這些 API 提供了從基礎監測、資料整理、趨勢分析到深度洞察、報告產出等全方位的網路輿情數據服務。
                """,
                ),
                ("human", "{query}"),
            ]
        )

        return rewrite_prompt | self.llm | StrOutputParser()


class OpinionLLMService:
    def __init__(self):
        """Initialize the LLM service with Open AI"""
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.opinian_agent = self._create_news_search_agent()
        self.summary_chain = self._create_summary_chain()
        self.sentiment_chain = self._create_sentiment_chain()

    def _create_summary_chain(self):
        summary_prompt = """
        Summarize the following text in 3-5 sentence with same language with the given text, focusing on key points:
        
        {text}
        """
        summary_prompt_template = PromptTemplate.from_template(summary_prompt)
        return summary_prompt_template | self.llm | StrOutputParser()

    def _create_sentiment_chain(self):
        structured_llm_sentiment_grader = self.llm.with_structured_output(
            SentimentGrader
        )
        sentiment_prompt = """
        Analyze the sentiment of the following context.

        context: {context}

        Return positive, neutral or negative.
        Answer in one word.
        Answer:
        """
        sentiment_prompt_template = PromptTemplate.from_template(sentiment_prompt)
        return sentiment_prompt_template | structured_llm_sentiment_grader

    def _create_news_search_agent(self) -> AgentExecutor:
        tools = [search_news]  # List of actual tool objects

        # Create a prompt suitable for an agent with tool calling instructions
        agent_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "If the following query is related to news, opinion analysis, public sentiment, market research, social media analysis, or news analysis. then search it with tool. "
                    "Otherwise answer with: 請參考上述說明輸入與觀點分析、公眾情緒、市場研究、社群媒體分析相關的新聞查詢，謝謝您！",
                ),
                ("human", "{query}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create the agent runnable
        agent = create_openai_tools_agent(self.llm, tools, agent_prompt)

        # Create the executor which handles the tool call loop
        return AgentExecutor(
            agent=agent, tools=tools, verbose=True
        )  # verbose=True shows the steps

    def translate_sentiment_tag(self, sentiment_tag: str) -> str:
        """Translate the sentiment tag to a more human-readable format"""
        sentiment_mapping = {
            "positive": "正面",
            "negative": "負面",
            "neutral": "中立",
        }
        return sentiment_mapping.get(sentiment_tag, sentiment_tag)

    def generate_analysis_response(self, query: str, analysis_results: Dict) -> str:
        """Generate a comprehensive response based on the news analysis results"""
        # Convert analysis results to a format suitable for the prompt
        results_summary = []

        for data in analysis_results.values():
            df = pd.DataFrame(data["ner"])
            markdown_ner = df.to_markdown(index=False)
            results_summary.append(
                f"""
## {data['title']}     
###### Published: {data['publish_date']}    
###### 內文:       
{data['content']}      
###### 摘要:      
{data['summary']}   
###### 情感: {self.translate_sentiment_tag(data['sentiment'])}      
###### NER:      
{markdown_ner}      
                """
            )

        formatted_results = "\n".join(results_summary)

        response = f"""
        Based on the query: {query}, here are the analysis results:
        
        {formatted_results}
        """
        return response.strip()
