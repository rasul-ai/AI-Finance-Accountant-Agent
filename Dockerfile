FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y wget ffmpeg unzip curl gcc  && \
    rm -rf /var/lib/apt/lists/*

   # Set working directory
   WORKDIR /app

   # Set Hugging Face cache directory
   ENV HF_HOME=/app/cache

   # Create cache directory and set permissions
   RUN mkdir -p /app/cache /app/db && chmod -R 777 /app/cache /app/db

# Copy your code into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install --no-cache-dir torch==2.2.0+cpu torchvision==0.17.0+cpu torchaudio==2.2.0+cpu -f https://download.pytorch.org/whl/torch_stable.html


# Install spaCy model
RUN python -m spacy download en_core_web_lg
# RUN python -m spacy download en_core_web_sm

# Download and unzip the Vosk model
RUN wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip vosk-model-small-en-us-0.15.zip && \
    rm vosk-model-small-en-us-0.15.zip

# Install Ollama
# RUN curl -fsSL https://ollama.com/install.sh | sh

# Pull the Ollama model
# RUN ollama serve & sleep 5 && ollama pull gemma:2b

# Expose the port FastAPI will run on
EXPOSE 7860

# Start the API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]