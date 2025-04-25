import os
import time
import uuid
from src.utils.redis_handler import RedisHandler
import redis
from typing import Dict, List

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from src.agents.rag_agent import SelfRAGWorkflow
from src.agents.supervisor_agent import SupervisorAgent
from src.utils.log_handler import setup_logger
from google.genai import Client, types
from google.genai.types import GenerateContentConfig


# Initialize logger
logger = setup_logger(__name__)

# audio_worker = AudioToText()
autio_client = Client(api_key=os.getenv("GOOGLE_API_KEY", ""))


def audio_to_text(audio_file_object):
    response = autio_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "請將語音轉換為文字。",
            types.Part.from_bytes(
                data=audio_file_object,
                mime_type="audio/wav",
            ),
        ],
        config=GenerateContentConfig(temperature=0.1),
    )
    return response.text


# redis
@st.cache_resource
def get_redis_scenarios_connection():
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=0,
            decode_responses=True,  # Automatically decode response bytes to strings
        )
        return r
    except Exception as e:
        st.error(f"Failed to connect to Redis: {e}")
        return None


@st.cache_resource
def get_redis_vector_search_connection():
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=1,
            decode_responses=True,  # Automatically decode response bytes to strings
        )
        return r
    except Exception as e:
        st.error(f"Failed to connect to Redis: {e}")
        return None


@st.cache_resource
def get_redis_superviser_connection():
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=2,
            decode_responses=True,  # Automatically decode response bytes to strings
        )
        return r
    except Exception as e:
        st.error(f"Failed to connect to Redis: {e}")
        return None


redis_scenario_handler = RedisHandler(get_redis_scenarios_connection())
redis_vector_search_handler = RedisHandler(get_redis_vector_search_connection())
redis_supervisor_handler = RedisHandler(get_redis_superviser_connection())


def get_all_keys(r):
    if r:
        return r.keys("*")
    return []


def get_value(r, key):
    if r:
        return r.get(key)
    return None


api_key = os.getenv("GOOGLE_API_KEY", "")
# Configure API
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment variables")
    st.error(
        "🚨 GOOGLE_API_KEY not found in st.secrets! Please add it to your .env file."
    )
    st.stop()


def convert_to_langchain_messages(messages: List[Dict]) -> List[BaseMessage]:
    """Convert the session state messages to langchain message objects"""
    lc_messages = []
    for message in messages:
        if message["role"] == "user":
            lc_messages.append(HumanMessage(content=message["content"]))
        elif message["role"] == "assistant":
            lc_messages.append(AIMessage(content=message["content"]))
    return lc_messages


# --- Initialization & API Key Configuration ---
def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    if "initialized" not in st.session_state:
        logger.info("Initializing session state variables")
        st.session_state.initialized = True
        st.session_state.timer_duration_minutes = 5
        st.session_state.timer_running = False
        st.session_state.start_time = None
        st.session_state.duration_seconds = 0
        st.session_state.messages = []
        st.session_state.warning_sent = False
        st.session_state.time_up = False
        st.session_state.langchain_chat = None
        st.session_state.supervisor_agent = None
        st.session_state.chat_session_id = None
        st.session_state.scenarios_key = None
        st.session_state.supervisor_key = None
        st.session_state.vector_search_key = None
        st.session_state.last_audio = None
        st.session_state.last_text = None


initialize_session_state()


# --- Helper Functions ---
def format_time(seconds):
    if seconds < 0:
        seconds = 0
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def reset_app():
    logger.info("Resetting application state")
    st.session_state.timer_running = False
    st.session_state.start_time = None
    st.session_state.duration_seconds = 0
    st.session_state.messages = []
    st.session_state.warning_sent = False
    st.session_state.time_up = False
    st.session_state.langchain_chat = None
    st.session_state.supervisor_agent = None
    st.session_state.chat_session_id = None
    st.session_state.scenarios_key = None
    st.session_state.supervisor_key = None
    st.session_state.vector_search_key = None
    st.session_state.last_audio = None
    st.session_state.last_text = None
    # Clear potential widget states explicitly if needed (optional)
    # if 'duration_input' in st.session_state: del st.session_state['duration_input']
    st.rerun()


def start_chat_session():
    if st.session_state.timer_duration_minutes > 0:
        logger.info(
            f"Starting new chat session with {st.session_state.timer_duration_minutes} minute duration"
        )
        st.session_state.timer_running = True
        st.session_state.time_up = False
        st.session_state.warning_sent = False
        st.session_state.duration_seconds = st.session_state.timer_duration_minutes * 60
        st.session_state.start_time = time.time()
        st.session_state.chat_session_id = str(uuid.uuid4())
        try:
            logger.info(
                f"Initializing SelfRAGWorkflow for session: {st.session_state.chat_session_id}"
            )

            if st.session_state.scenarios_key is None:
                st.error("Please select a scenario before starting the session.")
                st.stop()
                return

            if st.session_state.supervisor_key is None:
                st.error("Please select a supervisor key before starting the session.")
                st.stop()
                return

            scenarios_description = redis_scenario_handler.get_value(
                st.session_state.scenarios_key
            )

            supervisor_instructions = redis_supervisor_handler.get_value(
                st.session_state.supervisor_key
            )

            st.session_state.langchain_chat = SelfRAGWorkflow(
                session_id=st.session_state.chat_session_id,
                scenarios_description=scenarios_description,
            )

            st.session_state.supervisor_agent = SupervisorAgent(
                scenarios_description=scenarios_description,
                supervisor_instructions=supervisor_instructions,
            )

            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Timer started! You can begin chatting.",
                }
            ]
            st.rerun()
        except Exception as e:
            logger.error(
                f"Failed to initialize Langchain chat model: {str(e)}", exc_info=True
            )
            st.error(f"Failed to initialize Langchain chat model: {e}")
            st.session_state.timer_running = False
    else:
        logger.warning("User attempted to start session with duration <= 0 minutes")
        st.error("Please set a duration greater than 0 minutes.")


# async
# TODO: it will cause error message for: Event loop is closed
# async def call_agent(initial_state, agents):
#     """Call the agent with the initial state"""
#     state = await agents.workflow.ainvoke(initial_state)
#     return state


# async def ainvoke(initial_state, agents):
#     # Create a task so it runs in the background
#     agent_task = asyncio.create_task(
#         call_agent(initial_state=initial_state, agents=agents)
#     )

#     # This will run immediately, not waiting for the task to complete
#     print("print something while the workflow is running")

#     # Now wait for the task to complete and get its result
#     result = await agent_task

#     if result:
#         print("Async workflow execution finished")
#         print(f"Result: {result}")

#     return result


# --- App Logic ---

st.title("智能陪練機器人")

# --- UI Placeholders ---
# ADD a placeholder specifically for the configuration section
config_placeholder = st.empty()
# Keep other placeholders
timer_display_placeholder = st.empty()
progress_bar_placeholder = st.empty()
chat_placeholder = st.container()
final_message_placeholder = st.empty()

# --- Configuration Phase (uses the new placeholder) ---
if not st.session_state.timer_running and not st.session_state.time_up:
    # Draw the configuration UI INSIDE the placeholder's container
    with config_placeholder.container():
        st.write("Set the chat duration and start the session.")

        # Use session state value safely, provide default
        current_duration = st.session_state.get("timer_duration_minutes", 5)

        # Add a unique key to the number input
        new_duration = st.number_input(
            "Set timer duration (minutes):",
            min_value=1,
            value=current_duration,
            step=1,
            key="config_duration_input",  # Unique key
        )
        # Important: Update session state if the value changes
        if new_duration != current_duration:
            logger.info(
                f"Chat duration changed from {current_duration} to {new_duration} minutes"
            )
            st.session_state.timer_duration_minutes = new_duration
            st.rerun()  # Rerun if duration changes to reflect it immediately

        # Add a unique key to the button
        if st.button("Start Chat Session", key="config_start_button"):
            # Update the duration one last time before starting, just in case
            st.session_state.timer_duration_minutes = (
                st.session_state.config_duration_input
            )
            start_chat_session()
else:
    # If the timer IS running or IS up, explicitly clear the config placeholder
    config_placeholder.empty()


# --- Running Phase (Timer Active) ---
if st.session_state.timer_running:
    # (Your existing timer logic, warning logic, time up check, and chat interface)
    # ... (make sure this section is correctly indented) ...
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = st.session_state.duration_seconds - elapsed_time
    progress = min(1.0, elapsed_time / st.session_state.duration_seconds)

    timer_display_placeholder.metric("Time Remaining", format_time(remaining_time))
    progress_bar_placeholder.progress(progress)

    quarter_time_threshold = st.session_state.duration_seconds * 0.25
    if remaining_time <= quarter_time_threshold and not st.session_state.warning_sent:
        warning_minutes = round(quarter_time_threshold / 60, 1)
        logger.info(f"Time warning: less than {warning_minutes} minutes remaining")
        st.warning(f"⏳ Time remaining is less than {warning_minutes} minutes!")
        st.session_state.warning_sent = True

    if remaining_time <= 0:
        logger.info("Time's up for chat session")
        st.session_state.timer_running = False
        st.session_state.time_up = True
        timer_display_placeholder.metric("Time Remaining", "00:00")
        progress_bar_placeholder.progress(1.0)
        final_message_placeholder.success("⏰ Time's up! Chat session ended.")

    # Only show the chat interface if the time isn't up
    with chat_placeholder:
        if not st.session_state.time_up:  # Add this condition
            st.write("##### 對話中")
            # Display the last message in the chat
            try:
                last_two_messages = st.session_state.messages[-2]
                with st.chat_message(last_two_messages["role"]):
                    st.markdown(last_two_messages["content"])
            except IndexError:
                # If there are not enough messages, just skip this part
                pass
            try:
                button_mnessage = st.session_state.messages[-1]
                with st.chat_message(button_mnessage["role"]):
                    st.markdown(button_mnessage["content"])
            except IndexError:
                pass

            if st.session_state.timer_running and st.session_state.langchain_chat:
                if audio_prompt := st.audio_input("Audio Input"):
                    if audio_prompt.getvalue() != st.session_state.last_audio:
                        prompt = audio_to_text(audio_prompt.getvalue())
                        if prompt != st.session_state.last_text:
                            st.session_state.last_text = prompt
                            st.session_state.messages.append(
                                {"role": "user", "content": prompt}
                            )
                            lc_messages = convert_to_langchain_messages(
                                st.session_state.messages
                            )
                            try:
                                logger.debug("Invoking LangChain workflow")

                                initial_state = {
                                    "messages": lc_messages,
                                    "max_generation": 2,
                                    "docs": [],
                                    "is_retrieval_related": False,
                                    "validated_docs": [],
                                    "response": "",
                                    "response_validated": None,
                                    "max_generation": 2,
                                    "query_rewritten": False,
                                    "rewritten_query": "",
                                }

                                response = (
                                    st.session_state.langchain_chat.workflow.invoke(
                                        initial_state
                                    )
                                )
                                assistant_response = response["messages"][-1].content
                            except Exception as e:
                                logger.error(
                                    f"Error generating response: {str(e)}",
                                    exc_info=True,
                                )
                                st.error(
                                    f"An error occurred while processing your request: {e}"
                                )
                                assistant_response = f"Sorry, I couldn't generate a response due to {str(e)}"
                            st.session_state.messages.append(
                                {"role": "assistant", "content": assistant_response}
                            )
                            st.session_state.last_audio = audio_prompt.getvalue()
                            st.rerun()

    # Sidebar content - always show certain elements
    with st.sidebar:

        # Show reset task section when timer is running
        st.header("機器人簡述")
        st.info(
            """
這個機器人專門根據情境以及對應的文檔做查詢以及回覆，請您和它對話。    
對話結束後它會給予您一些回饋，幫助您成長。
            """
        )

        st.header("機器人功能")
        st.markdown(
            """
            ✉️ 建立情境     
            🔍 向量查詢與問題改寫     
            ☑️ 相關性驗證     
            ✒️ 對話內容評估   
            """
        )
        st.header("重置任務")
        st.info("按下重置按鈕將會清除所有對話紀錄，並重新開始新的對話。")
        if st.button("重置任務按鈕", type="primary"):
            logger.info("User clicked Reset Session button")
            reset_app()

        if st.session_state.timer_running:
            time.sleep(1)
            st.rerun()

else:
    # Only show this sidebar content when timer is not running
    with st.sidebar:
        st.header("機器人簡述")
        st.info(
            """
這個機器人專門根據情境以及對應的文檔做查詢以及回覆，請您和它對話。    
對話結束後它會給予您一些回饋，幫助您成長。
            """
        )

        st.header("機器人功能")
        st.markdown(
            """
            ✉️ 建立情境     
            🔍 向量查詢與問題改寫     
            ☑️ 相關性驗證     
            ✒️ 對話內容評估   
            """
        )

        st.session_state.scenarios_key = st.selectbox(
            "情境選擇",
            options=redis_scenario_handler.get_all_keys(),
            index=0,
        )

        st.session_state.supervisor_key = st.selectbox(
            "回饋選擇",
            options=redis_supervisor_handler.get_all_keys(),
            index=0,
        )

        st.session_state.vector_search_key = st.selectbox(
            "知識庫選擇",
            options=redis_vector_search_handler.get_all_keys(),
            index=0,
        )
        RedisHandler.set_current_key(st.session_state.vector_search_key)


# --- Time's Up Phase ---
if st.session_state.time_up:
    # Clear the running phase chat interface by emptying the chat_placeholder first
    chat_placeholder.empty()

    final_message_placeholder.success("⏰ Time's up! Chat session ended.")

    if st.session_state.supervisor_agent:
        supervisor_initial_state = {
            "chat_history": convert_to_langchain_messages(st.session_state.messages),
            "feedback": "",
        }
        supervisor_response = st.session_state.supervisor_agent.workflow.invoke(
            supervisor_initial_state
        )
        feedback = supervisor_response["feedback"]
        st.text_area("對話回饋", value=feedback.strip(), height=600, disabled=True)

    expandar = st.expander("對話歷史紀錄", expanded=False)
    with expandar:
        display_messages = [
            m
            for m in st.session_state.messages
            if m["content"] != "Timer started! You can begin chatting."
        ]
        if not display_messages:
            st.info("No chat messages were exchanged during the session.")
        else:
            for message in display_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    st.info("Click Reset to start a new session.")
    if st.button("重置按鈕", type="primary"):
        logger.info("User clicked Reset Session button")
        reset_app()
