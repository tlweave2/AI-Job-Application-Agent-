
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class ActionType(Enum):
	"""Types of actions that can be executed"""
	CLICK = "click"
	TYPE = "type"
	SELECT = "select"
	UPLOAD = "upload"
	WAIT = "wait"
	CLEAR = "clear"

@dataclass
class Action:
	"""Represents an action to be executed"""
	type: ActionType
	selector: str
	value: Optional[str] = None
	options: Optional[Dict[str, Any]] = None
	reasoning: Optional[str] = None
    
	def __post_init__(self):
		# Convert string action type to enum if needed
		if isinstance(self.type, str):
			self.type = ActionType(self.type)
    
	@property
	def type_str(self) -> str:
		"""Get action type as string"""
		return self.type.value
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization"""
		return {
			"type": self.type_str,
			"selector": self.selector,
			"value": self.value,
			"options": self.options,
			"reasoning": self.reasoning
		}
    
	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> 'Action':
		"""Create Action from dictionary"""
		return cls(
			type=ActionType(data["type"]),
			selector=data["selector"],
			value=data.get("value"),
			options=data.get("options"),
			reasoning=data.get("reasoning")
		)

@dataclass
class ActionPlan:
	"""A plan containing multiple actions to execute"""
	actions: List[Action]
	reasoning: str
	confidence: float
	includes_submit: bool
	estimated_completion: float
	priority: str = "normal"  # normal, high, critical
    
	def __post_init__(self):
		# Ensure actions are Action objects
		self.actions = [
			action if isinstance(action, Action) else Action.from_dict(action)
			for action in self.actions
		]
    
	@property
	def action_count(self) -> int:
		"""Number of actions in this plan"""
		return len(self.actions)
    
	@property
	def has_file_uploads(self) -> bool:
		"""Check if plan includes file uploads"""
		return any(action.type == ActionType.UPLOAD for action in self.actions)
    
	@property
	def has_form_inputs(self) -> bool:
		"""Check if plan includes form input actions"""
		return any(action.type in [ActionType.TYPE, ActionType.SELECT] for action in self.actions)
    
	def get_actions_by_type(self, action_type: ActionType) -> List[Action]:
		"""Get all actions of a specific type"""
		return [action for action in self.actions if action.type == action_type]
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization"""
		return {
			"actions": [action.to_dict() for action in self.actions],
			"reasoning": self.reasoning,
			"confidence": self.confidence,
			"includes_submit": self.includes_submit,
			"estimated_completion": self.estimated_completion,
			"priority": self.priority
		}
    
	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> 'ActionPlan':
		"""Create ActionPlan from dictionary"""
		return cls(
			actions=[Action.from_dict(action_data) for action_data in data["actions"]],
			reasoning=data["reasoning"],
			confidence=data["confidence"],
			includes_submit=data["includes_submit"],
			estimated_completion=data["estimated_completion"],
			priority=data.get("priority", "normal")
		)

@dataclass
class RepairSuggestion:
	"""Suggestion for repairing a failed action"""
	original_action: Action
	suggested_action: Action
	reasoning: str
	confidence: float
	repair_type: str = "selector_fix"  # selector_fix, value_fix, type_change, alternative_approach
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization"""
		return {
			"original_action": self.original_action.to_dict(),
			"suggested_action": self.suggested_action.to_dict(),
			"reasoning": self.reasoning,
			"confidence": self.confidence,
			"repair_type": self.repair_type
		}

@dataclass
class ExecutionResult:
	"""Result of executing an action plan or individual action"""
	success: bool
	completed_actions: int
	failed_actions: int
	form_completion: float
	final_state: str
	screenshot_path: Optional[str] = None
	error_message: Optional[str] = None
	execution_time: Optional[float] = None
    
	@property
	def total_actions(self) -> int:
		"""Total number of actions attempted"""
		return self.completed_actions + self.failed_actions
    
	@property
	def success_rate(self) -> float:
		"""Success rate of executed actions"""
		if self.total_actions == 0:
			return 0.0
		return self.completed_actions / self.total_actions
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization"""
		return {
			"success": self.success,
			"completed_actions": self.completed_actions,
			"failed_actions": self.failed_actions,
			"form_completion": self.form_completion,
			"final_state": self.final_state,
			"screenshot_path": self.screenshot_path,
			"error_message": self.error_message,
			"execution_time": self.execution_time,
			"success_rate": self.success_rate
		}
