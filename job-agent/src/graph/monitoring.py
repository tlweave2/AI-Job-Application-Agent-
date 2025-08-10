from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class NodePerformance:
    node_name: str
    execution_count: int
    total_time: float
    avg_time: float
    success_rate: float
    last_execution: float

class PerformanceMonitor:
    """Monitor graph performance and bottlenecks"""
    
    def __init__(self):
        self.node_stats = {}
        self.execution_history = []
    
    def record_node_execution(self, node_name: str, execution_time: float, success: bool):
        """Record node execution statistics"""
        
        if node_name not in self.node_stats:
            self.node_stats[node_name] = {
                'execution_count': 0,
                'total_time': 0.0,
                'success_count': 0,
                'last_execution': 0.0
            }
        
        stats = self.node_stats[node_name]
        stats['execution_count'] += 1
        stats['total_time'] += execution_time
        stats['last_execution'] = time.time()
        
        if success:
            stats['success_count'] += 1
    
    def get_performance_report(self) -> Dict[str, NodePerformance]:
        """Generate performance report"""
        
        report = {}
        for node_name, stats in self.node_stats.items():
            avg_time = stats['total_time'] / stats['execution_count']
            success_rate = stats['success_count'] / stats['execution_count']
            
            report[node_name] = NodePerformance(
                node_name=node_name,
                execution_count=stats['execution_count'],
                total_time=stats['total_time'],
                avg_time=avg_time,
                success_rate=success_rate,
                last_execution=stats['last_execution']
            )
        
        return report
    
    def identify_bottlenecks(self) -> List[str]:
        """Identify performance bottlenecks"""
        
        report = self.get_performance_report()
        bottlenecks = []
        
        # Find nodes with high execution time
        for node_name, perf in report.items():
            if perf.avg_time > 5.0:  # More than 5 seconds average
                bottlenecks.append(f"{node_name}: {perf.avg_time:.1f}s average")
        
        # Find nodes with low success rate
        for node_name, perf in report.items():
            if perf.success_rate < 0.8:  # Less than 80% success
                bottlenecks.append(f"{node_name}: {perf.success_rate:.1%} success rate")
        
        return bottlenecks
