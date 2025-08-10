
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid

@dataclass
class ActionLog:
	"""Structured log entry for agent actions"""
	timestamp: str
	session_id: str
	action_id: str
	action_type: str
	selector: str
	value: Optional[str]
	success: bool
	execution_time: float
	error_message: Optional[str] = None
	screenshot_path: Optional[str] = None
	page_url: Optional[str] = None
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for JSON serialization"""
		return asdict(self)

@dataclass
class SessionLog:
	"""Log entry for agent session"""
	session_id: str
	start_time: str
	end_time: Optional[str]
	target_url: str
	total_actions: int
	successful_actions: int
	failed_actions: int
	final_state: str
	auto_submit_enabled: bool
	form_submitted: bool
    
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for JSON serialization"""
		return asdict(self)

class AgentLogger:
	"""Structured logging for job application agent"""
    
	def __init__(self, log_dir: str = "./logs", session_id: str = None):
		self.log_dir = Path(log_dir)
		self.log_dir.mkdir(exist_ok=True)
        
		self.session_id = session_id or str(uuid.uuid4())[:8]
		self.session_start = datetime.now().isoformat()
        
		# Set up log files
		self.action_log_file = self.log_dir / f"actions_{self.session_id}.jsonl"
		self.session_log_file = self.log_dir / f"session_{self.session_id}.json"
		self.debug_log_file = self.log_dir / f"debug_{self.session_id}.log"
        
		# Configure standard logger
		self._setup_debug_logger()
        
		# Session tracking
		self.actions_logged = []
		self.session_start_time = time.time()
        
		self.logger = logging.getLogger(f"agent.{self.session_id}")
		self.logger.info(f"Agent session started: {self.session_id}")
    
	def _setup_debug_logger(self):
		"""Set up debug logging to file"""
		debug_logger = logging.getLogger(f"agent.{self.session_id}")
		debug_logger.setLevel(logging.DEBUG)
        
		# File handler for detailed logs
		file_handler = logging.FileHandler(self.debug_log_file)
		file_formatter = logging.Formatter(
			'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		)
		file_handler.setFormatter(file_formatter)
		debug_logger.addHandler(file_handler)
        
		# Prevent duplicate logs
		debug_logger.propagate = False
    
	def log_action(
		self,
		action_type: str,
		selector: str,
		value: Optional[str] = None,
		success: bool = True,
		execution_time: float = 0.0,
		error_message: Optional[str] = None,
		screenshot_path: Optional[str] = None,
		page_url: Optional[str] = None
	) -> str:
		"""Log an individual action"""
        
		action_id = str(uuid.uuid4())[:8]
        
		action_log = ActionLog(
			timestamp=datetime.now().isoformat(),
			session_id=self.session_id,
			action_id=action_id,
			action_type=action_type,
			selector=selector,
			value=value,
			success=success,
			execution_time=execution_time,
			error_message=error_message,
			screenshot_path=screenshot_path,
			page_url=page_url
		)
        
		# Write to JSONL file
		with open(self.action_log_file, 'a') as f:
			f.write(json.dumps(action_log.to_dict()) + '\n')
        
		# Track in memory
		self.actions_logged.append(action_log)
        
		# Log to debug logger
		status = "SUCCESS" if success else "FAILED"
		self.logger.info(f"Action {action_id}: {action_type} on {selector} - {status}")
        
		if error_message:
			self.logger.error(f"Action {action_id} error: {error_message}")
        
		return action_id
    
	def log_auth_check(self, auth_state: str, next_action: str, confidence: float):
		"""Log authentication check result"""
		self.logger.info(f"Auth check: {auth_state} -> {next_action} (confidence: {confidence:.2f})")
    
	def log_plan_generation(self, action_count: int, confidence: float, includes_submit: bool):
		"""Log action plan generation"""
		self.logger.info(f"Generated plan: {action_count} actions (confidence: {confidence:.2f}, submit: {includes_submit})")
    
	def log_form_analysis(self, total_elements: int, form_count: int, required_fields: int):
		"""Log form analysis results"""
		self.logger.info(f"Form analysis: {total_elements} elements, {form_count} forms, {required_fields} required fields")
    
	def log_completion_check(self, completion_percentage: float, success_rate: float, should_submit: bool):
		"""Log completion and submission decision"""
		self.logger.info(f"Completion check: {completion_percentage:.1%} complete, {success_rate:.1%} success rate, submit: {should_submit}")
    
	def log_session_end(
		self,
		final_state: str,
		auto_submit_enabled: bool,
		form_submitted: bool
	):
		"""Log session completion"""
        
		end_time = datetime.now().isoformat()
		successful_actions = sum(1 for action in self.actions_logged if action.success)
		failed_actions = len(self.actions_logged) - successful_actions
        
		session_log = SessionLog(
			session_id=self.session_id,
			start_time=self.session_start,
			end_time=end_time,
			target_url=self.actions_logged[0].page_url if self.actions_logged else "unknown",
			total_actions=len(self.actions_logged),
			successful_actions=successful_actions,
			failed_actions=failed_actions,
			final_state=final_state,
			auto_submit_enabled=auto_submit_enabled,
			form_submitted=form_submitted
		)
        
		# Write session summary
		with open(self.session_log_file, 'w') as f:
			json.dump(session_log.to_dict(), f, indent=2)
        
		duration = time.time() - self.session_start_time
		self.logger.info(f"Session ended: {final_state} (duration: {duration:.1f}s, actions: {len(self.actions_logged)})")
    
	def get_session_summary(self) -> Dict[str, Any]:
		"""Get current session summary"""
		successful_actions = sum(1 for action in self.actions_logged if action.success)
		failed_actions = len(self.actions_logged) - successful_actions
        
		return {
			"session_id": self.session_id,
			"duration": time.time() - self.session_start_time,
			"total_actions": len(self.actions_logged),
			"successful_actions": successful_actions,
			"failed_actions": failed_actions,
			"success_rate": successful_actions / len(self.actions_logged) if self.actions_logged else 0.0
		}

class LogAnalyzer:
	"""Analyze agent logs for insights and debugging"""
    
	def __init__(self, log_dir: str = "./logs"):
		self.log_dir = Path(log_dir)
    
	def analyze_session(self, session_id: str) -> Dict[str, Any]:
		"""Analyze a specific session's performance"""
        
		action_log_file = self.log_dir / f"actions_{session_id}.jsonl"
		session_log_file = self.log_dir / f"session_{session_id}.json"
        
		if not action_log_file.exists():
			return {"error": f"Session {session_id} not found"}
        
		# Load actions
		actions = []
		with open(action_log_file, 'r') as f:
			for line in f:
				actions.append(json.loads(line))
        
		# Load session data
		session_data = {}
		if session_log_file.exists():
			with open(session_log_file, 'r') as f:
				session_data = json.load(f)
        
		# Analyze patterns
		action_types = {}
		success_by_type = {}
		execution_times = []
        
		for action in actions:
			action_type = action['action_type']
			action_types[action_type] = action_types.get(action_type, 0) + 1
            
			if action_type not in success_by_type:
				success_by_type[action_type] = {"total": 0, "successful": 0}
            
			success_by_type[action_type]["total"] += 1
			if action['success']:
				success_by_type[action_type]["successful"] += 1
            
			execution_times.append(action['execution_time'])
        
		# Calculate success rates by type
		success_rates = {}
		for action_type, stats in success_by_type.items():
			success_rates[action_type] = stats["successful"] / stats["total"]
        
		return {
			"session_id": session_id,
			"session_data": session_data,
			"total_actions": len(actions),
			"action_types": action_types,
			"success_rates": success_rates,
			"avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
			"actions": actions
		}
    
	def find_common_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
		"""Find most common failure patterns across all sessions"""
        
		failures = []
        
		# Scan all action log files
		for log_file in self.log_dir.glob("actions_*.jsonl"):
			with open(log_file, 'r') as f:
				for line in f:
					action = json.loads(line)
					if not action['success'] and action.get('error_message'):
						failures.append({
							"action_type": action['action_type'],
							"selector": action['selector'],
							"error": action['error_message'],
							"session": action['session_id']
						})
        
		# Group by error patterns
		error_patterns = {}
		for failure in failures:
			error_key = f"{failure['action_type']}:{failure['error']}"
			if error_key not in error_patterns:
				error_patterns[error_key] = {
					"count": 0,
					"action_type": failure['action_type'],
					"error": failure['error'],
					"examples": []
				}
            
			error_patterns[error_key]["count"] += 1
			if len(error_patterns[error_key]["examples"]) < 3:
				error_patterns[error_key]["examples"].append({
					"selector": failure['selector'],
					"session": failure['session']
				})
        
		# Sort by frequency
		sorted_patterns = sorted(error_patterns.values(), key=lambda x: x['count'], reverse=True)
        
		return sorted_patterns[:limit]
    
	def get_performance_stats(self) -> Dict[str, Any]:
		"""Get overall performance statistics"""
        
		all_sessions = []
		total_actions = 0
		successful_actions = 0
        
		# Scan all session files
		for session_file in self.log_dir.glob("session_*.json"):
			with open(session_file, 'r') as f:
				session = json.load(f)
				all_sessions.append(session)
				total_actions += session['total_actions']
				successful_actions += session['successful_actions']
        
		return {
			"total_sessions": len(all_sessions),
			"total_actions": total_actions,
			"overall_success_rate": successful_actions / total_actions if total_actions > 0 else 0,
			"avg_actions_per_session": total_actions / len(all_sessions) if all_sessions else 0,
			"sessions_with_submission": sum(1 for s in all_sessions if s.get('form_submitted', False))
		}

# Convenience function for easy logging setup
def setup_agent_logging(session_id: str = None, log_dir: str = "./logs") -> AgentLogger:
	"""Set up logging for an agent session"""
	return AgentLogger(log_dir=log_dir, session_id=session_id)

# Test function
def test_logging():
	"""Test logging functionality"""
	logger = setup_agent_logging("test_session")
    
	# Test action logging
	action_id = logger.log_action(
		action_type="type",
		selector="#firstName",
		value="John",
		success=True,
		execution_time=0.5,
		page_url="https://example.com/apply"
	)
    
	logger.log_action(
		action_type="click",
		selector="#submit",
		success=False,
		error_message="Element not found",
		execution_time=1.0
	)
    
	# Test session end
	logger.log_session_end(
		final_state="form_filled",
		auto_submit_enabled=False,
		form_submitted=False
	)
    
	print(f"✅ Test session logged: {logger.session_id}")
	print(f"   Log files created in: {logger.log_dir}")
    
	# Test analysis
	analyzer = LogAnalyzer(str(logger.log_dir))
	analysis = analyzer.analyze_session(logger.session_id)
	print(f"   Analysis: {analysis['total_actions']} actions logged")

if __name__ == "__main__":
	test_logging()
