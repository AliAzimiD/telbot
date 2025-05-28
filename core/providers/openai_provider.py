from typing import Dict, Any
import openai
from core.llm_pipeline import LLMProvider, LLMRequest, LLMResponse, ModelType

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self):
        self.client = None
        self.model_name = "gpt-3.5-turbo"
        self.is_initialized = False
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize OpenAI client."""
        try:
            api_key = config.get('api_key')
            if not api_key:
                raise ValueError("OpenAI API key required")
            
            self.client = openai.OpenAI(api_key=api_key)
            self.model_name = config.get('model', 'gpt-3.5-turbo')
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            return False
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI."""
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized")
        
        try:
            messages = [{"role": "user", "content": request.query}]
            if request.context:
                messages.insert(0, {"role": "system", "content": request.context})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=request.max_tokens or 512,
                temperature=request.temperature or 0.1
            )
            
            return LLMResponse(
                content=response.choices[^4_0].message.content,
                model_name=self.model_name,
                tokens_used=response.usage.total_tokens,
                metadata={'provider': 'openai'}
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self.is_initialized and self.client is not None
    
    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'name': self.model_name,
            'type': ModelType.OPENAI_GPT.value,
            'capabilities': ['text_generation', 'chat', 'analysis', 'coding']
        }
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.client = None
        self.is_initialized = False