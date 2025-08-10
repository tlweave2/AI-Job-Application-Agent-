
from typing import Dict, Any, List

PLANNER_PROMPT = """You are an expert at planning form-filling actions for job application automation.

Your task is to create a plan of 3-6 atomic actions to fill out this job application form efficiently and accurately.

CURRENT PAGE STATE:
URL: {url}
Title: {title}
Cycle: {cycle_number}

AVAILABLE ELEMENTS:
{elements_summary}

USER DATA AVAILABLE:
{user_data}

EXECUTION CONTEXT:
{execution_context}

PLANNING INSTRUCTIONS:
1. **Prioritize Required Fields**: Focus on fields marked as required first
2. **Standard Job Fields**: Look for common patterns (name, email, phone, experience, etc.)
3. **Batch Similar Actions**: Group related form fields together
4. **Conservative Approach**: Only include actions you're confident will succeed
5. **Submit Logic**: Only include submit if ALL required fields can be filled and form is 90%+ complete

FIELD MAPPING GUIDELINES:
- first_name/firstName → personal.first_name
- last_name/lastName → personal.last_name  
- email → personal.email
- phone/phoneNumber → personal.phone
- experience/years → experience.years_programming
- Cover letter/motivation → Use RAG for long-form responses

ACTION TYPES:
- "type": Enter text in input/textarea fields
- "click": Click buttons, checkboxes, radio buttons
- "select": Choose option from dropdown menus
- "upload": Upload files to file input fields

RESPONSE FORMAT:
{{
	"actions": [
		{{
			"type": "type|click|select|upload",
			"selector": "exact_selector_from_elements_above",
			"value": "value_to_enter_or_select",
			"reasoning": "why this action and why this value"
		}}
	],
	"reasoning": "Overall strategy for this batch of actions and why these specific fields were chosen",
	"confidence": 0.95,
	"includes_submit": false,
	"estimated_completion": 0.75,
	"priority": "high"
}}

VALIDATION RULES:
- Only use selectors that appear in the elements list above
- Values must come from user data or be reasonable defaults
- estimated_completion: 0.0-1.0 representing form completion after these actions
- confidence: 0.0-1.0 representing likelihood of successful execution
- includes_submit: true only if form will be 90%+ complete and all required fields filled

PRIORITY LEVELS:
- "critical": Required fields that block submission
- "high": Important fields that significantly improve application
- "normal": Standard fields that should be filled
- "low": Optional fields that can be skipped if needed
"""

SIMPLE_PLANNER_PROMPT = """Plan actions to fill this job application form.

Available elements: {elements_summary}
User data: {user_data}

Create 3-6 actions to fill the most important fields first.

Response format:
{{
	"actions": [
		{{"type": "type", "selector": "#firstName", "value": "John", "reasoning": "Fill required first name field"}}
	],
	"reasoning": "Fill basic required information first",
	"confidence": 0.9,
	"includes_submit": false,
	"estimated_completion": 0.6
}}
"""

RAG_FIELD_INDICATORS = [
	"cover letter",
	"motivation",
	"why do you want",
	"tell us about",
	"describe your",
	"explain your",
	"what interests you",
	"additional information",
	"comments",
	"message to employer"
]

def format_planner_prompt(
	url: str,
	title: str,
	cycle_number: int,
	elements_summary: str,
	user_data: Dict[str, Any],
	execution_context: Dict[str, Any] = None,
	simple_mode: bool = False
) -> str:
	"""Format the action planning prompt"""
    
	if simple_mode:
		return SIMPLE_PLANNER_PROMPT.format(
			elements_summary=elements_summary,
			user_data=format_user_data(user_data)
		)
    
	context_str = ""
	if execution_context:
		context_items = []
		for key, value in execution_context.items():
			context_items.append(f"- {key}: {value}")
		context_str = "\n".join(context_items)
	else:
		context_str = "- First planning cycle\n- No previous actions executed"
    
	return PLANNER_PROMPT.format(
		url=url,
		title=title,
		cycle_number=cycle_number,
		elements_summary=elements_summary,
		user_data=format_user_data(user_data),
		execution_context=context_str
	)

def format_user_data(user_data: Dict[str, Any]) -> str:
	"""Format user data for inclusion in prompts"""
	if not user_data:
		return "No user data available"
    
	formatted_lines = []
    
	# Personal information
	if 'personal' in user_data:
		formatted_lines.append("PERSONAL:")
		personal = user_data['personal']
		for key, value in personal.items():
			if value:  # Only include non-empty values
				formatted_lines.append(f"  - {key}: {value}")
    
	# Experience information  
	if 'experience' in user_data:
		formatted_lines.append("EXPERIENCE:")
		experience = user_data['experience']
		for key, value in experience.items():
			if value:
				if isinstance(value, list):
					formatted_lines.append(f"  - {key}: {', '.join(value)}")
				else:
					formatted_lines.append(f"  - {key}: {value}")
    
	# Preferences
	if 'preferences' in user_data:
		formatted_lines.append("PREFERENCES:")
		preferences = user_data['preferences']
		for key, value in preferences.items():
			if value:
				formatted_lines.append(f"  - {key}: {value}")
    
	return "\n".join(formatted_lines) if formatted_lines else "No structured user data available"

def identify_rag_fields(elements_summary: str) -> List[str]:
	"""Identify fields that should use RAG for content generation"""
	rag_fields = []
	elements_lower = elements_summary.lower()
    
	for indicator in RAG_FIELD_INDICATORS:
		if indicator in elements_lower:
			# Extract the actual field selector if possible
			lines = elements_summary.split('\n')
			for line in lines:
				if indicator in line.lower():
					rag_fields.append(line.strip())
					break
    
	return rag_fields
