import os
from typing import Dict, Any
from langchain_community.llms import LlamaCpp
from core.llm_pipeline import LLMProvider, LLMRequest, LLMResponse, ModelType

class LlamaLocalProvider(LLMProvider):
    """Local LLaMA model provider."""
    
    def __init__(self):
        self.llm: Optional[LlamaCpp] = None
        self.model_info = {}
        self.is_initialized = False
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize local LLaMA model."""
        try:
            model_path = config.get('model_path')
            if not model_path or not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found: {model_path}")
            
            self.llm = LlamaCpp(
                model_path=model_path,
                n_ctx=config.get('n_ctx', 1024),
                n_batch=config.get('n_batch', 256),
                temperature=config.get('temperature', 0.1),
                n_gpu_layers=config.get('n_gpu_layers', 0),
                verbose=config.get('verbose', False),
                max_tokens=config.get('max_tokens', 512),
                n_threads=config.get('n_threads', 4),
                f16_kv=config.get('f16_kv', True)
            )
            
            self.model_info = {
                'name': 'llama_local',
                'type': ModelType.LLAMA_LOCAL.value,
                'path': model_path,
                'context_length': config.get('n_ctx', 1024),
                'capabilities': ['text_generation', 'qa', 'analysis']
            }
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLaMA: {e}")
            return False
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using local LLaMA."""
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized")
        
        try:
            # Prepare prompt
            prompt = request.query
            if request.context:
                prompt = f"Context: {request.context}\n\nQuestion: {request.query}"
            
            # Generate response
            response_text = self.llm.invoke(prompt)
            
            return LLMResponse(
                content=response_text,
                model_name=self.model_info['name'],
                metadata={'provider': 'llama_local'}
            )
            
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")
    
    def is_available(self) -> bool:
        """Check if model is available."""
        return self.is_initialized and self.llm is not None
    
    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return self.model_info
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.llm = None
        self.is_initialized = False