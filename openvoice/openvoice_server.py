import os
import time

import torch
import se_extractor
import io
import magic

from fastapi import FastAPI, UploadFile, File, HTTPException
from starlette.responses import FileResponse, Response
from typing import Optional
from pydantic import BaseModel

from api import BaseSpeakerTTS, ToneColorConverter

app = FastAPI()

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


class SynthesizeSpeechRequest(BaseModel):
    text: str
    voice: Optional[str] = 'default_voice.wav'
    style: Optional[str] = 'default'
    language: Optional[str] = 'English'
    speed: Optional[float] = 1.0


class UploadAudioRequest(BaseModel):
    audio_file_label: str


@app.post("/upload_audio/")
async def upload_audio(request: UploadAudioRequest, file: UploadFile = File(...)):
    """
    Upload an audio file for later use as the reference audio.

    :param request: The request parameters.
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
        stored_file_name = f"{request.audio_file_label}.{file_extension}"

        with open(f"resources/{stored_file_name}", "wb") as f:
            f.write(contents)

        return {"message": f"File {file.filename} uploaded successfully with label {request.audio_file_label}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize_speech/")
async def synthesize_speech(request: SynthesizeSpeechRequest, response: Response):

    """
    Synthesize speech from text using a specified voice and style.

    :param request: The request parameters.
    :type request: SynthesizeSpeechRequest
    :param response: The response object.
    :type response: Response
    :return: Confirmation of successful synthesis.
    :rtype: dict
    """
    start_time = time.time()
    try:
        # Retrieve the correct file based on the 'voice' parameter
        # It should match the 'audio_file_label' used while uploading
        matching_files = [file for file in os.listdir("resources") if file.startswith(request.voice)]

        if not matching_files:
            raise HTTPException(status_code=400, detail="No matching voice found.")

        reference_speaker = f'resources/{matching_files[0]}'

        target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, target_dir='processed', vad=True)
        save_path = f'{output_dir}/output_en_default.wav'

        # Run the base speaker tts
        src_path = f'{output_dir}/tmp.wav'
        base_speaker_tts.tts(request.text, src_path, speaker=request.style, language=request.language, speed=request.speed)

        # Run the tone color converter
        encode_message = "@MyShell"
        tone_color_converter.convert(
            audio_src_path=src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=encode_message)

        result = FileResponse(save_path, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    end_time = time.time()
    elapsed_time = end_time - start_time
    response.headers["X-Elapsed-Time"] = str(elapsed_time)
    response.headers["X-Device-Used"] = device

    return result
