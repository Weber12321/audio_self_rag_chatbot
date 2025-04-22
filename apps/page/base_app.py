import os
import streamlit as st
import google.generativeai as genai
import asyncio


api_key = os.getenv("GOOGLE_API_KEY", "")
# Configure Gemini API
if not api_key:
    st.error(
        "🚨 GOOGLE_API_KEY not found in st.secrets! Please add it to your .env file."
    )
    st.stop()

# Configure Gemini API
genai.configure(api_key=api_key)

# === page config ===
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = ""

if "time_up" not in st.session_state:
    st.session_state.time_up = False

if "messages" not in st.session_state:
    st.session_state.messages = []


async def countdown_timer(chat_total_time):
    """
    Display a countdown timer with a progress bar asynchronously

    Parameters:
    - chat_total_time: Time in minutes for the countdown
    """
    # Create a progress bar
    progress_bar = st.progress(0)

    # Create a container for the timer text
    timer_text = st.empty()

    # Convert minutes to seconds
    total_seconds = chat_total_time * 60

    # Calculate steps for smooth countdown
    steps = 100
    step_time = total_seconds / steps

    # Countdown loop
    for i in range(steps, 0, -1):
        # Update progress bar
        if st.session_state.time_up:
            break
        progress_bar.progress((steps - i) / steps)

        # Display remaining time in minutes and seconds format
        remaining_seconds = i * step_time
        mins = int(remaining_seconds // 60)
        secs = int(remaining_seconds % 60)
        timer_text.text(f"倒數計時: {mins}分{secs}秒")

        # Use asyncio.sleep instead of time.sleep
        await asyncio.sleep(step_time)

    # Complete the progress bar
    progress_bar.empty()
    timer_text.text("時間到！")

    # Return or set a flag to indicate timer completion
    st.session_state.time_up = True
    return None


# Helper function to run async function in a new thread
def run_async_timer(total_time):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(countdown_timer(total_time))
    finally:
        loop.close()


st.title("文件對話機器人")

# === file upload ===
upload_files = st.file_uploader(
    "請上傳文件內容", type=["pdf"], accept_multiple_files=True
)

if upload_files:
    for uploaded_file in upload_files:
        # Display file name
        st.write(f"處理文件: {uploaded_file.name}")

        # # Read PDF content
        # pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))

        # # Extract text from each page
        # text_content = ""
        # for page_num in range(len(pdf_reader.pages)):
        #     page = pdf_reader.pages[page_num]
        #     text_content += page.extract_text()

        # st.session_state.pdf_content += text_content

        # # Show a sample of the extracted content
        # st.write("已提取文件內容：")
        # st.write(text_content[:300] + "..." if len(text_content) > 300 else text_content)

# === timer ===
chat_total_time = st.number_input(
    "請輸入計時器（分鐘）", min_value=1, max_value=30, value=5, step=1
)

# === chat ===
start_chat = st.button("開始對話")
if start_chat:
    # Call the async countdown timer function using threading
    import threading

    timer_thread = threading.Thread(target=run_async_timer, args=(chat_total_time,))
    timer_thread.daemon = True
    timer_thread.start()

    # Chat Stage
    st.subheader("與文件對話")

    with st.sidebar:
        stop_chat = st.button("停止對話")
        if stop_chat:
            st.session_state.time_up = True
            st.session_state.messages = []
            st.success("對話已停止。")

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Function to generate response using Gemini
    def generate_gemini_response(conversation):
        try:
            # Configure the model
            model = genai.GenerativeModel("gemini-2.0-flash")

            # Create context with PDF content
            # context = (
            #     f"以下是文件內容，請基於這些內容回答用戶的問題：\n\n{pdf_content}\n\n"
            # )

            # Generate response
            response = model.generate_content(conversation)
            return response.text
        except Exception as e:
            return f"生成回應時發生錯誤: {str(e)}"

    # Accept user input
    if not st.session_state.time_up:
        if prompt := st.chat_input("輸入您的問題"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    # Create conversation history for context
                    conversation_history = ""
                    for msg in st.session_state.messages[
                        -5:
                    ]:  # Use last 5 messages for context
                        role = "用戶" if msg["role"] == "user" else "助手"
                        conversation_history += f"{role}: {msg['content']}\n"

                    response = generate_gemini_response(conversation_history)
                    st.markdown(response)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.info("對話時間已結束，請點擊'開始對話'重新開始。")
