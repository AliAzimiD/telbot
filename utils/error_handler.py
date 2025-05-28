import logging
import traceback
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the bot."""
    
    def __init__(self, config_manager):
        self.config = config_manager
    
    async def handle_error(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
        """Global error handler for the bot."""
        error = context.error
        
        # Log the error with full traceback
        logger.error(f"Bot error: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Try to notify the user if possible
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "🔧 I encountered an unexpected error. Please try again or contact support.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to send error message to user: {e}")
    
    async def handle_command_error(self, update: Update, error: Exception, command: str) -> None:
        """Handle errors in command processing."""
        logger.error(f"Error in /{command} command: {error}")
        
        error_messages = {
            "start": "Failed to process start command. Please try again.",
            "help": "Failed to load help information. Please try again.",
            "status": "Failed to get bot status. Please check system health.",
            "stats": "Failed to get statistics. Please contact administrator."
        }
        
        message = error_messages.get(command, f"Failed to process /{command} command.")
        
        try:
            await update.message.reply_text(f"❌ {message}")
        except Exception as e:
            logger.error(f"Failed to send command error message: {e}")
    
    async def handle_query_error(self, update: Update, error: Exception) -> None:
        """Handle errors in query processing."""
        logger.error(f"Query processing error: {error}")
        
        # Provide specific error messages based on error type
        if "timeout" in str(error).lower():
            error_msg = "⏱️ Query timeout. Please try a simpler question."
        elif "database" in str(error).lower():
            error_msg = "💾 Database temporarily unavailable. Please try again."
        elif "model" in str(error).lower() or "llm" in str(error).lower():
            error_msg = "🤖 AI model temporarily unavailable. Please try again."
        else:
            error_msg = "🔧 Unable to process your query. Please rephrase and try again."
        
        try:
            await update.message.reply_text(error_msg)
        except Exception as e:
            logger.error(f"Failed to send query error message: {e}")
    
    def log_user_action(self, user_id: int, action: str, details: str = "") -> None:
        """Log user actions for monitoring."""
        try:
            log_message = f"User {user_id} - {action}"
            if details:
                log_message += f" - {details}"
            
            logger.info(log_message)
        except Exception as e:
            logger.error(f"Failed to log user action: {e}")