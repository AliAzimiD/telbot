from typing import Dict, Any, Optional
from core.llm_pipeline import LLMProvider, ModelType
from core.providers.llama_provider import LlamaLocalProvider
from core.providers.openai_provider import OpenAIProvider
from core.providers.huggingface_provider import HuggingFaceProvider

class ModelFactory:
    """Factory for creating LLM providers."""
    
    _registry = {
        ModelType.LLAMA_LOCAL: LlamaLocalProvider,
        ModelType.OPENAI_GPT: OpenAIProvider,
        ModelType.HUGGINGFACE: HuggingFaceProvider,
    }
    
    @classmethod
    def create_provider(cls, model_type: ModelType, config: Dict[str, Any]) -> Optional[LLMProvider]:
        """Create and initialize a provider."""
        if model_type not in cls._registry:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        provider_class = cls._registry[model_type]
        provider = provider_class()
        
        if provider.initialize(config):
            return provider
        else:
            return None
    
    @classmethod
    def register_provider(cls, model_type: ModelType, provider_class):
        """Register a new provider type."""
        cls._registry[model_type] = provider_class
    
    @classmethod
    def list_supported_types(cls) -> List[ModelType]:
        """List all supported model types."""
        return list(cls._registry.keys())