import os
import time
import torch
import se_extractor
import io
import magic
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from api import BaseSpeakerTTS, ToneColorConverter

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize OpenVoice models
ckpt_base = 'checkpoints/base_speakers/EN'
ckpt_converter = 'checkpoints/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
base_speaker_tts = BaseSpeakerTTS('checkpoints/base_speakers/EN/config.json', device=device)
base_speaker_tts.load_ckpt('checkpoints/base_speakers/EN/checkpoint.pth')
tone_color_converter = ToneColorConverter('checkpoints/converter/config.json', device=device)
tone_color_converter.load_ckpt('checkpoints/converter/checkpoint.pth')

output_dir = 'outputs'
os.makedirs(output_dir, exist_ok=True)

source_se = torch.load(f'{ckpt_base}/en_default_se.pth').to(device)


class UploadAudioRequest(BaseModel):
    audio_file_label: str


@app.post("/upload_base_speaker/")
async def upload_base_speaker(file: UploadFile = File(...)):
    """
    Upload a .pth file for a new base speaker.

    :param file: The .pth file to be uploaded.
    :type file: UploadFile
    :return: Confirmation of successful upload.
    :rtype: dict
    """
    try:
        contents = await file.read()
        with open(f"checkpoints/base_speakers/EN/{file.filename}", "wb") as f:
            f.write(contents)
        return {"message": f"File {file.filename} uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/change_base_speaker/")
async def change_base_speaker(speaker_name: str):
    """
    Change the base speaker.

    :param speaker_name: The name of the new base speaker.
    :type speaker_name: str
    :return: Confirmation of successful change.
    :rtype: dict
    """
    try:
        base_speaker_tts.load_ckpt(f'checkpoints/base_speakers/EN/{speaker_name}.pth')
        return {"message": f"Base speaker changed to {speaker_name} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/base_tts/")
async def base_tts(text: str, style: Optional[str] = 'default', language: Optional[str] = 'English', speed: Optional[float] = 1.0):
    """
    Perform text-to-speech conversion using only the base speaker.

    :param text: The text to be converted to speech.
    :type text: str
    :param style: The style to be used for the synthesized speech, defaults to 'default'.
    :type style: str, optional
    :param language: The language of the text to be synthesized, defaults to 'English'.
    :type language: str, optional
    :param speed: The speed of the synthesized speech, defaults to 1.0.
    :type speed: float, optional
    :return: The speech audio.
    :rtype: .wav file
    """
    try:
        save_path = f'{output_dir}/output_en_default.wav'
        base_speaker_tts.tts(text, save_path, speaker=style, language=language, speed=speed)
        result = StreamingResponse(open(save_path, 'rb'), media_type="audio/wav")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/change_voice/")
async def change_voice(file: UploadFile = File(...), watermark: Optional[str] = "@MyShell"):
    """
    Change the voice of an existing audio file.

    :param file: The audio file to be changed.
    :type file: UploadFile
    :param watermark: The watermark to be encoded in the voice conversion, defaults to '@MyShell'.
    :type watermark: str, optional
    :return: The audio file with the changed voice.
    :rtype: .wav file
    """
    try:
        contents = await file.read()
        temp_file = io.BytesIO(contents)
        target_se, audio_name = se_extractor.get_se(temp_file, tone_color_converter, target_dir='processed', vad=True)
        save_path = f'{output_dir}/output_en_default.wav'
        tone_color_converter.convert(
            audio_src_path=temp_file,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=watermark)
        result = StreamingResponse(open(save_path, 'rb'), media_type="audio/wav")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload_audio/")
async def upload_audio(audio_file_label: str = Form(...), file: UploadFile = File(...)):
    """
    Upload an audio file for later use as the reference audio.

    :param audio_file_label: The label for the audio file.
    :param file: The audio file to be uploaded.
    :type file: UploadFile
    :return: Confirmation of successful upload.
    :rtype: dict
    """
    try:
        contents = await file.read()

        allowed_extensions = {'wav', 'mp3', 'flac', 'ogg'}
        max_file_size = 5 * 1024 * 1024  # 5MB

        if not file.filename.split('.')[-1] in allowed_extensions:
            return {"error": "Invalid file type. Allowed types are: wav, mp3, flac, ogg"}

        if len(contents) > max_file_size:
            return {"error": "File size is over limit. Max size is 5MB."}

        # Note: we need to first write the file in order to check magic.
        temp_file = io.BytesIO(contents)
        file_format = magic.from_buffer(temp_file.read(), mime=True)

        if 'audio' not in file_format:
            return {"error": "Invalid file content."}

        # Make sure the resources directory exists
        os.makedirs("resources", exist_ok=True)

        # Use provided 'audio_file_label' for stored file's name.
        # We retain the file extension to ensure appropriate processing later.
        file_extension = file.filename.split('.')[-1]
        stored_file_name = f"{audio_file_label}.{file_extension}"

        with open(f"resources/{stored_file_name}", "wb") as f:
            f.write(contents)

        return {"message": f"File {file.filename} uploaded successfully with label {audio_file_label}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/synthesize_speech/")
async def synthesize_speech(
        text: str,
        voice: str,
        style: Optional[str] = 'default',
        language: Optional[str] = 'English',
        speed: Optional[float] = 1.0,
        watermark: Optional[str] = "@MyShell"
):
    """
    Synthesize speech from text using a specified voice and style.

    :param text: The text to be synthesized into speech.
    :type text: str
    :param voice: The voice to be used for the synthesized speech.
    :type voice: str
    :param style: The style to be used for the synthesized speech, defaults to 'default'.
    :type style: str, optional
    :param language: The language of the text to be synthesized, defaults to 'English'.
    :type language: str, optional
    :param speed: The speed of the synthesized speech, defaults to 1.0.
    :type speed: float, optional
    :param watermark: The watermark to be encoded in the voice conversion, defaults to '@MyShell'.
    :type watermark: str, optional
    :return: The synthesized speech as a .wav file.
    :rtype: .wav file
    """
    start_time = time.time()
    try:
        # Retrieve the correct file based on the 'voice' parameter
        # It should match the 'audio_file_label' used while uploading
        matching_files = [file for file in os.listdir("resources") if file.startswith(voice)]

        if not matching_files:
            raise HTTPException(status_code=400, detail="No matching voice found.")

        reference_speaker = f'resources/{matching_files[0]}'

        target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, target_dir='processed', vad=True)
        save_path = f'{output_dir}/output_en_default.wav'

        # Run the base speaker tts
        src_path = f'{output_dir}/tmp.wav'
        base_speaker_tts.tts(text, src_path, speaker=style, language=language, speed=speed)

        # Run the tone color converter
        tone_color_converter.convert(
            audio_src_path=src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=watermark)

        result = StreamingResponse(open(save_path, 'rb'), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    end_time = time.time()
    elapsed_time = end_time - start_time

    result.headers["X-Elapsed-Time"] = str(elapsed_time)
    result.headers["X-Device-Used"] = device

    # Add CORS headers
    result.headers["Access-Control-Allow-Origin"] = "*"  # Required for CORS support
    result.headers["Access-Control-Allow-Credentials"] = "true"  # Required for cookies, authorization headers with HTTPS
    result.headers["Access-Control-Allow-Headers"] = "Origin, Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token, locale"
    result.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"

    return result
