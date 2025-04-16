# Use official Python image
FROM python:3.10-slim

# Install system dependencies required for PyAudio
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy your code into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Make sure setup.sh is executable
RUN chmod +x setup.sh

# Run the app
CMD ["bash", "-c", "source setup.sh && uvicorn app:app --host 0.0.0.0 --port 10000"]
