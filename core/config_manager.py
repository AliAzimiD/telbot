import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pathlib import Path

logger = logging.getLogger(__name__)

class BotConfig(BaseModel):
    """Bot configuration model with validation."""
    telegram_token: str = Field(..., min_length=40)
    model_path: str = Field(..., min_length=1)
    db_path: str = Field(default="data/database.db")
    csv_path: str = Field(default="data/dftotal.csv")
    max_message_length: int = Field(default=4000, gt=0)
    response_timeout: int = Field(default=30, gt=0)
    model_n_ctx: int = Field(default=1024, gt=0)
    model_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/bot.log")
    admin_user_ids: list = Field(default_factory=list)

class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, env_file: str = ".env"):
        load_dotenv(env_file)
        self._config = self._load_config()
        self._validate_paths()
        
    def _load_config(self) -> BotConfig:
        """Load and validate configuration from environment."""
        try:
            # Parse admin user IDs
            admin_ids_str = os.getenv('ADMIN_USER_IDS', '')
            admin_ids = [int(uid.strip()) for uid in admin_ids_str.split(',') if uid.strip().isdigit()]
            
            config_data = {
                'telegram_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'model_path': os.getenv('MODEL_PATH'),
                'db_path': os.getenv('DB_PATH', 'data/database.db'),
                'csv_path': os.getenv('CSV_DATA_PATH', 'data/dftotal.csv'),
                'max_message_length': int(os.getenv('MAX_MESSAGE_LENGTH', 4000)),
                'response_timeout': int(os.getenv('RESPONSE_TIMEOUT', 30)),
                'model_n_ctx': int(os.getenv('MODEL_N_CTX', 1024)),
                'model_temperature': float(os.getenv('MODEL_TEMPERATURE', 0.1)),
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'log_file': os.getenv('LOG_FILE', 'logs/bot.log'),
                'admin_user_ids': admin_ids
            }
            
            return BotConfig(**config_data)
            
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            raise
    
    def _validate_paths(self) -> None:
        """Validate required paths exist."""
        # Create directories if they don't exist
        Path(os.path.dirname(self._config.db_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(self._config.log_file)).mkdir(parents=True, exist_ok=True)
        
        # Check model file exists
        if not os.path.exists(self._config.model_path):
            logger.warning(f"Model file not found: {self._config.model_path}")
    
    @property
    def telegram_token(self) -> str:
        return self._config.telegram_token
    
    @property
    def model_path(self) -> str:
        return self._config.model_path
    
    @property
    def db_path(self) -> str:
        return self._config.db_path
    
    @property
    def csv_path(self) -> str:
        return self._config.csv_path
    
    @property
    def max_message_length(self) -> int:
        return self._config.max_message_length
    
    @property
    def response_timeout(self) -> int:
        return self._config.response_timeout
    
    @property
    def model_config(self) -> Dict[str, Any]:
        """Get model configuration parameters."""
        return {
            'model_path': self._config.model_path,
            'n_ctx': self._config.model_n_ctx,
            'temperature': self._config.model_temperature
        }
    
    @property
    def admin_user_ids(self) -> list:
        return self._config.admin_user_ids
    
    def get_config(self) -> BotConfig:
        """Get the full configuration object."""
        return self._config
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in self._config.admin_user_ids