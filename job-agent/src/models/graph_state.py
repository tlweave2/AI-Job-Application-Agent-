from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum

class FieldType(Enum):
    TEXT_INPUT = "text_input"
    TEXTAREA = "textarea" 
    DROPDOWN = "dropdown"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE_UPLOAD = "file_upload"
    CONDITIONAL = "conditional"

class FillStrategy(Enum):
    SIMPLE_MAPPING = "simple_mapping"     # name, email, phone
    RAG_GENERATION = "rag_generation"     # essays, cover letters
    OPTION_SELECTION = "option_selection" # dropdowns, radio
    CONDITIONAL_LOGIC = "conditional"     # depends on other fields
    SKIP_FIELD = "skip"                   # assessments, out of scope

class ApplicationState(TypedDict):
    # Page context
    url: str
    page_title: str
    current_snapshot: dict
    
    # Field processing
    field_queue: List[dict]          # Fields to process
    current_field: Optional[dict]    # Field being processed
    completed_fields: List[dict]     # Successfully filled
    failed_fields: List[dict]        # Failed attempts
    skipped_fields: List[dict]       # Intentionally skipped
    
    # User context
    user_data: dict                  # Questionnaire data
    rag_context: dict               # RAG pipeline state
    
    # Execution context
    retry_count: int
    cycle_count: int
    execution_time: float
    
    # Decision context
    field_analysis: Optional[dict]   # Current field analysis
    fill_strategy: Optional[FillStrategy]
    requires_human: bool
    
    # Results
    form_completion: float
    should_submit: bool
    final_state: str
