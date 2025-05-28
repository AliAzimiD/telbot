import logging
from typing import Dict, Any, List, Optional
from core.llm_pipeline import LLMPipeline, LLMRequest, LLMResponse
from core.model_factory import ModelFactory
from config.models_config import ModelConfigurations
from utils.model_benchmarker import ModelBenchmarker

logger = logging.getLogger(__name__)

class EnhancedLLMManager:
    """Enhanced LLM manager with pipeline support."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.pipeline = LLMPipeline(config_manager)
        self.benchmarker = ModelBenchmarker()
        self.loaded_models: Dict[str, Any] = {}
        
    def initialize_models(self, model_names: List[str]) -> Dict[str, bool]:
        """Initialize multiple models."""
        results = {}
        
        for model_name in model_names:
            try:
                config = ModelConfigurations.get_config(model_name)
                provider = ModelFactory.create_provider(
                    config['type'], 
                    config['config']
                )
                
                if provider:
                    self.pipeline.register_provider(model_name, provider)
                    self.loaded_models[model_name] = provider.get_info()
                    results[model_name] = True
                    logger.info(f"Successfully loaded model: {model_name}")
                else:
                    results[model_name] = False
                    logger.error(f"Failed to load model: {model_name}")
                    
            except Exception as e:
                results[model_name] = False
                logger.error(f"Error loading model {model_name}: {e}")
        
        return results
    
    def set_primary_model(self, model_name: str) -> bool:
        """Set the primary model for processing."""
        return self.pipeline.set_active_provider(model_name)
    
    def set_fallback_chain(self, model_names: List[str]) -> None:
        """Set fallback model chain."""
        self.pipeline.set_fallback_chain(model_names)
    
    async def process_query(self, query: str, user_id: int = None, 
                           context: str = None) -> LLMResponse:
        """Process query through the pipeline."""
        request = LLMRequest(
            query=query,
            context=context,
            user_id=user_id
        )
        
        response = await self.pipeline.process(request)
        
        # Log performance metrics
        self.benchmarker.record_response(response)
        
        return response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about all loaded models."""
        return {
            'loaded_models': self.loaded_models,
            'active_model': self.pipeline.active_provider,
            'fallback_chain': self.pipeline.fallback_chain,
            'available_configs': ModelConfigurations.list_models()
        }
    
    def benchmark_models(self, test_queries: List[str]) -> Dict[str, Any]:
        """Benchmark all loaded models."""
        return self.benchmarker.run_benchmark(
            self.pipeline.providers, 
            test_queries
        )
    
    def switch_model(self, model_name: str) -> bool:
        """Dynamically switch to a different model."""
        if model_name not in self.loaded_models:
            # Try to load the model if not already loaded
            result = self.initialize_models([model_name])
            if not result.get(model_name, False):
                return False
        
        return self.set_primary_model(model_name)