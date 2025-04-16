#!/bin/bash

# Install dependencies (already handled by Render, but for manual/local runs)
# pip install -r requirements.txt


# Update and install system packages
# sudo apt-get update
# sudo apt-get install portaudio19-dev -y

# Install spaCy language model
python -m spacy download en_core_web_lg

# Install ollama
curl -fsSL https://ollama.com/install.sh | sh

#Start ollama server
ollama serve

# Pull Ollama model
ollama pull gemma:2b

# Check ollama list
ollama list

