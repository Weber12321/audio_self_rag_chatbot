import os
import tempfile
import time
from typing import Tuple
import requests
import tempfile
from typing import Literal

from src.utils.log_handler import setup_logger


logger = setup_logger(__name__)


class BronciWrapper:

    def __init__(self) -> None:
        self.username = os.getenv("BRONCI_USERNAME", "ASR0307_27714944")
        self.password = os.getenv("BRONCI_PASSWORD", "Api030727714944")
        self.api_url = os.getenv("BRONCI_API_URL", "https://asrapi01.bronci.com.tw")
        self.model = os.getenv("BRONCI_MODEL", "basic-taigi.2024.06.27")
        self.token = self.login()
        if not self.token:
            raise ValueError("Failed to get authentication token.")

    def login(self):
        """Logs in to the ASR service and returns the authentication token."""
        login_url = f"{self.api_url}/api/v1/login"
        credentials = {"username": self.username, "password": self.password}
        try:
            response = requests.post(
                login_url,
                json=credentials,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            if "token" not in data:
                raise ValueError("Login failed: Token not found in response.")
            logger.info("Login successful.")
            return data["token"]
        except (requests.RequestException, ValueError) as e:
            logger.error("Login failed: %s", e)
            raise

    def post_subtitle_task(
        self, audio_path, title="sample", description="sample", speaker_number=1
    ) -> Tuple[int, int]:
        """Posts a subtitle task to the ASR service."""

        subtitle_url = f"{self.api_url}/api/v1/subtitle/tasks"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            with open(audio_path, "rb") as audio_file:
                files = {"filename": audio_file}
                response = requests.post(
                    subtitle_url,
                    headers=headers,
                    files=files,
                    data={
                        "title": title,
                        "description": description,
                        "modelVersion": self.model,
                        "speakerNum": speaker_number,
                        "sourceType": 2,
                    },
                )
            response.raise_for_status()
            data = response.json()

            if data["code"] != 200:
                error_message = f"Failed to post subtitle task. error: {data['error']}"
                raise ValueError(error_message)
            return data["id"], data["code"]
        except requests.RequestException as e:
            logger.error("Failed to post subtitle task: %s", e)
            raise
        except KeyError as e:
            logger.error("Invalid response: %s", e)
            raise
        except Exception as e:
            logger.error(
                "Invalid response: %s with respnose text %s", (e, response.text)
            )
            raise

    def get_subtitle_task(self, task_id: int) -> int:
        """Retrieves the status of a subtitle task."""
        subtitle_url = f"{self.api_url}/api/v1/subtitle/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(subtitle_url, headers=headers)
            response.raise_for_status()
            results = response.json()
            if results["code"] == 200:
                return results["data"][0]["status"]
            else:
                logger.error("Failed to get subtitle task: %s", results)
                raise ValueError("Failed to get subtitle task")
        except requests.RequestException as e:
            logger.error("Failed to get subtitle task: %s", e)
            raise

    def get_url(self, task_id: int) -> str:
        """Downloads the transcribed subtitle file."""
        subtitle_url = f"https://asrapi01.bronci.com.tw/api/v1/subtitle/tasks/{task_id}/subtitle-link"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(
                subtitle_url, headers=headers, params={"type": "DIA"}
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 200:
                raise ValueError(f"Failed to get subtitle link: {data}")
            return data["data"][0]["url"]
        except requests.RequestException as e:
            logger.error("Failed to download subtitle file: %s", e)
            raise

    def download_and_extract_text(self, url: str):
        """Downloads a file from a URL, saves it to a temporary file,
        reads its content, and returns the content as a string.
        Cleans up the temporary file afterwards.

        Args:
            url: The URL of the file to download.

        Returns:
            The text content of the file as a string, or None if an error occurred.
        """
        try:
            # Download the file
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dia") as temp_file:
                # Write the downloaded content to the temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name  # Store the path

            # Read the content from the temporary file
            with open(temp_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            return file_content

        except requests.exceptions.RequestException as e:
            print(f"Error downloading the file: {e}")
            return None
        except IOError as e:
            print(f"Error reading the file: {e}")
            return None
        finally:
            # Clean up the temporary file (important!)
            if "temp_file_path" in locals():
                try:
                    os.remove(temp_file_path)
                except OSError as e:
                    print(
                        f"Warning - could not delete temporary file"
                        f" {temp_file_path}: {e}"
                    )

    def delete_task(self, task_id: int):
        """Deletes a subtitle task."""
        subtitle_url = f"{self.api_url}/api/v1/subtitle/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.delete(subtitle_url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to delete subtitle task: %s", e)
            raise

    def transcribe(
        self,
        audio_path,
        title="sample",
        description="sample",
        speaker_number=2,
        max_retry=30,
    ) -> str:
        logger.info("Transcribing audio file: %s", audio_path)
        task_id, _ = self.post_subtitle_task(
            audio_path, title, description, speaker_number
        )
        logger.info("Get transcription task id: %s", task_id)
        retry = 0
        while True:
            if retry <= max_retry:
                status = self.get_subtitle_task(task_id)
                if status != 3:
                    time.sleep(2)
                    continue
            break

        url = f"{self.get_url(task_id)}?token={self.token}"
        text = self.download_and_extract_text(url)
        logger.info("Get transcription text: %s", text)
        if text:
            self.delete_task(task_id)
            return text
        raise ValueError("Failed to transcribe audio file.")


bronci_instance = BronciWrapper()


class AudioToText:
    """
    Interface for converting audio to text here using function calling
    """

    def __call__(
        self,
        audio_file: bytes,
        audio_type: Literal["wav", "mp3", "m4a", "mp4", "ogg"] = "wav",
    ) -> str:

        with tempfile.NamedTemporaryFile(delete=True, suffix=f".{audio_type}") as tmp:
            tmp.write(audio_file)
            tmp.flush()
            result = bronci_instance.transcribe(tmp.name)
        return result.strip()
