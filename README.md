# OpenVoice Server

OpenVoice Server is a FastAPI application that provides endpoints for uploading audio files, changing the base speaker, performing text-to-speech conversion, and synthesizing speech from text using a specified voice and style.
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

The server provides the following endpoints:

### 1. Upload Base Speaker

This endpoint allows you to upload a .pth file for a new base speaker.

**Endpoint:** `/upload_base_speaker/`

**Method:** `POST`

**Request Body:**

- `file` (file): The .pth file to be uploaded.

**Example Request:**

```python
import requests

url = "http://localhost:8000/upload_base_speaker/"
file = open("example_speaker.pth", "rb")

response = requests.post(url, files={"file": file})

print(response.json())
```

### 2. Change Base Speaker

This endpoint allows you to change the base speaker.

**Endpoint:** `/change_base_speaker/`

**Method:** `POST`

**Request Body:**

- `speaker_name` (str): The name of the new base speaker.

**Example Request:**

```python
import requests

url = "http://localhost:8000/change_base_speaker/"
data = {"speaker_name": "example_speaker"}

response = requests.post(url, data=data)

print(response.json())
```

### 3. Base Text-to-Speech

This endpoint performs text-to-speech conversion using only the base speaker.

**Endpoint:** `/base_tts/`

**Method:** `GET`

**Request Body:**

- `text` (str): The text to be converted to speech.
- `style` (str, optional): The style to be used for the synthesized speech. Defaults to 'default'.
- `language` (str, optional): The language of the text to be synthesized. Defaults to 'English'.
- `speed` (float, optional): The speed of the synthesized speech. Defaults to 1.0.

**Example Request:**

```python
import requests

url = "http://localhost:8000/base_tts/"
params = {
    "text": "Hello, world!",
    "style": "default",
    "language": "English",
    "speed": 1.0
}

response = requests.get(url, params=params)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

### 4. Change Voice

This endpoint allows you to change the voice of an existing audio file.

**Endpoint:** `/change_voice/`

**Method:** `POST`

**Request Body:**

- `reference_speaker` (str): The name of the reference speaker.
- `file` (file): The audio file to be changed.
- `watermark` (str, optional): The watermark to be encoded in the voice conversion. Defaults to '@MyShell'.

**Example Request:**

```python
import requests

url = "http://localhost:8000/change_voice/"
file = open("example.wav", "rb")
data = {"reference_speaker": "example_speaker"}

response = requests.post(url, data=data, files={"file": file})

with open("output.wav", "wb") as f:
    f.write(response.content)
```

### 5. Upload Audio

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

### 6. Synthesize Speech

This endpoint synthesizes speech from text using a specified voice and style.

**Endpoint:** `/synthesize_speech/`

**Method:** `GET`

**Request Body:**

- `text` (str): The text to be synthesized into speech.
- `voice` (str): The voice to be used for the synthesized speech.
- `style` (str, optional): The style to be used for the synthesized speech. Defaults to 'default'.
- `language` (str, optional): The language of the text to be synthesized. Defaults to 'English'.
- `speed` (float, optional): The speed of the synthesized speech. Defaults to 1.0.
- `watermark` (str, optional): The watermark to be encoded in the voice conversion. Defaults to '@MyShell'.

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
