from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

class FailureType(Enum):
    ELEMENT_NOT_FOUND = "element_not_found"
    VALUE_REJECTED = "value_rejected"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    ACCESS_DENIED = "access_denied"
    UNKNOWN = "unknown"

@dataclass
class RepairStrategy:
    strategy_type: str
    confidence: float
    estimated_time: float
    fallback_available: bool
    repair_actions: List[Dict]

class SmartRepairSystem:
    """Intelligent repair strategies based on failure patterns"""
    
    def __init__(self):
        self.failure_history = []
        self.success_patterns = {}
    
    async def analyze_failure_node(self, state: ApplicationState) -> ApplicationState:
        """Analyze why the action failed and determine repair strategy"""
        
        failed_field = state["current_field"]
        last_error = state.get("last_error", "")
        retry_count = state["retry_count"]
        
        # Classify failure type
        failure_type = self._classify_failure(last_error, failed_field)
        
        # Get repair strategy
        repair_strategy = self._get_repair_strategy(
            failure_type, failed_field, retry_count
        )
        
        # Update state with repair plan
        return {
            **state,
            "repair_strategy": repair_strategy,
            "failure_type": failure_type,
            "repair_confidence": repair_strategy.confidence
        }
    
    def _classify_failure(self, error: str, field: Dict) -> FailureType:
        """Classify the type of failure"""
        error_lower = error.lower()
        
        if any(keyword in error_lower for keyword in ["not found", "no such element"]):
            return FailureType.ELEMENT_NOT_FOUND
        elif any(keyword in error_lower for keyword in ["timeout", "wait"]):
            return FailureType.TIMEOUT
        elif any(keyword in error_lower for keyword in ["invalid", "rejected", "format"]):
            return FailureType.VALUE_REJECTED
        elif any(keyword in error_lower for keyword in ["access", "permission", "denied"]):
            return FailureType.ACCESS_DENIED
        else:
            return FailureType.UNKNOWN
    
    def _get_repair_strategy(self, failure_type: FailureType, field: Dict, retry_count: int) -> RepairStrategy:
        """Get appropriate repair strategy"""
        
        if failure_type == FailureType.ELEMENT_NOT_FOUND:
            return self._element_not_found_strategy(field, retry_count)
        elif failure_type == FailureType.VALUE_REJECTED:
            return self._value_rejected_strategy(field, retry_count)
        elif failure_type == FailureType.TIMEOUT:
            return self._timeout_strategy(field, retry_count)
        elif failure_type == FailureType.ACCESS_DENIED:
            return self._access_denied_strategy(field, retry_count)
        else:
            return self._unknown_failure_strategy(field, retry_count)
    
    def _element_not_found_strategy(self, field: Dict, retry_count: int) -> RepairStrategy:
        """Strategy for when element selector fails"""
        
        if retry_count == 0:
            # First attempt: try alternative selectors
            return RepairStrategy(
                strategy_type="alternative_selectors",
                confidence=0.8,
                estimated_time=2.0,
                fallback_available=True,
                repair_actions=[
                    {"type": "wait", "duration": 1.0},
                    {"type": "refresh_snapshot"},
                    {"type": "try_alternative_selectors"}
                ]
            )
        elif retry_count == 1:
            # Second attempt: wait for page to stabilize
            return RepairStrategy(
                strategy_type="wait_and_retry",
                confidence=0.6,
                estimated_time=5.0,
                fallback_available=True,
                repair_actions=[
                    {"type": "wait_for_stability", "duration": 3.0},
                    {"type": "refresh_snapshot"},
                    {"type": "retry_original_selector"}
                ]
            )
        else:
            # Final attempt: skip field
            return RepairStrategy(
                strategy_type="skip_field",
                confidence=1.0,
                estimated_time=0.1,
                fallback_available=False,
                repair_actions=[
                    {"type": "mark_as_skipped"},
                    {"type": "continue_to_next"}
                ]
            )
