import streamlit as st
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "app.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("frontend")

pages = {
    "首頁": [
        st.Page(
            "page/index.py",
            title="首頁",
            icon="🏠",
        ),
    ],
    "聊天室": [
        st.Page(
            "page/chatbot_app.py",
            title="倒數計時文字聊天室",
            icon="🤖",
        ),
    ],
    "機器人服務": [
        st.Page(
            "page/rag_app.py",
            title="PDF RAG 系統",
            icon="📊",
        ),
        st.Page(
            "page/scenario_app.py",
            title="情境管理系統",
            icon="📊",
        ),
        st.Page(
            "page/supervisor_app.py",
            title="回饋管理系統",
            icon="📊",
        ),
    ],
}


pg = st.navigation(pages)
pg.run()
