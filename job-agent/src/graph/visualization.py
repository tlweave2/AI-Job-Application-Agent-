import graphviz
from typing import Dict, Any

class GraphVisualizer:
    """Visualize and debug the LangGraph workflow"""
    
    def __init__(self, workflow: StateGraph):
        self.workflow = workflow
    
    def generate_flow_diagram(self, output_path: str = "workflow.png"):
        """Generate visual representation of the workflow"""
        
        dot = graphviz.Digraph(comment='Job Application Workflow')
        dot.attr(rankdir='TB', size='12,8')
        
        # Add nodes with different colors based on type
        node_colors = {
            'analysis': '#lightblue',
            'fill': '#lightgreen', 
            'validation': '#yellow',
            'human': '#orange',
            'terminal': '#lightcoral'
        }
        
        # Add all nodes
        for node_name in self.workflow.nodes:
            node_type = self._categorize_node(node_name)
            dot.node(node_name, node_name.replace('_', '\n'), 
                    fillcolor=node_colors.get(node_type, '#white'),
                    style='filled')
        
        # Add edges
        for source, targets in self.workflow.edges.items():
            if isinstance(targets, list):
                for target in targets:
                    dot.edge(source, target)
            else:
                dot.edge(source, targets)
        
        # Add conditional edges with labels
        for source, conditions in self.workflow.conditional_edges.items():
            for condition, target in conditions.items():
                dot.edge(source, target, label=condition, style='dashed')
        
        dot.render(output_path, format='png', cleanup=True)
        return f"{output_path}.png"
    
    def trace_execution_path(self, execution_log: List[Dict]) -> str:
        """Generate execution trace visualization"""
        
        dot = graphviz.Digraph(comment='Execution Trace')
        dot.attr(rankdir='LR')
        
        # Add execution steps
        for i, step in enumerate(execution_log):
            node_name = step['node']
            timestamp = step['timestamp']
            success = step.get('success', True)
            
            color = 'lightgreen' if success else 'lightcoral'
            label = f"{node_name}\n{timestamp}\n{'✓' if success else '✗'}"
            
            dot.node(f"step_{i}", label, fillcolor=color, style='filled')
            
            if i > 0:
                dot.edge(f"step_{i-1}", f"step_{i}")
        
        return dot.source
