import re
import logging
from typing import NamedTuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of query validation."""
    is_valid: bool
    error_message: str = ""

class QueryValidator:
    """Validates user queries for safety and format."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.max_query_length = 1000
        self.min_query_length = 3
        
        # SQL injection patterns to block
        self.dangerous_patterns = [
            r'\bdrop\s+table\b',
            r'\bdelete\s+from\b',
            r'\btruncate\s+table\b',
            r'\balter\s+table\b',
            r'\bcreate\s+table\b',
            r'\binsert\s+into\b',
            r'\bupdate\s+.*\bset\b',
            r'--',  # SQL comments
            r'/\*.*\*/',  # SQL block comments
            r'\bexec\b',
            r'\bexecute\b',
            r'\bsp_\w+',  # Stored procedures
            r'\bxp_\w+',  # Extended procedures
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
    
    def validate_query(self, query: str) -> ValidationResult:
        """Validate user query comprehensively."""
        if not query:
            return ValidationResult(False, "Query cannot be empty")
        
        query = query.strip()
        
        # Length validation
        if len(query) < self.min_query_length:
            return ValidationResult(False, f"Query too short (minimum {self.min_query_length} characters)")
        
        if len(query) > self.max_query_length:
            return ValidationResult(False, f"Query too long (maximum {self.max_query_length} characters)")
        
        # SQL injection check
        injection_result = self._check_sql_injection(query)
        if not injection_result.is_valid:
            return injection_result
        
        # Character validation (allow international characters)
        if not self._validate_characters(query):
            return ValidationResult(False, "Query contains invalid characters")
        
        # Rate limiting could be added here
        # if not self._check_rate_limit(user_id):
        #     return ValidationResult(False, "Rate limit exceeded")
        
        return ValidationResult(True)
    
    def _check_sql_injection(self, query: str) -> ValidationResult:
        """Check for potential SQL injection patterns."""
        query_lower = query.lower()
        
        for pattern in self.compiled_patterns:
            if pattern.search(query_lower):
                logger.warning(f"Potential SQL injection blocked: {query[:50]}...")
                return ValidationResult(False, "Query contains potentially dangerous SQL patterns")
        
        return ValidationResult(True)
    
    def _validate_characters(self, query: str) -> bool:
        """Validate query characters (allow international text)."""
        # Allow letters, numbers, spaces, and common punctuation
        # This regex allows Unicode characters for international support
        allowed_pattern = re.compile(r'^[\w\s\?\.,!;\-\(\)\[\]"\']+$', re.UNICODE)
        return bool(allowed_pattern.match(query))
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize query for safe processing."""
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove potential harmful characters
        query = re.sub(r'[<>{}]', '', query)
        
        return query
    
    def validate_user_id(self, user_id: int) -> ValidationResult:
        """Validate Telegram user ID."""
        if not isinstance(user_id, int) or user_id <= 0:
            return ValidationResult(False, "Invalid user ID")
        
        return ValidationResult(True)