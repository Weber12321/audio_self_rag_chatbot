import os
import streamlit as st
import time
from google import genai
from google.genai import types
import google.generativeai as generateai

api_key = os.getenv("GOOGLE_API_KEY", "")
# Configure Gemini API
if not api_key:
    st.error(
        "🚨 GOOGLE_API_KEY not found in st.secrets! Please add it to your .env file."
    )
    st.stop()

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"

autio_client = genai.Client(api_key=api_key)


# --- Initialization & API Key Configuration ---
# (Keep your existing initialization and API key config)
def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.timer_duration_minutes = 5
        st.session_state.timer_running = False
        st.session_state.start_time = None
        st.session_state.duration_seconds = 0
        st.session_state.messages = []
        st.session_state.warning_sent = False
        st.session_state.time_up = False
        st.session_state.gemini_chat = None
        st.session_state.last_audio = None


initialize_session_state()


# --- Helper Functions ---
# (Keep your existing format_time, reset_app, start_chat_session functions)
def format_time(seconds):
    if seconds < 0:
        seconds = 0
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def reset_app():
    st.session_state.timer_running = False
    st.session_state.start_time = None
    st.session_state.duration_seconds = 0
    st.session_state.messages = []
    st.session_state.warning_sent = False
    st.session_state.time_up = False
    st.session_state.gemini_chat = None
    st.session_state.last_audio = None
    # Clear potential widget states explicitly if needed (optional)
    # if 'duration_input' in st.session_state: del st.session_state['duration_input']
    st.rerun()


def audio_to_text(audio_file_object):
    response = autio_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "Generate a transcript of the speech.",
            types.Part.from_bytes(
                data=audio_file_object,
                mime_type="audio/wav",
            ),
        ],
    )
    return response.text


def start_chat_session():
    if st.session_state.timer_duration_minutes > 0:
        st.session_state.timer_running = True
        st.session_state.time_up = False
        st.session_state.warning_sent = False
        st.session_state.duration_seconds = st.session_state.timer_duration_minutes * 60
        st.session_state.start_time = time.time()
        try:
            model = generateai.GenerativeModel(GEMINI_MODEL)
            st.session_state.gemini_chat = model.start_chat(history=[])
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Timer started! You can begin chatting.",
                }
            ]
            st.rerun()
        except Exception as e:
            st.error(f"Failed to initialize Gemini chat model: {e}")
            st.session_state.timer_running = False
    else:
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
        st.warning(f"⏳ Time remaining is less than {warning_minutes} minutes!")
        st.session_state.warning_sent = True

    if remaining_time <= 0:
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

        if st.session_state.timer_running and st.session_state.gemini_chat:
            # if prompt := st.chat_input("Ask Gemini...", key="chat_input_main"):
            if audio_prompt := st.audio_input("Audio Input"):
                if audio_prompt.getvalue() != st.session_state.last_audio:
                    prompt = audio_to_text(audio_prompt.getvalue())
                    st.session_state.messages.append(
                        {"role": "user", "content": prompt}
                    )
                    try:
                        response = st.session_state.gemini_chat.send_message(prompt)
                        assistant_response = response.text
                    except Exception as e:
                        st.error(f"An error occurred while contacting Gemini: {e}")
                        assistant_response = (
                            "Sorry, I couldn't get a response from the AI."
                        )
                    st.session_state.messages.append(
                        {"role": "assistant", "content": assistant_response}
                    )
                    st.session_state.last_audio = audio_prompt.getvalue()
                    st.rerun()
                else:
                    pass

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
        reset_app()
