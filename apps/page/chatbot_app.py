import os
from typing import Dict, List
import streamlit as st
import time
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.rag_agent import SelfRAGWorkflow
from src.utils.log_handler import setup_logger

# Initialize logger
logger = setup_logger(__name__)

api_key = os.getenv("GOOGLE_API_KEY", "")
# Configure API
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment variables")
    st.error(
        "🚨 GOOGLE_API_KEY not found in st.secrets! Please add it to your .env file."
    )
    st.stop()


def convert_to_langchain_messages(messages: List[Dict]) -> List:
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
        st.session_state.chat_session_id = None


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
    st.session_state.chat_session_id = None
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
        st.session_state.chat_session_id = (
            "test_session_id"  # Placeholder for session ID
        )
        try:
            # Create LLM using the backend function
            # llm = create_google_model()

            # Create a chat prompt template with system message
            # prompt = ChatPromptTemplate.from_messages(
            #     [
            #         SystemMessage(
            #             content="You are a helpful AI assistant. Answer the user's questions concisely and accurately."
            #         ),
            #         MessagesPlaceholder(variable_name="history"),
            #         MessagesPlaceholder(variable_name="input"),
            #     ]
            # )

            # # Set up memory for conversation history
            # memory = ConversationBufferMemory(
            #     return_messages=True, memory_key="history"
            # )

            # # Create the conversation chain
            # st.session_state.langchain_chat = ConversationChain(
            #     llm=llm, memory=memory, prompt=prompt, verbose=True
            # )
            logger.info(
                f"Initializing SelfRAGWorkflow for session: {st.session_state.chat_session_id}"
            )
            st.session_state.langchain_chat = SelfRAGWorkflow(
                session_id=st.session_state.chat_session_id,
                scenarios_description="""
文件目的與適用範圍

目的： [9] 本手冊旨在規範船隊電腦（含 IT 及 OT 算貨電腦）發生病毒或惡意程式威脅事件時的標準處理流程，由機房同仁（依時段可能是系統管理部系統服務課 SSV 或 UHD）通知相關人員（船長、SSV 船隊防毒軟體管理人員、海技部），進行檢查與處理，以阻止惡意軟體攻擊及擴散，確保船隊資訊安全。
適用對象： [9] 船上同仁使用的所有船隊 IT 電腦及 OT 算貨電腦。
名詞定義

長榮資安整合平台 (ESIS)： [9] 優先部署於新造船及衛星網路不限流量船隻，用於統一部署、管理、監控船隊資安政策，彙整管控資訊，並記錄資安事件處理歷程的系統。
船隊 IT 電腦： [9] 指用於資料處理的資訊技術系統，如船長通信電腦、辦公室公務電腦等。手冊列有具體的電腦代碼 (如 BRG1, DECK1, LOADING, ECR1, MS 等)。 [11], [12]
船隊 OT 電腦： [11] 指用於直接監控和控制物理設備的操作技術系統，如 ICMS、機艙監控電腦、冷凍櫃監控系統等。
事件處理觸發時機

時機 1： [13] 接獲船上同仁通報電腦出現病毒攔截告警或惡意程式威脅。
時機 2： [15] UHD 監控信箱收到主旨開頭為 "[Ship Virus Alert]" 的警示郵件。此類郵件主旨會標示船名和電腦名稱，內文包含檔案路徑 (File Path)、事件時間 (Event time)、使用者 (User) 及電腦名稱 (Computer)。
核心處理步驟

判斷處理時段： [17]

上班時間：由系統管理部系統服務課 (SSV) 船隊防毒軟體管理負責人處理。
下班時間：由 UHD 依後續步驟寄送通知信。
判斷通知對象： [19]

先從 Alert 信件主旨取得船名，利用通訊錄 (需有 Inmarsat AB 通訊錄) 找到船長 Master 信箱。 [19]
EVER / UNI 開頭船隻： [19], [21]
收件人 (To)：船長、海技部方銘彬專工。
副本 (CC)：吳欣芝、資安管理專用信箱、資訊安全部信箱、人事部主管、海技一課課信箱、系統管理部經理、SSV 課信箱及多位 SSV 課內人員。
ITAL 開頭及 EVER COZY 船隻： [21]
收件人 (To)：船長、ITS 海技部李維修船長。
副本 (CC)[已移除電子郵件地址]、系統管理部經理、SSV 課信箱及多位 SSV 課內人員。
判斷是否已建置 ESIS 平台： [24]

檢查指定路徑下的 資安管理主機建置進度.xlsx 檔案 (J 欄位 ● 表示已建置，N/A 表示未建置)。 [24]
若已建置 ESIS： [24], [26], [27], [29]
依步驟 2 寄送通知信。
信件主旨格式：Virus detected with【船名】。
信件內容需提醒船長登入 ESIS 網站 (提供連結) 獲取詳細資訊、追查病毒來源、執行全機掃描並在 ESIS 網站回報。
務必附上附件 Notification of launching 'Evergreen Security Integrated System(ESIS).pdf。
未建置 ESIS 平台 - 判斷病毒來源： [32], [33]

根據 Alert 信件中的 [File path] 判斷：
USB 來源： 路徑非 C:\ 或 D:\ 開頭。
公檔來源： 路徑為 D:\share\ 開頭。
其他來源： 路徑為 C:\ 或 D:\ 開頭，但非 D:\share\。
未建置 ESIS 平台 - 寄送對應通知信： [34]

從 Alert 信件取得 [FilePath], Event Time, [User], [Computer] 填入對應範本。
範本 1 (USB 來源)： [34], [37], [38], [39]
主旨：Virus detected with【船名】。
內容：告知中毒電腦、時間、使用者、路徑，並指明是 USB 裝置。要求立即拔除 USB，對該電腦全機掃毒。中毒 USB 未格式化前不得再接入 IT 電腦。若其他電腦用過此 USB，也需更新病毒碼並全機掃毒。最後要求回報掃毒結果並追查來源。
範本 2 (公檔來源)： [47], [50], [51], [52], [53], [54]
主旨：Virus detected with【船名】。
內容：告知中毒電腦、時間、使用者、路徑，並指明是 share 共用磁碟槽。要求立即對該電腦全機掃毒。因病毒可能從其他電腦感染至公檔，需確認無私人電腦連接 IT 網路，並要求全船所有電腦更新病毒碼、全機掃毒，回報結果並追查來源。
範本 3 (其他來源)： [Image 6], [71], [72]
主旨：Virus detected with【船名】。
內容：告知中毒電腦、時間、使用者、路徑。要求立即對該電腦全機掃毒，回報結果並追查來源。
處理船長回報： [73]

所有船長的回報結果及後續追蹤，皆由 SSV 船隊防毒軟體管理值班人員接手處理。
若 UHD 信箱收到船長的回報，需將信件轉寄給 SSV 值班人員，並 CC 給步驟 2 中的所有收/副本人員。
通知 SSV 值班人員的時機 (UHD 操作)： [75], [77]

若 UHD 監控信箱持續收到 2 次或以上來自同一艘船、相同 File Path、相同 Computer Name 的病毒攔截信件。 [75]
接獲船長要求請公司電算同仁協助處理資安事件時。 [75]
通知時，需查詢指定路徑下的 船隊中毒事件處理輪值表，依輪值順序聯絡 SSV 值班人員。 [77]
總結：
這份手冊提供了一套結構化的流程來應對船隊電腦病毒事件。關鍵在於區分處理時段、判斷船隻類型與 ESIS 建置狀況、識別病毒來源（特別是對於未建置 ESIS 的船隻），並根據不同情況採取相應的通知和處置措施，最後確保事件得到追蹤與適當的升級處理。
""",
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


# --- App Logic ---

st.title("限時對話機器人")

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

    with chat_placeholder:
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
            if prompt := st.chat_input("Ask a question...", key="chat_input_main"):
                logger.info(
                    f"User sent message: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
                )
                st.session_state.messages.append({"role": "user", "content": prompt})
                try:
                    # Use Langchain for chat response
                    logger.debug("Invoking LangChain workflow")
                    response = st.session_state.langchain_chat.workflow.invoke(
                        {"query": prompt}
                    )
                    assistant_response = response
                    logger.info(
                        f"Generated response: {assistant_response[:50]}{'...' if len(assistant_response) > 50 else ''}"
                    )
                except Exception as e:
                    logger.error(f"Error generating response: {str(e)}", exc_info=True)
                    st.error(f"An error occurred while processing your request: {e}")
                    assistant_response = (
                        f"Sorry, I couldn't generate a response due to {str(e)}"
                    )
                st.session_state.messages.append(
                    {"role": "assistant", "content": assistant_response}
                )
                st.rerun()

    if st.session_state.timer_running:
        time.sleep(1)
        st.rerun()


# --- Time's Up Phase ---
if st.session_state.time_up:
    # (Your existing time's up logic)
    # ... (make sure this section is correctly indented) ...
    final_message_placeholder.success("⏰ Time's up! Chat session ended.")
    with chat_placeholder:
        st.write("##### 對話歷史紀錄")
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

# --- Reset Button ---
# Make sure this is OUTSIDE the main timer running/time up blocks if you want it always visible after start
if st.session_state.start_time is not None or st.session_state.time_up:
    # Add a key to the reset button
    if st.button("Reset Session", key="config_reset_button"):
        logger.info("User clicked Reset Session button")
        reset_app()
