import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import psutil

from core.llm_manager import LLMManager
from core.database_manager import DatabaseManager
from utils.query_validator import QueryValidator
from utils.response_cache import ResponseCache

logger = logging.getLogger(__name__)

class BotController:
    """Main business logic controller."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.database_manager = DatabaseManager(config_manager)
        self.llm_manager = LLMManager(config_manager)
        self.query_validator = QueryValidator(config_manager)
        self.response_cache = ResponseCache(config_manager)
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all components."""
        try:
            # Initialize LLM
            if not self.llm_manager.initialize():
                raise RuntimeError("Failed to initialize LLM")
            
            # Setup SQL agent with database
            self.llm_manager.setup_sql_agent(self.database_manager.get_langchain_db())
            
            logger.info("Bot controller initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot controller: {e}")
            raise
    
    async def process_user_query(self, query: str, user_id: int) -> str:
        """Process user query with validation and caching."""
        try:
            # Validate query
            validation_result = self.query_validator.validate_query(query)
            if not validation_result.is_valid:
                return f"Invalid query: {validation_result.error_message}"
            
            # Check cache first
            cached_response = self.response_cache.get_cached_response(query)
            if cached_response:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_response
            
            # Try simple queries first (faster)
            simple_response = await self._handle_simple_queries(query)
            if simple_response:
                self.response_cache.cache_response(query, simple_response)
                return simple_response
            
            # Process with LLM agent
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.llm_manager.query_with_agent, 
                query
            )
            
            # Cache the response
            self.response_cache.cache_response(query, response)
            
            # Log the query
            self._log_query(user_id, query, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error while processing your query: {str(e)}"
    
    async def _handle_simple_queries(self, query: str) -> Optional[str]:
        """Handle simple queries with direct SQL."""
        query_lower = query.lower().strip()
        
        try:
            # Row count queries
            if any(phrase in query_lower for phrase in ['how many rows', 'row count', 'total rows']):
                count = self.database_manager.execute_query("SELECT COUNT(*) FROM dftotal")[^3_0][^3_0]
                return f"The dataset contains **{count:,}** rows."
            
            # Column info queries
            if any(phrase in query_lower for phrase in ['what columns', 'column names', 'show columns']):
                table_info = self.database_manager.get_table_info()
                columns = [col['name'] for col in table_info['columns']]
                return f"**Dataset Columns ({len(columns)}):**\n" + "\n".join([f"• {col}" for col in columns])
            
            # Table structure
            if any(phrase in query_lower for phrase in ['table structure', 'describe table', 'table info']):
                table_info = self.database_manager.get_table_info()
                info_lines = [f"**Table: {table_info['table_name']}**"]
                info_lines.append(f"• Rows: {table_info['row_count']:,}")
                info_lines.append(f"• Columns: {table_info['column_count']}")
                info_lines.append("\n**Column Details:**")
                
                for col in table_info['columns']:
                    info_lines.append(f"• **{col['name']}** ({col['type']})")
                
                return "\n".join(info_lines)
            
            return None
            
        except Exception as e:
            logger.error(f"Simple query error: {e}")
            return None
    
    def _log_query(self, user_id: int, query: str, response: str) -> None:
        """Log query and response for analytics."""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'query': query[:100],  # Truncate for privacy
                'response_length': len(response),
                'model_used': 'local_llama'
            }
            logger.info(f"Query processed: {log_entry}")
        except Exception as e:
            logger.error(f"Error logging query: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'llm': self.llm_manager.get_status(),
            'database': self.database_manager.get_statistics(),
            'cache': self.response_cache.get_stats(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_admin_statistics(self) -> Dict[str, Any]:
        """Get detailed admin statistics."""
        try:
            # System resource info
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Database stats
            db_stats = self.database_manager.get_statistics()
            
            # Cache stats
            cache_stats = self.response_cache.get_stats()
            
            return {
                'database': db_stats,
                'cache_hits': cache_stats.get('hits', 0),
                'cache_misses': cache_stats.get('misses', 0),
                'memory_usage': round(memory.percent, 1),
                'cpu_usage': round(cpu_percent, 1),
                'uptime': 'N/A',  # Could implement uptime tracking
                'total_queries': cache_stats.get('total_queries', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting admin statistics: {e}")
            return {}
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return self.config.is_admin(user_id)