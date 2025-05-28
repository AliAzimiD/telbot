import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageRouter:
    """Routes messages to appropriate handlers."""
    
    def __init__(self, bot_controller):
        self.bot_controller = bot_controller
    
    async def route_start_command(self, user) -> Dict[str, Any]:
        """Route /start command."""
        username = user.first_name or "User"
        
        message = f"""Welcome {username} to Local Data Analysis Bot! 🤖

I'm powered by a local LLaMA model and can help you analyze your dataset using natural language queries.

**Quick Start:**
Just ask me questions about your data!
• Try: "How many rows are in the dataset?"
• Or: "What are the column names?"

**Available Commands:**
/help - Show detailed help
/status - Check bot and model status  

**Privacy Note:**
All processing happens locally on the server - your data never leaves!

Ready to analyze your data? Ask me anything! 🚀"""
        
        return {
            "text": message,
            "parse_mode": "Markdown",
            "type": "start_response"
        }
    
    async def route_help_command(self) -> Dict[str, Any]:
        """Route /help command."""
        help_text = """**🔍 How to use this bot**

**Simple Queries (Fast Response):**
• "How many rows?" 
• "What columns are available?"
• "Describe the table structure"

**Complex Analysis (Uses Local AI):**
• "What's the average age by department?"
• "Show gender distribution" 
• "Count employees by education level"
• "Find patterns in the data"

**Tips for Better Results:**
• Be specific in your questions
• Use column names if you know them  
• Ask one question at a time
• Try rephrasing if results aren't clear

**System Info:**
🖥️ **Server:** Ubuntu 22.04, 8GB RAM, 4 cores
⚡ **Mode:** Local processing (CPU-only)
🔒 **Privacy:** All data stays on server
🤖 **Model:** Local LLaMA (no internet required)

**Commands:**
/start - Welcome message
/help - This help message  
/status - Bot and model status

**Need admin access?** Contact your system administrator."""
        
        return {
            "text": help_text,
            "parse_mode": "Markdown",
            "type": "help_response"
        }
    
    async def route_status_command(self) -> Dict[str, Any]:
        """Route /status command."""
        try:
            status = await self.bot_controller.get_system_status()
            
            status_text = f"""**🔍 Bot Status Report**

**Model Status:**
{'✅ Model loaded' if status['llm']['llm_loaded'] else '❌ Model not loaded'}
{'✅ Agent ready' if status['llm']['sql_agent_ready'] else '❌ Agent not ready'}
📍 Model path: `{status['llm']['model_path']}`

**Database Status:**
{'✅ Database ready' if status['database']['is_ready'] else '❌ Database not ready'}
📊 Rows: {status['database']['table_info'].get('row_count', 'Unknown')}
🗂️ Columns: {status['database']['table_info'].get('column_count', 'Unknown')}

**System Info:**
🖥️ Server: Ubuntu 22.04
⚡ Mode: Local processing (CPU-only)
🔒 Privacy: All data stays on server

**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            return {
                "text": status_text,
                "parse_mode": "Markdown",
                "type": "status_response"
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "text": f"❌ **Status Check Failed**\n\nError: {str(e)}",
                "parse_mode": "Markdown",
                "type": "error_response"
            }
    
    async def route_stats_command(self) -> Dict[str, Any]:
        """Route /stats command (admin only)."""
        try:
            stats = await self.bot_controller.get_admin_statistics()
            
            stats_text = f"""**📊 Admin Statistics**

**Database Info:**
• File size: {stats['database']['file_size_mb']} MB
• Path: `{stats['database']['database_path']}`

**Query Performance:**
• Cache hits: {stats.get('cache_hits', 'N/A')}
• Average response time: {stats.get('avg_response_time', 'N/A')}s

**System Resources:**
• Memory usage: {stats.get('memory_usage', 'N/A')}%
• CPU usage: {stats.get('cpu_usage', 'N/A')}%

**Bot Activity:**
• Uptime: {stats.get('uptime', 'N/A')}
• Total queries processed: {stats.get('total_queries', 'N/A')}

**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            return {
                "text": stats_text,
                "parse_mode": "Markdown",
                "type": "stats_response"
            }
            
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {
                "text": f"❌ **Stats Error**\n\nError: {str(e)}",
                "parse_mode": "Markdown",
                "type": "error_response"
            }
    
    async def route_query(self, query: str, user_id: int, username: str) -> Dict[str, Any]:
        """Route user query to appropriate handler."""
        try:
            # Log the query
            logger.info(f"Query from {username} (ID: {user_id}): {query}")
            
            # Process the query through bot controller
            response_text = await self.bot_controller.process_user_query(query, user_id)
            
            return {
                "text": response_text,
                "parse_mode": "Markdown",
                "type": "query_response",
                "user_id": user_id,
                "username": username
            }
            
        except Exception as e:
            logger.error(f"Error routing query: {e}")
            return {
                "text": f"Sorry {username}, I encountered an error processing your query. Please try again.",
                "parse_mode": "Markdown",
                "type": "error_response"
            }