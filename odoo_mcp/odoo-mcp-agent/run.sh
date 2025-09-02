#!/bin/bash

# Simple run script for Odoo MCP Agent

echo "🤖 Odoo MCP Agent Launcher"
echo "========================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Creating from example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env with your credentials before running!"
    exit 1
fi

# Check for command
if [ -z "$1" ]; then
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  app      - Run Streamlit app"
    echo "  install  - Install dependencies"
    exit 1
fi

case "$1" in
    app)
        echo "🚀 Starting Streamlit app..."
        streamlit run streamlit_app.py
        ;;
    install)
        echo "📦 Installing dependencies..."
        pip install openai-agents openai-agents-mcp streamlit python-dotenv
        echo "✅ Dependencies installed!"
        ;;
    *)
        echo "❌ Unknown command: $1"
        exit 1
        ;;
esac