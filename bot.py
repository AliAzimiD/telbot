#!/usr/bin/env python3
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core.bot_controller import BotController
from core.config_manager import ConfigManager
from core.message_router import MessageRouter
from utils.error_handler import ErrorHandler
from utils.response_formatter import ResponseFormatter

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Telegram bot class with improved modularity."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.bot_controller = BotController(config_manager)
        self.message_router = MessageRouter(self.bot_controller)
        self.error_handler = ErrorHandler(config_manager)
        self.response_formatter = ResponseFormatter(config_manager)
        
        # Initialize Telegram application
        self.app = Application.builder().token(self.config.telegram_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Set up all command and message handlers."""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("help", self._handle_help))
        self.app.add_handler(CommandHandler("status", self._handle_status))
        self.app.add_handler(CommandHandler("stats", self._handle_stats))
        
        # Message handler for queries
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_query)
        )
        
        # Error handler
        self.app.add_error_handler(self.error_handler.handle_error)
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        try:
            response = await self.message_router.route_start_command(update.effective_user)
            await self._send_response(update, response)
        except Exception as e:
            await self.error_handler.handle_command_error(update, e, "start")
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        try:
            response = await self.message_router.route_help_command()
            await self._send_response(update, response)
        except Exception as e:
            await self.error_handler.handle_command_error(update, e, "help")
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        try:
            response = await self.message_router.route_status_command()
            await self._send_response(update, response)
        except Exception as e:
            await self.error_handler.handle_command_error(update, e, "status")
    
    async def _handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command."""
        try:
            if not self.bot_controller.is_admin(update.effective_user.id):
                await update.message.reply_text("Access denied.")
                return
            
            response = await self.message_router.route_stats_command()
            await self._send_response(update, response)
        except Exception as e:
            await self.error_handler.handle_command_error(update, e, "stats")
    
    async def _handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle user queries."""
        try:
            # Show typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, 
                action="typing"
            )
            
            # Route the query through the message router
            response = await self.message_router.route_query(
                query=update.message.text,
                user_id=update.effective_user.id,
                username=update.effective_user.first_name
            )
            
            await self._send_response(update, response)
            
        except Exception as e:
            await self.error_handler.handle_query_error(update, e)
    
    async def _send_response(self, update: Update, response: dict) -> None:
        """Send formatted response to user."""
        formatted_response = self.response_formatter.format_response(response)
        
        # Handle long messages
        if len(formatted_response.text) > self.config.max_message_length:
            chunks = self.response_formatter.split_long_message(formatted_response.text)
            for chunk in chunks:
                await update.message.reply_text(
                    chunk, 
                    parse_mode=formatted_response.parse_mode
                )
        else:
            await update.message.reply_text(
                formatted_response.text, 
                parse_mode=formatted_response.parse_mode
            )
    
    def run(self) -> None:
        """Start the bot."""
        try:
            logger.info("Starting Telegram Bot...")
            logger.info(f"Bot configured for model: {self.config.model_path}")
            self.app.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")

def main():
    """Main entry point."""
    try:
        # Ensure required directories exist
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        
        config_manager = ConfigManager()
        bot = TelegramBot(config_manager)
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```


## Environment Configuration

**.env.example**

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Database Configuration
DB_PATH=data/database.db
CSV_DATA_PATH=data/dftotal.csv

# Model Configuration
MODEL_PATH=models/llama-2-7b-chat.Q4_K_M.gguf
MODEL_N_CTX=1024
MODEL_TEMPERATURE=0.1

# Bot Settings
MAX_MESSAGE_LENGTH=4000
RESPONSE_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Admin Configuration (comma-separated user IDs)
ADMIN_USER_IDS=123456789,987654321