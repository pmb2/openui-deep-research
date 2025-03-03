#!/bin/bash

# Start the custom deep research agent

# Print banner
echo "========================================"
echo "   Custom Deep Research Agent Startup   "
echo "========================================"

# Check if .env file exists, create if not
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
  echo "Please edit .env file and add your API keys before continuing."
  exit 1
fi

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null; then
  echo "Docker is not installed. Please install Docker before continuing."
  exit 1
fi

if ! command -v docker-compose &> /dev/null; then
  if ! command -v docker compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose before continuing."
    exit 1
  fi
  DOCKER_COMPOSE="docker compose"
else
  DOCKER_COMPOSE="docker-compose"
fi

# Start the services
echo "Starting services..."
$DOCKER_COMPOSE up -d

echo "Services started! The research agent is now available at:"
echo "- Backend API: http://localhost:8000"
echo "- Open WebUI: http://localhost:3001"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop services, run: docker-compose down"
