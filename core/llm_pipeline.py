from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import time
import logging
from langchain_core.language_models.llms import LLM
from langchain_core.runnables import Runnable

logger = logging.getLogger(__name__)

@dataclass
class LLMRequest:
    """Standardized input for all LLM operations."""
    query: str
    context: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = None

@dataclass
class LLMResponse:
    """Standardized output from all LLM operations."""
    content: str
    model_name: str
    tokens_used: Optional[int] = None
    response_time: float = 0.0
    metadata: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None

class ModelType(Enum):
    """Supported model types."""
    LLAMA_LOCAL = "llama_local"
    LLAMA_GGUF = "llama_gguf"
    OPENAI_GPT = "openai_gpt"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"

class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the model with given configuration."""
        pass
    
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response for the given request."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available and ready."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get model information and capabilities."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass

class LLMPipeline:
    """Main pipeline for processing requests through various LLMs."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.providers: Dict[str, LLMProvider] = {}
        self.active_provider: Optional[str] = None
        self.fallback_chain: List[str] = []
        
    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """Register a new LLM provider."""
        self.providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")
    
    def set_active_provider(self, name: str) -> bool:
        """Set the active LLM provider."""
        if name not in self.providers:
            logger.error(f"Provider {name} not found")
            return False
        
        if not self.providers[name].is_available():
            logger.error(f"Provider {name} is not available")
            return False
        
        self.active_provider = name
        logger.info(f"Active provider set to: {name}")
        return True
    
    def set_fallback_chain(self, providers: List[str]) -> None:
        """Set fallback chain for when primary provider fails."""
        self.fallback_chain = providers
        logger.info(f"Fallback chain set: {providers}")
    
    async def process(self, request: LLMRequest) -> LLMResponse:
        """Process request through active provider with fallback."""
        # Try active provider first
        if self.active_provider:
            try:
                return await self._process_with_provider(self.active_provider, request)
            except Exception as e:
                logger.warning(f"Active provider {self.active_provider} failed: {e}")
        
        # Try fallback chain
        for provider_name in self.fallback_chain:
            if provider_name in self.providers:
                try:
                    logger.info(f"Trying fallback provider: {provider_name}")
                    return await self._process_with_provider(provider_name, request)
                except Exception as e:
                    logger.warning(f"Fallback provider {provider_name} failed: {e}")
                    continue
        
        # All providers failed
        return LLMResponse(
            content="All LLM providers failed",
            model_name="none",
            success=False,
            error_message="All configured providers are unavailable"
        )
    
    async def _process_with_provider(self, provider_name: str, request: LLMRequest) -> LLMResponse:
        """Process request with specific provider."""
        start_time = time.time()
        provider = self.providers[provider_name]
        
        try:
            response = provider.generate(request)
            response.response_time = time.time() - start_time
            return response
        except Exception as e:
            return LLMResponse(
                content="",
                model_name=provider_name,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )