# Use official Python image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl gcc portaudio19-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your code into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt



# Install spaCy model
RUN python -m spacy download en_core_web_lg

# Download and unzip the Vosk model
RUN wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip vosk-model-small-en-us-0.15.zip && \
    rm vosk-model-small-en-us-0.15.zip

# Install Ollama
# RUN curl -fsSL https://ollama.com/install.sh | sh

# Pull the Ollama model
# RUN ollama serve & sleep 5 && ollama pull gemma:2b

# Expose the port FastAPI will run on
EXPOSE 10000

# Start the API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]

