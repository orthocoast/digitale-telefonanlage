#!/bin/bash
# Start script for development server with environment variables

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
    echo "✓ Environment variables loaded from .env"
else
    echo "✗ Error: .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Start the development server
echo "Starting development server..."
python3 webhook_server_dev.py
