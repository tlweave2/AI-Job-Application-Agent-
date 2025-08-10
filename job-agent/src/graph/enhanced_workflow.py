from langgraph.graph import StateGraph, START, END
from models.graph_state import ApplicationState, FillStrategy
from graph.enhanced_nodes import EnhancedGraphNodes

def create_enhanced_workflow(browser, llm_services, rag_pipeline) -> StateGraph:
    """Create enhanced workflow with intelligent field classification"""
    
    # Initialize enhanced nodes
    enhanced_nodes = EnhancedGraphNodes(browser, llm_services, rag_pipeline)
    
    # Create the workflow
    workflow = StateGraph(ApplicationState)
    
    # Add enhanced nodes
    workflow.add_node("page_analysis", enhanced_nodes.enhanced_page_analysis_node)
    workflow.add_node("field_analysis", enhanced_nodes.intelligent_field_analysis_node)
    workflow.add_node("simple_fill", enhanced_nodes.smart_simple_fill_node)
    workflow.add_node("rag_fill", enhanced_nodes.smart_rag_fill_node)
    workflow.add_node("option_selection", enhanced_nodes.smart_option_selection_node)
    workflow.add_node("validation", enhanced_nodes.enhanced_validation_node)
    workflow.add_node("human_review", create_human_review_node())
    workflow.add_node("submit_form", create_submit_node())
    workflow.add_node("completion_check", create_completion_node())
    
    # Entry point
    workflow.add_edge(START, "page_analysis")
    
    # Page analysis to field analysis
    workflow.add_edge("page_analysis", "field_analysis")
    
    # Conditional routing after field analysis
    workflow.add_conditional_edges(
        "field_analysis",
        route_after_field_analysis,
        {
            "simple_fill": "simple_fill",
            "rag_fill": "rag_fill",
            "option_selection": "option_selection", 
            "human_review": "human_review",
            "completion_check": "completion_check"
        }
    )
    
    # All fill nodes go to validation
    fill_nodes = ["simple_fill", "rag_fill", "option_selection"]
    for node in fill_nodes:
        workflow.add_edge(node, "validation")
    
    # Conditional routing after validation
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "field_analysis": "field_analysis",
            "completion_check": "completion_check",
            "human_review": "human_review"
        }
    )
    
    # Completion check routing
    workflow.add_conditional_edges(
        "completion_check",
        route_after_completion,
        {
            "submit_form": "submit_form",
            "field_analysis": "field_analysis",
            "human_review": "human_review"
        }
    )
    
    # Terminal states
    workflow.add_edge("submit_form", END)
    workflow.add_edge("human_review", END)
    
    return workflow

def route_after_field_analysis(state: ApplicationState) -> str:
    """Enhanced routing based on intelligent classification"""
    
    current_field = state.get("current_field")
    if not current_field:
        return "completion_check"
    
    classification = current_field.get("classification")
    if not classification:
        return "human_review"
    
    fill_strategy = classification.fill_strategy
    
    # Route based on intelligent classification
    if fill_strategy == FillStrategy.SIMPLE_MAPPING:
        return "simple_fill"
    elif fill_strategy == FillStrategy.RAG_GENERATION:
        return "rag_fill"
    elif fill_strategy == FillStrategy.OPTION_SELECTION:
        return "option_selection"
    elif fill_strategy == FillStrategy.SKIP_FIELD:
        # Skip and continue to next field
        return "field_analysis"
    else:
        return "human_review"

def route_after_validation(state: ApplicationState) -> str:
    """Enhanced routing after validation"""
    
    # Check if we have more fields to process
    current_field = state.get("current_field")
    if current_field:
        retry_count = state.get("retry_count", 0)
        
        if retry_count < 3:
            # Retry the same field
            return "field_analysis"
        else:
            # Skip field and continue
            return "field_analysis"
    else:
        # No more fields - check completion
        return "completion_check"

def route_after_completion(state: ApplicationState) -> str:
    """Route after completion check"""
    
    should_submit = state.get("should_submit", False)
    has_more_fields = bool(state.get("field_queue"))
    
    if should_submit:
        return "submit_form"
    elif has_more_fields:
        return "field_analysis"
    else:
        return "human_review"

def create_human_review_node():
    """Create human review node"""
    async def human_review_node(state: ApplicationState) -> ApplicationState:
        # Implementation from previous human integration code
        return {
            **state,
            "final_state": "paused_for_human_review",
            "requires_human": True
        }
    return human_review_node

def create_submit_node():
    """Create form submission node"""
    async def submit_form_node(state: ApplicationState) -> ApplicationState:
        # Implementation for form submission
        return {
            **state,
            "final_state": "submitted",
            "form_submitted": True
        }
    return submit_form_node

def create_completion_node():
    """Create completion check node"""
    async def completion_check_node(state: ApplicationState) -> ApplicationState:
        # Use the completion check from enhanced nodes
        enhanced_nodes = state.get("_enhanced_nodes")  # Passed in context
        if enhanced_nodes:
            return enhanced_nodes._check_form_completion(state)
        
        # Fallback basic completion check
        return {
            **state,
            "final_state": "incomplete"
        }
    return completion_check_node
