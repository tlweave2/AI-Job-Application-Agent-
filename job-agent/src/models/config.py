
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class BrowserConfig:
	"""Browser configuration settings"""
	headful: bool = True
	user_data_dir: str = "./data/browser_profile"
	viewport: Dict[str, int] = None
    
	def __post_init__(self):
		if self.viewport is None:
			self.viewport = {"width": 1280, "height": 720}

@dataclass
class TimeoutConfig:
	"""Timeout configuration for various operations"""
	default: int = 10000
	navigation: int = 30000
	action: int = 5000

@dataclass
class ThresholdConfig:
	"""Accuracy and confidence thresholds for auto-submit gating"""
	short_field_accuracy: float = 0.99
	long_answer_confidence: float = 0.90

@dataclass
class ProfileConfig:
	"""Complete profile configuration"""
	browser: BrowserConfig
	timeouts: TimeoutConfig
	thresholds: ThresholdConfig
    
	@classmethod
	def from_dict(cls, config_dict: Dict[str, Any]) -> 'ProfileConfig':
		"""Create ProfileConfig from dictionary (e.g., from YAML)"""
		browser_data = config_dict.get('browser', {})
		timeout_data = config_dict.get('timeouts', {})
		threshold_data = config_dict.get('thresholds', {})
        
		return cls(
			browser=BrowserConfig(**browser_data),
			timeouts=TimeoutConfig(**timeout_data),
			thresholds=ThresholdConfig(**threshold_data)
		)

@dataclass
class PersonalInfo:
	"""Personal information from questionnaire"""
	first_name: str = ""
	last_name: str = ""
	email: str = ""
	phone: str = ""
	work_authorization: str = ""
	relocation: str = ""
	linkedin: str = ""

@dataclass
class ExperienceInfo:
	"""Experience information from questionnaire"""
	years_programming: str = ""
	preferred_technologies: List[str] = None
	current_title: str = ""
	current_company: str = ""
    
	def __post_init__(self):
		if self.preferred_technologies is None:
			self.preferred_technologies = []

@dataclass
class PreferencesInfo:
	"""Preference information from questionnaire"""
	salary_expectation: str = ""
	start_date: str = ""
	remote_work: str = ""

@dataclass
class QuestionnaireConfig:
	"""Complete questionnaire configuration"""
	personal: PersonalInfo
	experience: ExperienceInfo
	preferences: PreferencesInfo
    
	@classmethod
	def from_dict(cls, config_dict: Dict[str, Any]) -> 'QuestionnaireConfig':
		"""Create QuestionnaireConfig from dictionary (e.g., from YAML)"""
		personal_data = config_dict.get('personal', {})
		experience_data = config_dict.get('experience', {})
		preferences_data = config_dict.get('preferences', {})
        
		return cls(
			personal=PersonalInfo(**personal_data),
			experience=ExperienceInfo(**experience_data),
			preferences=PreferencesInfo(**preferences_data)
		)

@dataclass
class AgentConfig:
	"""Main agent configuration"""
	profile_path: str
	resume_path: str
	questionnaire_path: str
	openai_api_key: str
	auto_submit: bool = False
	max_cycles: int = 10
	max_retries: int = 2
