import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_path = os.getenv('DB_PATH', 'data/dftotal.db')
        self.csv_path = os.getenv('CSV_DATA_PATH', 'data/dftotal.csv')
        self.engine = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database from CSV if needed"""
        try:
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Create SQLAlchemy engine
            self.engine = create_engine(f'sqlite:///{self.db_path}')
            
            # Load CSV data if database is empty or doesn't exist
            if not os.path.exists(self.db_path) or self._is_database_empty():
                self._load_csv_to_database()
                
            logger.info(f"Database initialized at: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _is_database_empty(self) -> bool:
        """Check if database is empty"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = result.fetchall()
                return len(tables) == 0
        except:
            return True
    
    def _load_csv_to_database(self):
        """Load CSV file into SQLite database"""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(self.csv_path)
            
            # Convert to appropriate data types
            df = df.convert_dtypes()
            
            # Load into SQLite
            df.to_sql('dftotal', self.engine, if_exists='replace', index=False)
            
            logger.info(f"Loaded {len(df)} rows from {self.csv_path} to database")
            
        except Exception as e:
            logger.error(f"Error loading CSV to database: {e}")
            raise
    
    def get_engine(self):
        """Get SQLAlchemy engine"""
        return self.engine
    
    def get_langchain_db(self):
        """Get LangChain SQLDatabase wrapper"""
        return SQLDatabase.from_uri(f'sqlite:///{self.db_path}')
    
    def execute_query(self, query: str):
        """Execute raw SQL query"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return result.fetchall()
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def get_table_info(self) -> dict:
        """Get information about the main table"""
        try:
            with self.engine.connect() as conn:
                # Get row count
                count_result = conn.execute(text("SELECT COUNT(*) FROM dftotal"))
                row_count = count_result.scalar()
                
                # Get column info
                columns_result = conn.execute(text("PRAGMA table_info(dftotal)"))
                columns = [{"name": row[^2_1], "type": row[^2_2], "nullable": not row[^2_3]} 
                          for row in columns_result]
                
                return {
                    "row_count": row_count,
                    "columns": columns,
                    "table_name": "dftotal"
                }
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {}
    
    def is_ready(self) -> bool:
        """Check if database is ready"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM dftotal LIMIT 1"))
                return True
        except:
            return False