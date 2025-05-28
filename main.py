import asyncio
from core.llm_manager import EnhancedLLMManager
from core.config_manager import ConfigManager

async def main():
    # Initialize the system
    config = ConfigManager()
    llm_manager = EnhancedLLMManager(config)
    
    # Load multiple models
    models_to_load = ['llama_local', 'openai_gpt3']
    load_results = llm_manager.initialize_models(models_to_load)
    print(f"Model loading results: {load_results}")
    
    # Set primary model and fallback
    llm_manager.set_primary_model('llama_local')
    llm_manager.set_fallback_chain(['openai_gpt3'])
    
    # Process queries
    test_queries = [
        "How many rows are in the dataset?",
        "What is the average age by department?",
        "Explain the data distribution"
    ]
    
    for query in test_queries:
        response = await llm_manager.process_query(query)
        print(f"Query: {query}")
        print(f"Response: {response.content}")
        print(f"Model: {response.model_name}")
        print(f"Time: {response.response_time:.2f}s")
        print("-" * 50)
    
    # Benchmark models
    benchmark_results = llm_manager.benchmark_models(test_queries)
    for model_name, result in benchmark_results.items():
        print(f"{model_name}: {result.avg_response_time:.2f}s avg, "
              f"{result.success_rate:.1%} success rate")
    
    # Switch models dynamically
    if llm_manager.switch_model('openai_gpt3'):
        print("Switched to OpenAI model")
        response = await llm_manager.process_query("Test with new model")
        print(f"New model response: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())