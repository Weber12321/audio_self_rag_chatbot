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
logger.info("Starting application")

pages = {
    "聊天室": [
        # st.Page(
        #     "develop/timer_app.py",
        #     title="倒數計時語音聊天室",
        #     icon="🤖",
        # ),
        st.Page(
            "chatbot_app.py",
            title="倒數計時文字聊天室",
            icon="🤖",
        ),
    ],
    "機器人服務": [
        st.Page(
            "rag_app.py",
            title="PDF RAG 系統",
            icon="📊",
        ),
    ],
}


pg = st.navigation(pages)
pg.run()
