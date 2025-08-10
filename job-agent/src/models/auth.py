
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional

class AuthState(Enum):
	"""Authentication states for web pages"""
	READY = "ready"
	LOGIN_REQUIRED = "login_required"
	CAPTCHA_PRESENT = "captcha_present"
	TWO_FA_REQUIRED = "two_fa_required"
	BLOCKED = "blocked"
	UNKNOWN = "unknown"
	SESSION_EXPIRED = "session_expired"
	REGISTRATION_REQUIRED = "registration_required"

class NextAction(Enum):
	"""Next actions based on auth state"""
	PROCEED = "proceed"
	PAUSE_FOR_HUMAN = "pause_for_human"
	SKIP_PAGE = "skip_page"
	RETRY_LATER = "retry_later"
	TERMINATE = "terminate"

@dataclass
class AuthVerdict:
	"""Result of authentication state classification"""
	state: AuthState
	next_action: NextAction
	reason: str
	confidence: float
	detected_elements: Optional[Dict[str, Any]] = None
	suggested_wait_time: Optional[int] = None  # seconds to wait before retry
    
	def __post_init__(self):
		# Convert string enums to proper enums if needed
		if isinstance(self.state, str):
			self.state = AuthState(self.state)
		if isinstance(self.next_action, str):
			self.next_action = NextAction(self.next_action)
    
	@property
	def should_proceed(self) -> bool:
		"""Check if agent should proceed with form filling"""
		return self.next_action == NextAction.PROCEED
    
	@property
	def needs_human_intervention(self) -> bool:
		"""Check if human intervention is required"""
		return self.next_action == NextAction.PAUSE_FOR_HUMAN
    
	@property
	def should_skip(self) -> bool:
		"""Check if page should be skipped"""
		return self.next_action == NextAction.SKIP_PAGE
    
	@property
	def is_blocking(self) -> bool:
		"""Check if this auth state blocks automation"""
		return self.state in [
			AuthState.LOGIN_REQUIRED,
			AuthState.CAPTCHA_PRESENT,
			AuthState.TWO_FA_REQUIRED,
			AuthState.BLOCKED,
			AuthState.SESSION_EXPIRED
		]
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization"""
		return {
			"state": self.state.value,
			"next_action": self.next_action.value,
			"reason": self.reason,
			"confidence": self.confidence,
			"detected_elements": self.detected_elements,
			"suggested_wait_time": self.suggested_wait_time
		}
    
	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> 'AuthVerdict':
		"""Create AuthVerdict from dictionary"""
		return cls(
			state=AuthState(data["state"]),
			next_action=NextAction(data["next_action"]),
			reason=data["reason"],
			confidence=data["confidence"],
			detected_elements=data.get("detected_elements"),
			suggested_wait_time=data.get("suggested_wait_time")
		)

@dataclass
class AuthContext:
	"""Context information for authentication decisions"""
	previous_attempts: int = 0
	session_cookies_present: bool = False
	user_logged_in_elsewhere: bool = False
	page_load_time: Optional[float] = None
	referrer_url: Optional[str] = None
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization"""
		return {
			"previous_attempts": self.previous_attempts,
			"session_cookies_present": self.session_cookies_present,
			"user_logged_in_elsewhere": self.user_logged_in_elsewhere,
			"page_load_time": self.page_load_time,
			"referrer_url": self.referrer_url
		}
