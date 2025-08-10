def route_after_analysis(state: ApplicationState) -> str:
    """Route to appropriate fill strategy after field analysis"""
    strategy = state.get("fill_strategy")
    
    if strategy == FillStrategy.SIMPLE_MAPPING:
        return "simple_fill"
    elif strategy == FillStrategy.RAG_GENERATION:
        return "rag_fill"
    elif strategy == FillStrategy.OPTION_SELECTION:
        return "option_fill"
    elif strategy == FillStrategy.CONDITIONAL_LOGIC:
        return "conditional_logic"
    elif strategy == FillStrategy.SKIP_FIELD:
        return "skip_field"
    else:
        return "human_review"

def route_after_validation(state: ApplicationState) -> str:
    """Route after validation"""
    if state.get("requires_human"):
        return "human_review"
    elif state.get("should_submit"):
        return "submit_form"
    elif state["current_field"] is None:
        return "completion_check"
    elif state["retry_count"] > 3:
        return "repair_strategy"
    else:
        return "field_analysis"

def route_completion_check(state: ApplicationState) -> str:
    """Route based on completion status"""
    if state["form_completion"] >= 0.9:
        return "submit_form"
    elif len(state["field_queue"]) > 0:
        return "field_analysis"  # Process remaining fields
    else:
        return "human_review"   # Incomplete but no more fields
