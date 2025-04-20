import streamlit as st
import time


# --- Initialization ---
def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.timer_duration_minutes = 5  # Default duration
        st.session_state.timer_running = False
        st.session_state.start_time = None
        st.session_state.duration_seconds = 0
        st.session_state.messages = []
        st.session_state.warning_sent = False
        st.session_state.time_up = False


initialize_session_state()


# --- Helper Functions ---
def format_time(seconds):
    """Formats seconds into MM:SS string."""
    if seconds < 0:
        seconds = 0
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def reset_app():
    """Resets the application state."""
    st.session_state.timer_running = False
    st.session_state.start_time = None
    st.session_state.duration_seconds = 0
    st.session_state.messages = []
    st.session_state.warning_sent = False
    st.session_state.time_up = False
    # Keep the chosen duration or reset it? Let's keep it for convenience.
    # st.session_state.timer_duration_minutes = 5 # Optional: reset duration too
    st.rerun()  # Rerun to reflect the cleared state immediately


# --- UI Placeholders ---
# Use placeholders to update elements in place
timer_display_placeholder = st.empty()
progress_bar_placeholder = st.empty()
chat_placeholder = st.container()  # Container for chat messages
final_message_placeholder = st.empty()

# --- App Logic ---

st.title("Timed Chat Bot")

# --- Configuration Phase (Before Timer Starts) ---
if not st.session_state.timer_running and not st.session_state.time_up:
    st.write("Set the chat duration and start the session.")

    # Allow user to set timer duration
    st.session_state.timer_duration_minutes = st.number_input(
        "Set timer duration (minutes):",
        min_value=1,
        value=st.session_state.timer_duration_minutes,
        step=1,
    )

    # Start Chat Button
    if st.button("Start Chat Session"):
        if st.session_state.timer_duration_minutes > 0:
            st.session_state.timer_running = True
            st.session_state.time_up = False
            st.session_state.warning_sent = False
            st.session_state.duration_seconds = (
                st.session_state.timer_duration_minutes * 60
            )
            st.session_state.start_time = time.time()
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Timer started! You can begin chatting.",
                }
            ]
            st.rerun()  # Rerun immediately to start the timer display
        else:
            st.error("Please set a duration greater than 0 minutes.")

# --- Running Phase (Timer Active) ---
if st.session_state.timer_running:
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = st.session_state.duration_seconds - elapsed_time
    progress = min(
        1.0, elapsed_time / st.session_state.duration_seconds
    )  # Ensure progress doesn't exceed 1.0

    # Update Timer Display and Progress Bar
    timer_display_placeholder.metric("Time Remaining", format_time(remaining_time))
    progress_bar_placeholder.progress(progress)

    # Check for Quarter Time Warning
    quarter_time_threshold = st.session_state.duration_seconds * 0.25
    if remaining_time <= quarter_time_threshold and not st.session_state.warning_sent:
        warning_minutes = round(quarter_time_threshold / 60, 1)
        st.warning(f"Time remaining is less than {warning_minutes} minutes!")
        st.session_state.warning_sent = True  # Ensure warning is sent only once

    # Check if Time is Up
    if remaining_time <= 0:
        st.session_state.timer_running = False
        st.session_state.time_up = True
        timer_display_placeholder.metric("Time Remaining", "00:00")
        progress_bar_placeholder.progress(1.0)
        final_message_placeholder.success("Time's up! Chat session ended.")
        # No need to rerun here, the next block handles the 'time_up' state

    # --- Chat Interface ---
    with chat_placeholder:
        st.write("--- Chat History ---")
        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input - only allow input if the timer is still running
        if prompt := st.chat_input("What is up?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Add assistant response (simple echo for demo)
            assistant_response = f"Echo: {prompt}"
            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_response}
            )
            with st.chat_message("assistant"):
                st.markdown(assistant_response)

            # Rerun to display the new message immediately
            st.rerun()

    # --- Force Periodic Rerun for Timer Update ---
    # If the timer is still running after processing chat input,
    # wait a second and rerun to update the timer display.
    if st.session_state.timer_running:
        time.sleep(1)
        st.rerun()

# --- Time's Up Phase ---
if st.session_state.time_up:
    final_message_placeholder.success("Time's up! Chat session ended.")

    # Display final chat history clearly
    with chat_placeholder:  # Reuse the chat placeholder area
        st.write("--- Final Chat History ---")
        if st.session_state.messages:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        else:
            st.info("No messages were exchanged during the session.")

    st.info("Click Reset to start a new session.")


# --- Reset Button (Always Visible After First Start or Time Up) ---
if st.session_state.start_time is not None or st.session_state.time_up:
    if st.button("Reset Session"):
        reset_app()

# --- Sidebar or Footer for Reset (Alternative Placement) ---
# with st.sidebar:
#    st.header("Controls")
#    if st.button("Reset Session"):
#         reset_app()
