# voice/speech_to_text.py
import wave
import vosk
import pyaudio
import io
import json
from vosk import Model, KaldiRecognizer

class SpeechToText:
    def __init__(self, model_path):
        self.model = vosk.Model(model_path)
        self.sample_rate = 16000

    def listen(self, duration=10, sample_rate=16000):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=1024)
        stream.start_stream()

        print("Listening...")
        frames = []
        for _ in range(0, int(sample_rate / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Convert frames to WAV format
        wf = wave.open(io.BytesIO(), 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Transcribe
        wf.seek(0)
        rec = vosk.KaldiRecognizer(self.model, sample_rate)
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        return result.get("text", "")

    def transcribe_audio(self, audio_file):
        """
        Process an audio file and convert speech to text using Vosk.

        Args:
            audio_file (str): Path to the audio file (WAV format).

        Returns:
            str: The recognized text, or None if recognition fails.
        """
        try:
            wf = wave.open(audio_file, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000, 32000, 44100, 48000]:
                print("Audio file must be WAV format, mono, 16-bit, with a supported sample rate.")
                return None

            rec = KaldiRecognizer(self.model, wf.getframerate())
            print("Processing audio with Vosk...")

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    return result.get("text", "")

            final_result = json.loads(rec.FinalResult())
            text = final_result.get("text", "")
            print(f"Recognized text: {text}")
            return text

        except Exception as e:
            print(f"Error processing audio: {e}")
            return None