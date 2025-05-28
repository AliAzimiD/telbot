import os
import logging
from langchain_community.llms import LlamaCpp

logger = logging.getLogger(__name__)

class ModelLoader:
    def __init__(self):
        self.model_cache = {}
    
    def load_llama_model(self, model_path: str) -> LlamaCpp:
        """Load LLaMA model with optimized settings for Ubuntu server"""
        if model_path in self.model_cache:
            logger.info("Using cached model")
            return self.model_cache[model_path]
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            # Get model configuration from environment
            n_ctx = int(os.getenv('MODEL_N_CTX', 1024))
            temperature = float(os.getenv('MODEL_TEMPERATURE', 0.1))
            
            logger.info(f"Loading LLaMA model from: {model_path}")
            
            model = LlamaCpp(
                model_path=model_path,
                n_ctx=n_ctx,  # Context length (1024 for 8GB RAM)
                n_batch=256,  # Batch size for 4-core CPU
                temperature=temperature,  # Low temperature for consistent responses
                n_gpu_layers=0,  # CPU-only (no GPU)
                verbose=False,  # Quiet operation
                max_tokens=512,  # Limit response length
                n_threads=4,  # Use all 4 CPU cores
                f16_kv=True,  # Use half precision for key-value cache
            )
            
            # Cache the model
            self.model_cache[model_path] = model
            logger.info("LLaMA model loaded successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def get_model_info(self, model_path: str) -> dict:
        """Get information about the model"""
        try:
            import os
            if not os.path.exists(model_path):
                return {"error": "Model file not found"}
            
            file_size = os.path.getsize(model_path) / (1024**3)  # GB
            return {
                "path": model_path,
                "size_gb": round(file_size, 2),
                "exists": True,
                "type": "GGUF" if model_path.endswith('.gguf') else "Unknown"
            }
        except Exception as e:
            return {"error": str(e)}