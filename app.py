# app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from main import process_query
from voice.speech_to_text import SpeechToText
import os
import asyncio
import pyaudio
import wave
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files (for CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Vosk model path and audio file path
vosk_model_path = "./vosk-model-small-en-us-0.15"
audio_file_path = "voice/temp_audio.wav"

# Ensure the voice directory exists
os.makedirs("voice", exist_ok=True)

# Initialize SpeechToText
stt = SpeechToText(model_path=vosk_model_path)

# Global variables for recording state
recording = False
audio_frames = []
recording_task = None

def save_audio_to_wav(frames, sample_rate=16000):
    """Save audio frames to a WAV file."""
    try:
        logger.info(f"Saving audio to {audio_file_path} with {len(frames)} frames")
        wf = wave.open(audio_file_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        if os.path.exists(audio_file_path):
            logger.info(f"WAV file saved successfully: {os.path.getsize(audio_file_path)} bytes")
        else:
            logger.error("WAV file was not created")
    except Exception as e:
        logger.error(f"Error saving WAV file: {str(e)}")
        raise

async def record_audio():
    """Background task to record audio."""
    global audio_frames
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        stream.start_stream()
        logger.info("Recording started...")

        while recording:
            data = stream.read(1024, exception_on_overflow=False)
            audio_frames.append(data)
            await asyncio.sleep(0.01)  # Small sleep to prevent blocking

        stream.stop_stream()
        stream.close()
        logger.info(f"Recording stopped, captured {len(audio_frames)} frames")
    except Exception as e:
        logger.error(f"Error during recording: {str(e)}")
    finally:
        p.terminate()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/start_recording", response_class=JSONResponse)
async def start_recording():
    global recording, audio_frames, recording_task
    if not recording:
        recording = True
        audio_frames = []
        recording_task = asyncio.create_task(record_audio())
        logger.info("Started recording task")
        return {"status": "Recording started"}
    logger.warning("Recording already in progress")
    return {"status": "Already recording"}

@app.post("/stop_recording", response_class=HTMLResponse)
async def stop_recording(request: Request):
    global recording, recording_task
    if recording:
        recording = False
        if recording_task:
            await recording_task  # Wait for the recording task to complete
            recording_task = None

        # Save the audio to WAV
        try:
            save_audio_to_wav(audio_frames)
        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": f"Failed to save audio: {str(e)}"
            })

        # Transcribe the saved audio
        try:
            text = stt.transcribe_audio(audio_file_path)
            logger.info(f"Transcription result: '{text}'")
            if not text:
                logger.warning("Transcription returned no text")
                return templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "Could not understand the audio."
                })
            return templates.TemplateResponse("index.html", {
                "request": request,
                "transcribed_text": text
            })
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": f"Transcription error: {str(e)}"
            })
    logger.warning("No recording in progress")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "error": "No recording in progress."
    })

@app.post("/query", response_class=HTMLResponse)
async def handle_query(request: Request, query_text: str = Form(...), use_retriever: str = Form("no")):
    use_retriever = use_retriever.lower() in ["yes", "y"]
    result = await process_query(vosk_model_path, query_text=query_text, use_retriever=use_retriever)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "User_Query": query_text,
        "Intent": result["intent"],
        "Entities": result["entities"],
        "API_Response": result["base_response"],
        "RAG_Response": result["retriever_response"],
        "Web_Search_Response": result["web_search_response"],
        "Final_Response": result["final_response"],
        "Error": result["error"]
    })