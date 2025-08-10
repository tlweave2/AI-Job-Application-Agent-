from langgraph.graph import StateGraph, START, END
from .nodes import *
from .routing import *

def create_job_application_graph() -> StateGraph:
    """Create the main job application workflow graph"""
    
    workflow = StateGraph(ApplicationState)
    
    # Add nodes
    workflow.add_node("page_analysis", page_analysis_node)
    workflow.add_node("field_analysis", field_analysis_node)
    workflow.add_node("simple_fill", simple_fill_node)
    workflow.add_node("rag_fill", rag_fill_node)
    workflow.add_node("option_fill", option_fill_node)
    workflow.add_node("conditional_logic", conditional_logic_node)
    workflow.add_node("skip_field", skip_field_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("repair_strategy", repair_strategy_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("submit_form", submit_form_node)
    workflow.add_node("completion_check", completion_check_node)
    
    # Entry point
    workflow.add_edge(START, "page_analysis")
    
    # Linear flow from page analysis to field analysis
    workflow.add_edge("page_analysis", "field_analysis")
    
    # Conditional routing after field analysis
    workflow.add_conditional_edges(
        "field_analysis",
        route_after_analysis,
        {
            "simple_fill": "simple_fill",
            "rag_fill": "rag_fill", 
            "option_fill": "option_fill",
            "conditional_logic": "conditional_logic",
            "skip_field": "skip_field",
            "human_review": "human_review"
        }
    )
    
    # All fill nodes go to validation
    for fill_node in ["simple_fill", "rag_fill", "option_fill", "conditional_logic", "skip_field"]:
        workflow.add_edge(fill_node, "validation")
    
    # Conditional routing after validation
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "field_analysis": "field_analysis",
            "repair_strategy": "repair_strategy", 
            "human_review": "human_review",
            "submit_form": "submit_form",
            "completion_check": "completion_check"
        }
    )
    
    # Repair goes back to field analysis
    workflow.add_edge("repair_strategy", "field_analysis")
    
    # Completion check routing
    workflow.add_conditional_edges(
        "completion_check",
        route_completion_check,
        {
            "submit_form": "submit_form",
            "field_analysis": "field_analysis",
            "human_review": "human_review"
        }
    )
    
    # Terminal nodes
    workflow.add_edge("submit_form", END)
    workflow.add_edge("human_review", END)
    
    return workflow
