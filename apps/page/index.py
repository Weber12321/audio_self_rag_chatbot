import os
import streamlit as st
import importlib.util
import sys


# Set page config
st.set_page_config(
    page_title="Viki Audio Chatbot Tools Guide",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

base_url = os.getenv("STREAMLIT_BASE_URL", "")


# Function to load and run another Streamlit script
def load_streamlit_script(script_path):
    """Load and execute a Streamlit script from the given path."""
    spec = importlib.util.spec_from_file_location("st_script", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["st_script"] = module
    spec.loader.exec_module(module)


# Function to create header with gradient background
def add_gradient_header(title, subtitle=""):
    header_html = f"""
    <div style="
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    ">
        <h1 style="color: white;">{title}</h1>
        <p style="color: #eee; font-size: 1.2em;">{subtitle}</p>
    </div>
    """
    st.html(header_html)


# Function to create step cards with icons
def create_step_card(
    step_num, title, description, icon, button_text=None, button_url=None
):
    card_html = f"""
    <div style="
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background-color: #f9f9f9;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="
                background-color: #4b6cb7;
                color: white;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                margin-right: 15px;
            ">{step_num}</div>
            <h3 style="margin: 0;">{title}</h3>
            <div style="margin-left: auto; font-size: 24px;">{icon}</div>
        </div>
        <p style="color: black;">{description}</p>
        {f'<a href="{button_url}" target="_self" style="display: inline-block; background-color: #4b6cb7; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; margin-top: 10px;">{button_text}</a>' if button_text else ''}
    </div>
    """
    st.html(card_html)


# Function to render image preview
def render_app_preview(title, description, image_path=None):
    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader(title)
        st.write(description)
    with col2:
        if image_path and os.path.exists(image_path):
            st.image(image_path, use_column_width=True)
        else:
            st.info("Preview image not available")


# Function to create workflow diagram
def render_workflow_diagram():
    # Using direct st.graphviz_chart call instead of exec()
    st.graphviz_chart(
        """
    digraph {
        rankdir=LR;
        node [shape=box, style=filled, fillcolor="#f5f5f5", fontname="Arial"];
        edge [color="#333333"];
        
        upload [label="1. Upload PDF\\nrag_app.py", fillcolor="#e1f5fe"];
        scenario [label="2. Create Scenarios\\nscenario_app.py", fillcolor="#e8f5e9"];
        supervisor [label="3. Create Supervisor\\nsupervisor_app.py", fillcolor="#e8f5e9"];
        chat [label="4. Start Chat Session\\nchatbot_app.py", fillcolor="#fff8e1"];
        
        upload -> scenario [label="Vector Store"];
        scenario -> supervisor [label="Scenario Data"];
        supervisor -> chat [label="Supervisor Data"];
    }
    """
    )


# Main content
def main():
    add_gradient_header(
        "Viki Audio Chatbot Tools Guide",
        "Follow these steps to set up and use the conversational AI system",
    )

    st.markdown(
        """
    This guide will help you understand how to use the Viki Audio Chatbot effectively. 
    The system consists of three main components that need to be used in sequence:
    """
    )

    # Workflow diagram
    st.subheader("Workflow Overview")
    render_workflow_diagram()

    # Step 1
    create_step_card(
        1,
        "Upload PDF Documents",
        """
        First, you need to upload PDF documents to create a vector store. This will allow the AI to search
        and retrieve information from your documents during conversations.
        
        **What happens in this step:**
        - Upload one or more PDF documents
        - The system processes the text and creates vector embeddings
        - These embeddings are stored in Redis and can be reused later
        """,
        "📄",
        "Go to PDF Upload Tool",
        button_url=base_url + "rag_app",
    )

    # Step 2
    create_step_card(
        2,
        "Create Scenarios",
        """
        Next, create scenarios that describe the context and purpose of conversations.
        The AI will use these scenarios to frame its responses appropriately.
        
        **What happens in this step:**
        - Define a scenario with a description
        - Set any specific constraints or guidance for the AI
        - Save the scenario for use in chat sessions
        """,
        "🎭",
        "Go to Scenario Creator",
        button_url=base_url + "scenario_app",
    )

    # Step 3
    create_step_card(
        3,
        "Create Supervisor",
        """
        Then, create supervisor that evaluate the context and purpose of conversations.
        
        **What happens in this step:**
        - Define a supervisor with rules
        - Save the supervisor for use in chat sessions
        """,
        "🎭",
        "Go to Supervisor Creator",
        button_url=base_url + "supervisor_app",
    )

    # Step 4
    create_step_card(
        4,
        "Start a Chat Session",
        """
        Finally, start a chat session where you can interact with the AI. 
        The AI will use both the vector store and the scenario to provide informed responses.
        
        **What happens in this step:**
        - Select a previously created scenario
        - Choose which vector store to use
        - Set a time limit for the conversation
        - Chat with the AI and receive feedback after the session
        """,
        "💬",
        "Go to Chat Interface",
        button_url=base_url + "chatbot_app",
    )

    st.markdown("---")

    # Additional notes
    st.subheader("Important Notes")
    st.info(
        """
    - **Order matters**: You must complete steps 1,2 and 3 before attempting step 4
    - **Vector stores are persistent**: Once created, they remain available for future sessions
    - **Sessions are timed**: The chat interface includes a timer to limit conversation length
    - **Feedback is provided**: After a chat session ends, you'll receive feedback on the conversation
    """
    )

    # FAQ section
    with st.expander("Frequently Asked Questions"):
        st.markdown(
            """
        ### Why do I need to upload PDFs first?
        The system needs to process and understand your documents before it can answer questions about them. This processing creates a "vector store" which enables efficient information retrieval.
        
        ### Can I use the same vector store for different scenarios?
        Yes! Once you've created a vector store, you can use it with any number of different scenarios.
        
        ### What should I include in a scenario description?
        A good scenario description includes the context, purpose, and any specific constraints for the conversation. For example, "Act as a financial advisor helping a client understand retirement options."
        
        ### How long can chat sessions last?
        You can set the duration of each chat session when you start it. The system will automatically end the session when time runs out.
        
        ### Is my data secure?
        All data is processed locally and stored in a Redis database on your system. No information is sent to external servers beyond what's needed for API calls to the language model.
        """
        )


if __name__ == "__main__":
    main()
