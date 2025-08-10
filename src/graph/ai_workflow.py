"""
AI-FIRST WORKFLOW - No Hard-Coded Business Logic
Every decision is made by AI, not predetermined rules
"""

from langgraph.graph import StateGraph, START, END
from models.graph_state import ApplicationState
from graph.ai_field_classifier import AIEnhancedNodes

# ...existing code...

def create_ai_first_workflow(browser, llm_services, rag_pipeline) -> StateGraph:
    """Create AI-first workflow where every decision uses AI"""
    
    # Initialize AI-powered nodes (no hard-coded logic)
    ai_nodes = AIEnhancedNodes(browser, llm_services, rag_pipeline)
    
    workflow = StateGraph(ApplicationState)
    
    # All nodes use AI decision-making
    workflow.add_node("ai_page_analysis", ai_nodes.ai_page_analysis_node)
    workflow.add_node("ai_field_analysis", ai_nodes.ai_field_analysis_node)
    workflow.add_node("ai_simple_fill", ai_nodes.ai_simple_fill_node)
    workflow.add_node("ai_rag_fill", ai_nodes.ai_rag_fill_node)
    workflow.add_node("ai_option_selection", ai_nodes.ai_option_selection_node)
    workflow.add_node("ai_validation", ai_nodes.ai_validation_node)
    workflow.add_node("ai_completion_check", ai_nodes.ai_completion_check_node)
    workflow.add_node("human_review", create_human_review_node())
    workflow.add_node("submit_form", create_submit_node())
    
    # Entry point
    workflow.add_edge(START, "ai_page_analysis")
    
    # AI-driven routing (no hard-coded conditions)
    workflow.add_edge("ai_page_analysis", "ai_field_analysis")
    
    # AI decides routing after field analysis
    workflow.add_conditional_edges(
        "ai_field_analysis",
        ai_route_after_field_analysis,  # AI makes routing decisions
        {
            "ai_simple_fill": "ai_simple_fill",
            "ai_rag_fill": "ai_rag_fill", 
            "ai_option_selection": "ai_option_selection",
            "human_review": "human_review",
            "ai_completion_check": "ai_completion_check"
        }
    )
    
    # All fill nodes go to AI validation
    fill_nodes = ["ai_simple_fill", "ai_rag_fill", "ai_option_selection"]
    for node in fill_nodes:
        workflow.add_edge(node, "ai_validation")
    
    # AI-driven validation routing
    workflow.add_conditional_edges(
        "ai_validation",
        ai_route_after_validation,  # AI decides next step
        {
            "ai_field_analysis": "ai_field_analysis",
            "ai_completion_check": "ai_completion_check", 
            "human_review": "human_review"
        }
    )
    
    # AI-driven completion routing
    workflow.add_conditional_edges(
        "ai_completion_check",
        ai_route_after_completion,  # AI decides if ready to submit
        {
            "submit_form": "submit_form",
            "ai_field_analysis": "ai_field_analysis",
            "human_review": "human_review"
        }
    )
    
    # Terminal states
    workflow.add_edge("submit_form", END)
    workflow.add_edge("human_review", END)
    
    return workflow

# ...existing code...

def create_human_review_node():
    async def human_review_node(state: ApplicationState) -> ApplicationState:
        return {
            **state,
            "final_state": "paused_for_human_review",
            "requires_human": True
        }
    return human_review_node

def create_submit_node():
    async def submit_form_node(state: ApplicationState) -> ApplicationState:
        return {
            **state,
            "final_state": "submitted",
            "form_submitted": True
        }
    return submit_form_node

# ...existing code...
