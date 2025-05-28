# runbot.sh
#!/bin/bash
# Telegram Bot Startup Script

echo "Starting Telegram Bot..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
 source .venv/bin/activate
 echo "Virtual environment activated"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
 echo ".env file not found. Copy from .env.example"
 exit 1
fi

# Check if model exists
MODEL_PATH=$(grep MODEL_PATH .env | cut -d '=' -f2)
if [ ! -f "$MODEL_PATH" ]; then
 echo "Model file not found at $MODEL_PATH"
 echo "Run: python scripts/install_model.py"
fi

# Start the bot
python bot.py