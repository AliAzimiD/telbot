import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from utils.text_processing import format_help_message
from commands.query_handler import LocalQueryHandler

logger = logging.getLogger(__name__)

class BasicCommands:
    def __init__(self):
        self.query_handler = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        username = update.effective_user.first_name
        welcome_msg = f"""Welcome {username} to Local Data Analysis Bot! 🤖

I'm powered by a local LLaMA model and can help you analyze your dataset using natural language queries.

**Quick Start:**
Just ask me questions about your data!
• Try: "How many rows are in the dataset?"
• Or: "What are the column names?"

**Available Commands:**
/help - Show detailed help
/status - Check bot and model status  
/info - Dataset information

**Privacy Note:**
All processing happens locally on the server - your data never leaves!

Ready to analyze your data? Ask me anything! 🚀"""
        
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_msg = format_help_message()
        await update.message.reply_text(help_msg, parse_mode="Markdown")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            # Get query handler if not initialized
            if not self.query_handler:
                self.query_handler = LocalQueryHandler()
            
            status = self.query_handler.get_status()
            
            status_msg = f"""**🔍 Bot Status Report**

**Model Status:**
{'✅ Model loaded' if status['llm_loaded'] else '❌ Model not loaded'}
{'✅ Agent ready' if status['agent_ready'] else '❌ Agent not ready'}
📍 Model path: {status['model_path']}

**Database Status:**
{'✅ Database ready' if status['database_ready'] else '❌ Database not ready'}

**System Info:**
🖥️ Server: Ubuntu 22.04
⚡ Mode: Local processing (CPU-only)
🔒 Privacy: All data stays on server

**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            status_msg = f"❌ **Status Check Failed**\n\nIssue: {str(e)}\n\nSuggestion: Try restarting the bot or check model configuration."
        
        await update.message.reply_text(status_msg, parse_mode="Markdown")
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command - show dataset information"""
        try:
            if not self.query_handler:
                self.query_handler = LocalQueryHandler()
            
            # Get basic dataset info
            simple_queries = [
                "How many rows are in the dataset?",
                "What columns are available?"
            ]
            
            info_parts = ["📊 **Dataset Information**"]
            
            for query in simple_queries:
                try:
                    result = await self.query_handler._handle_simple_queries(query)
                    if result:
                        info_parts.append(result)
                except Exception as e:
                    info_parts.append(f"Error getting info: {e}")
            
            info_msg = "\n\n".join(info_parts)
            
        except Exception as e:
            logger.error(f"Error getting dataset info: {e}")
            info_msg = f"❌ Unable to retrieve dataset information: {str(e)}"
        
        await update.message.reply_text(info_msg, parse_mode="Markdown")