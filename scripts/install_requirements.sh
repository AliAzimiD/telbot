#!/bin/bash
# Ultimate installation script for telbot

echo "🚀 Installing TELBOT Ultimate Requirements..."

# System dependencies for Ubuntu 22.04
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    g++ \
    clang \
    python3-dev \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    pkg-config \
    git \
    curl \
    wget

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and core tools
pip install --upgrade pip setuptools wheel

# Install PyTorch CPU-only first
pip install torch==2.3.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install llama-cpp-python with optimizations
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python==0.2.78

# Install core requirements
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm

# Install NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"

echo "✅ Installation complete!"
echo "Run: source .venv/bin/activate && python bot.py"