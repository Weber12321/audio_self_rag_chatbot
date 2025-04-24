# Viki Audio Chatbot Tools

## Description

This project provides a set of tools for building and interacting with a conversational AI system. It includes functionalities for managing PDF documents, creating conversational scenarios, and engaging in timed chat sessions with an AI assistant powered by Google Gemini. The system utilizes RAG (Retrieval-Augmented Generation) to provide contextually relevant answers based on uploaded documents and defined scenarios.

## Requirements

- Docker
- Docker Compose

## Setup

1.  **Install Prerequisites:** Ensure you have Docker and Docker Compose installed on your system.
2.  **Build Docker Image:** Build the necessary Docker image using the following command in the project root directory:
    ```sh
    docker build -f dockers/Dockerfile -t timer_chatbot:develop .
    ```
3.  **Configure Environment:**
    - Copy the example environment file:
      ```sh
      cp .env.example .env
      ```
    - Edit the `.env` file and add your Google Gemini API key to the `GOOGLE_API_KEY` variable.
4.  **Port Configuration:** Be aware of the `PORT_OFFSET` variable in the `.env` file. This value determines the host ports exposed by the containers. For example, if `PORT_OFFSET=66`, the Streamlit application will be accessible on port `6601` and Redis on `6679`. Adjust this value if the default ports conflict with other services on your machine.
5.  **Run the Application:** Start the services using Docker Compose:
    ```sh
    docker-compose up -d
    ```
6.  **Access the Application:** Open your web browser and navigate to `http://localhost:{PORT_OFFSET}01/` (replace `{PORT_OFFSET}` with the value set in your `.env` file, e.g., `http://localhost:6601/`).
7.  **Usage Guide:** For detailed instructions on how to use the different tools (PDF upload, scenario creation, chat interface), please refer to the application's index page, implemented in [apps/page/index.py](apps/page/index.py).

## Contact

For any questions or issues, please contact Weber (Yen-Chun), Huang.
