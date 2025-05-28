
import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError
from langchain_community.utilities import SQLDatabase

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations and connections."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self._engine: Optional[Engine] = None
        self._langchain_db: Optional[SQLDatabase] = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database from CSV if needed."""
        try:
            # Create database directory
            os.makedirs(os.path.dirname(self.config.db_path), exist_ok=True)
            
            # Create SQLAlchemy engine
            self._engine = create_engine(f'sqlite:///{self.config.db_path}')
            
            # Load CSV data if database is empty or doesn't exist
            if not os.path.exists(self.config.db_path) or self._is_database_empty():
                self._load_csv_to_database()
            
            # Initialize LangChain database wrapper
            self._langchain_db = SQLDatabase.from_uri(f'sqlite:///{self.config.db_path}')
            
            logger.info(f"Database initialized at: {self.config.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _is_database_empty(self) -> bool:
        """Check if database is empty."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = result.fetchall()
                return len(tables) == 0
        except SQLAlchemyError:
            return True
    
    def _load_csv_to_database(self) -> None:
        """Load CSV file into SQLite database."""
        if not os.path.exists(self.config.csv_path):
            logger.warning(f"CSV file not found: {self.config.csv_path}")
            # Create empty table for now
            self._create_empty_table()
            return
        
        try:
            # Read CSV file
            df = pd.read_csv(self.config.csv_path)
            
            # Convert to appropriate data types
            df = df.convert_dtypes()
            
            # Load into SQLite
            df.to_sql('dftotal', self._engine, if_exists='replace', index=False)
            
            logger.info(f"Loaded {len(df)} rows from {self.config.csv_path} to database")
            
        except Exception as e:
            logger.error(f"Error loading CSV to database: {e}")
            raise
    
    def _create_empty_table(self) -> None:
        """Create an empty table structure."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS dftotal (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            logger.info("Created empty dftotal table")
        except SQLAlchemyError as e:
            logger.error(f"Error creating empty table: {e}")
    
    def execute_query(self, query: str) -> List[tuple]:
        """Execute raw SQL query."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query))
                return result.fetchall()
        except SQLAlchemyError as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about the main table."""
        try:
            with self._engine.connect() as conn:
                # Get row count
                count_result = conn.execute(text("SELECT COUNT(*) FROM dftotal"))
                row_count = count_result.scalar()
                
                # Get column info
                columns_result = conn.execute(text("PRAGMA table_info(dftotal)"))
                columns = [
                    {
                        "name": row[^3_1], 
                        "type": row[^3_2], 
                        "nullable": not row[^3_3],
                        "primary_key": bool(row[^3_5])
                    } 
                    for row in columns_result
                ]
                
                return {
                    "table_name": "dftotal",
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": columns
                }
        except SQLAlchemyError as e:
            logger.error(f"Error getting table info: {e}")
            return {}
    
    def get_sample_data(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from the table."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM dftotal LIMIT {limit}"))
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Error getting sample data: {e}")
            return []
    
    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine."""
        return self._engine
    
    def get_langchain_db(self) -> SQLDatabase:
        """Get LangChain SQLDatabase wrapper."""
        return self._langchain_db
    
    def is_ready(self) -> bool:
        """Check if database is ready."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM dftotal LIMIT 1"))
                return True
        except SQLAlchemyError:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            table_info = self.get_table_info()
            file_size = os.path.getsize(self.config.db_path) if os.path.exists(self.config.db_path) else 0
            
            return {
                "database_path": self.config.db_path,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "table_info": table_info,
                "is_ready": self.is_ready()
            }
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {}