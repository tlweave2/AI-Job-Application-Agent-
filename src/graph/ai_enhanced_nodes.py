"""
AI-Enhanced LangGraph Nodes
All nodes use AI for decision making, no hard-coded business logic
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
import asyncio

from models.graph_state import ApplicationState, FillStrategy
from models.snapshot import ActionableElement, BrowserSnapshot
from models.plan import Action, ActionType
from graph.ai_field_classifier import AIFieldClassifier

logger = logging.getLogger(__name__)

class AIEnhancedNodes:
    """AI-powered nodes for LangGraph workflow"""
    
    def __init__(self, browser, llm_services, rag_pipeline):
        self.browser = browser
        self.llm = llm_services
        self.rag = rag_pipeline
        self.ai_classifier = AIFieldClassifier(llm_services)
    # ...existing code...
