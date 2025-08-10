from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
import asyncio

@dataclass
class HumanReviewRequest:
    session_id: str
    field: Dict
    context: str
    urgency: str  # low, medium, high, critical
    estimated_time: float
    suggested_actions: List[str]
    callback_url: Optional[str] = None

class HumanReviewSystem:
    """Handle human-in-the-loop interactions"""
    
    def __init__(self, notification_handler: Optional[Callable] = None):
        self.pending_reviews = {}
        self.notification_handler = notification_handler
        self.review_timeout = 300  # 5 minutes default
    
    async def human_review_node(self, state: ApplicationState) -> ApplicationState:
        """Node that pauses execution for human review"""
        
        current_field = state["current_field"]
        session_id = state.get("session_id", "unknown")
        
        # Create review request
        review_request = HumanReviewRequest(
            session_id=session_id,
            field=current_field,
            context=self._build_context_description(current_field, state),
            urgency=self._assess_urgency(current_field, state),
            estimated_time=self._estimate_review_time(current_field),
            suggested_actions=self._suggest_actions(current_field, state)
        )
        
        # Save state for resumption
        await self._save_state_for_resume(state, review_request)
        
        # Notify human (email, Slack, webhook, etc.)
        if self.notification_handler:
            await self.notification_handler(review_request)
        
        # Return paused state
        return {
            **state,
            "final_state": "paused_for_human_review",
            "review_request": review_request.to_dict(),
            "pause_timestamp": time.time(),
            "resume_available": True
        }
    
    def _build_context_description(self, field: Dict, state: ApplicationState) -> str:
        """Build human-readable context"""
        element = field["element"]
        
        context_parts = [
            f"Field: {element.selector}",
            f"Type: {element.tag}[{element.type}]",
            f"Placeholder: '{element.placeholder}'",
            f"Required: {element.required}",
            f"Page: {state['url']}",
            f"Progress: {len(state['completed_fields'])}/{len(state['field_queue']) + len(state['completed_fields'])}"
        ]
        
        if state.get("failure_type"):
            context_parts.append(f"Failed because: {state['failure_type']}")
        
        return "\n".join(context_parts)
    
    def _assess_urgency(self, field: Dict, state: ApplicationState) -> str:
        """Assess how urgent this review is"""
        
        # Critical: blocking submission
        if field.get("required") and state["form_completion"] > 0.8:
            return "critical"
        
        # High: many failed attempts
        if state["retry_count"] > 2:
            return "high"
        
        # Medium: complex field
        if field.get("estimated_difficulty") == "hard":
            return "medium"
        
        # Low: optional field
        return "low"
    
    async def resume_from_human_input(self, session_id: str, human_decision: Dict) -> ApplicationState:
        """Resume execution after human input"""
        
        # Load saved state
        saved_state = await self._load_saved_state(session_id)
        
        # Apply human decision
        if human_decision["action"] == "fill_field":
            # Human provided a value
            updated_state = self._apply_human_fill(saved_state, human_decision["value"])
        elif human_decision["action"] == "skip_field":
            # Human decided to skip
            updated_state = self._apply_human_skip(saved_state)
        elif human_decision["action"] == "modify_strategy":
            # Human suggested different approach
            updated_state = self._apply_strategy_change(saved_state, human_decision["new_strategy"])
        else:
            # Continue with original plan
            updated_state = saved_state
        
        # Clear pause state
        updated_state["final_state"] = "resumed_from_human"
        updated_state["requires_human"] = False
        
        return updated_state
