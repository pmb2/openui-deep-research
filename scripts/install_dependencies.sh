#!/bin/bash

# Install dependencies for the custom deep research agent

# Print banner
echo "==============================================="
echo "   Custom Deep Research Agent Setup Script     "
echo "==============================================="

# Make sure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

# Create necessary directories
mkdir -p data
mkdir -p logs

# Check for Docker and Docker Compose
echo "Checking for Docker..."
if ! command -v docker &> /dev/null; then
  echo "Docker is not installed. Would you like to install it? (y/n)"
  read -r install_docker
  if [[ "$install_docker" =~ ^[Yy]$ ]]; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    sudo usermod -aG docker "$USER"
    echo "Docker installed. You may need to log out and back in for group changes to take effect."
  else
    echo "Docker is required. Please install it manually and run this script again."
    exit 1
  fi
fi

echo "Checking for Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
  echo "Docker Compose is not installed. Would you like to install it? (y/n)"
  read -r install_compose
  if [[ "$install_compose" =~ ^[Yy]$ ]]; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed."
  else
    echo "Docker Compose is required. Please install it manually and run this script again."
    exit 1
  fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
  echo "Creating default .env file..."
  cat > .env << EOF
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Configuration
DEBUG=false
PORT=8000
SESSION_TIMEOUT_MINUTES=60

# Model Settings
GROQ_MODEL=deepseek-r1-distill-llama-70b
USE_OLLAMA_FALLBACK=true
OLLAMA_MODEL=deepseek-r1-distill-llama-70b

# Service URLs
PERPLEXICA_URL=http://perplexica:3000
OLLAMA_HOST=http://ollama:11434
EOF
  echo "Created .env file. Please edit it to add your API keys."
fi

# Make scripts executable
chmod +x scripts/*.sh

echo "Dependencies checked! You can now run: ./scripts/start.sh"
