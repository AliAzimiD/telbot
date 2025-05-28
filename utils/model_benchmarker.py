import time
import statistics
from typing import Dict, Any, List
from dataclasses import dataclass
from core.llm_pipeline import LLMProvider, LLMRequest

@dataclass
class BenchmarkResult:
    model_name: str
    avg_response_time: float
    success_rate: float
    total_queries: int
    tokens_per_second: float = 0.0

class ModelBenchmarker:
    """Benchmark and compare different models."""
    
    def __init__(self):
        self.results_history: List[BenchmarkResult] = []
    
    def benchmark_single_model(self, provider: LLMProvider, 
                              test_queries: List[str]) -> BenchmarkResult:
        """Benchmark a single model."""
        response_times = []
        successes = 0
        total_tokens = 0
        
        for query in test_queries:
            request = LLMRequest(query=query)
            start_time = time.time()
            
            try:
                response = provider.generate(request)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.success:
                    successes += 1
                    if response.tokens_used:
                        total_tokens += response.tokens_used
                        
            except Exception as e:
                response_times.append(float('inf'))
        
        avg_response_time = statistics.mean([t for t in response_times if t != float('inf')])
        success_rate = successes / len(test_queries)
        tokens_per_second = total_tokens / sum(response_times) if response_times else 0
        
        return BenchmarkResult(
            model_name=provider.get_info()['name'],
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            total_queries=len(test_queries),
            tokens_per_second=tokens_per_second
        )
    
    def run_benchmark(self, providers: Dict[str, LLMProvider], 
                     test_queries: List[str]) -> Dict[str, BenchmarkResult]:
        """Run benchmark on multiple models."""
        results = {}
        
        for name, provider in providers.items():
            if provider.is_available():
                results[name] = self.benchmark_single_model(provider, test_queries)
        
        return results
    
    def record_response(self, response) -> None:
        """Record individual response for ongoing monitoring."""
        # Implementation for tracking ongoing performance
        pass