# OpenVoice Server

OpenVoice Server is a FastAPI application that provides endpoints for uploading audio files and synthesizing speech from text using a specified voice and style.
It is built on top of the OpenVoice project, which is a versatile instant voice cloning system that can accurately clone the reference tone color and generate speech in multiple languages and accents.
See: https://github.com/myshell-ai/OpenVoice

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ValyrianTech/OpenVoice_server.git
   ```
2. Navigate to the project directory:
   ```bash
   cd openvoice_server
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the server, run the following command:

```bash
cd openvoice
uvicorn openvoice_server:app --host 0.0.0.0 --port 8000
```

The server provides two main endpoints:

### 1. Upload Audio

This endpoint allows you to upload an audio file that will be used as the reference audio for speech synthesis.

**Endpoint:** `/upload_audio/`

**Method:** `POST`

**Request Body:**

- `audio_file_label` (str): The label for the audio file.
- `file` (file): The audio file to be uploaded.

**Example Request:**

```python
import requests

url = "http://localhost:8000/upload_audio/"
audio_file_label = "example_label"
file = open("example.wav", "rb")

response = requests.post(url, data={"audio_file_label": audio_file_label}, files={"file": file})

print(response.json())
```

### 2. Synthesize Speech

This endpoint synthesizes speech from text using a specified voice and style.

**Endpoint:** `/synthesize_speech/`

**Method:** `GET`

**Request Body:**

- `text` (str): The text to be synthesized into speech.
- `voice` (str): The voice to be used for synthesis. This is the audio file label from the other endpoint.
- `style` (str, optional): The style to be used for synthesis. Defaults to 'default'. Options are: ['default', 'whispering', 'cheerful', 'terrified', 'angry', 'sad', 'friendly']
- `language` (str, optional): The language to be used for synthesis. Defaults to 'English'.
- `speed` (float, optional): The speed of the synthesized speech. Defaults to 1.0.

**Example Request:**

```python
import requests

url = "http://localhost:8000/synthesize_speech/"
data = {
    "text": "Hello, world!",
    "voice": "example_label",
    "style": "default",
    "language": "English",
    "speed": 1.0
}

response = requests.get(url, params=data)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

The response will be the synthesized speech audio file. In the headers of the response are 2 additional fields:
- x-elapsed-time: The time taken to synthesize the speech in seconds.
- x-device-used: The device used for synthesis.
