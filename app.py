from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from main import process_query
from voice.speech_to_text import SpeechToText
import os
import logging
import tempfile
import shutil
import wave
from pydub import AudioSegment

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files (for CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")


# Vosk model path
vosk_model_path = "./vosk-model-small-en-us-0.15"

# Initialize SpeechToText
stt = SpeechToText(model_path=vosk_model_path)

def is_valid_wav(file_path):
    """Check if the file is a valid WAV file."""
    try:
        with wave.open(file_path, 'rb') as wf:
            logger.info(f"WAV file validated: channels={wf.getnchannels()}, rate={wf.getframerate()}, frames={wf.getnframes()}")
            return True
    except wave.Error as e:
        logger.error(f"Invalid WAV file: {str(e)}")
        return False

def convert_to_wav(input_path, output_path):
    """Convert input audio to WAV format (16kHz, mono, 16-bit PCM)."""
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)  # 16-bit PCM
        audio.export(output_path, format="wav")
        logger.info(f"Converted audio to WAV: {output_path}, size: {os.path.getsize(output_path)} bytes")
        return True
    except Exception as e:
        logger.error(f"Failed to convert audio to WAV: {str(e)}")
        return False

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload_audio", response_class=HTMLResponse)
async def upload_audio(request: Request, audio_file: UploadFile = File(...)):
    # Use a temporary directory to store the uploaded audio file
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded file (could be WebM, OGG, etc.)
            input_file_path = os.path.join(temp_dir, "input_audio.webm")
            with open(input_file_path, "wb") as buffer:
                shutil.copyfileobj(audio_file.file, buffer)
                file_size = os.path.getsize(input_file_path) if os.path.exists(input_file_path) else 0
                logger.info(f"Uploaded audio saved to {input_file_path}, size: {file_size} bytes")

            # Verify file was saved
            if not os.path.exists(input_file_path) or file_size == 0:
                logger.error("Uploaded audio file was not saved correctly")
                return templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "Failed to save uploaded audio file."
                })

            # Convert to WAV
            wav_file_path = os.path.join(temp_dir, "temp_audio.wav")
            if not convert_to_wav(input_file_path, wav_file_path):
                logger.error("Audio conversion to WAV failed")
                return templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "Failed to convert audio to WAV format."
                })

            # Validate WAV file
            if not is_valid_wav(wav_file_path):
                logger.error("Converted file is not a valid WAV file")
                return templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "Converted audio is not a valid WAV file."
                })

            # Transcribe the WAV file
            try:
                text = stt.transcribe_audio(wav_file_path)
                logger.info(f"Transcription result: '{text}'")
                if not text:
                    logger.warning("Transcription returned no text")
                    return templates.TemplateResponse("index.html", {
                        "request": request,
                        "error": "Could not understand the audio. Please try speaking clearly."
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

    except Exception as e:
        logger.error(f"Error processing uploaded audio: {str(e)}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error processing audio: {str(e)}"
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
