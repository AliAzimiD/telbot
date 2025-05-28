from typing import Dict, Any
from core.llm_pipeline import ModelType

class ModelConfigurations:
    """Centralized model configurations."""
    
    CONFIGS = {
        'llama_local': {
            'type': ModelType.LLAMA_LOCAL,
            'config': {
                'model_path': '/root/models/llama-2-7b-chat.Q4_K_M.gguf',
                'n_ctx': 1024,
                'n_batch': 256,
                'temperature': 0.1,
                'n_gpu_layers': 0,
                'max_tokens': 512,
                'n_threads': 4,
                'f16_kv': True
            }
        },
        'openai_gpt3': {
            'type': ModelType.OPENAI_GPT,
            'config': {
                'api_key': '${OPENAI_API_KEY}',
                'model': 'gpt-3.5-turbo',
                'max_tokens': 512,
                'temperature': 0.1
            }
        },
        'huggingface_phi3': {
            'type': ModelType.HUGGINGFACE,
            'config': {
                'model_id': 'microsoft/Phi-3-mini-4k-instruct',
                'device_map': 'cpu',
                'max_tokens': 512,
                'temperature': 0.1
            }
        }
    }
    
    @classmethod
    def get_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        if model_name not in cls.CONFIGS:
            raise ValueError(f"Unknown model: {model_name}")
        return cls.CONFIGS[model_name]
    
    @classmethod
    def list_models(cls) -> List[str]:
        """List all available model configurations."""
        return list(cls.CONFIGS.keys())