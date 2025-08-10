
from typing import Dict, Any

REPAIR_PROMPT = """You are an expert at diagnosing and fixing failed web automation actions.

An action has failed and needs to be repaired. Analyze the failure and suggest a corrected action.

FAILED ACTION:
Type: {action_type}
Selector: {action_selector}
Value: {action_value}
Reasoning: {action_reasoning}

ERROR DETAILS:
Error Message: {error_message}
Execution Context: {execution_context}

CURRENT PAGE STATE:
URL: {url}
Elements Available: {elements_summary}

COMMON FAILURE PATTERNS:
1. **Selector Issues**:
   - Element selector changed (dynamic IDs, page updates)
   - Element not visible/enabled at execution time
   - Selector too specific or too generic

2. **Value Issues**:
   - Value format incorrect for field type
   - Value too long for field constraints
   - Required format not met (e.g., email, phone)

3. **Timing Issues**:
   - Element not loaded when action executed
   - Page still loading/changing
   - Need to wait for other actions to complete

4. **Action Type Issues**:
   - Wrong action type for element (click vs type)
   - Element requires different interaction method

REPAIR STRATEGIES:
1. **Try Alternative Selectors**: Look for similar elements with different selectors
2. **Adjust Values**: Format or shorten values to meet field requirements
3. **Change Action Type**: Use different interaction method
4. **Add Wait**: Include wait before action if timing issue
5. **Break Into Steps**: Split complex action into simpler parts

RESPONSE FORMAT:
{{
	"suggested_action": {{
		"type": "type|click|select|upload|wait",
		"selector": "corrected_selector_from_current_elements",
		"value": "corrected_value_if_applicable"
	}},
	"reasoning": "Detailed explanation of what likely caused the failure and how this repair addresses it",
	"confidence": 0.85,
	"repair_type": "selector_fix|value_fix|type_change|timing_fix|alternative_approach"
}}

REPAIR TYPE DEFINITIONS:
- selector_fix: Changed element selector to target correct element
- value_fix: Modified the value to meet field requirements
- type_change: Changed action type (e.g., click instead of type)
- timing_fix: Added wait or delay to handle timing issues
- alternative_approach: Completely different strategy to achieve same goal

CONFIDENCE GUIDELINES:
- 0.9-1.0: Very confident this will fix the issue
- 0.7-0.9: Good chance of success, clear diagnosis
- 0.5-0.7: Reasonable attempt, some uncertainty
- 0.0-0.5: Low confidence, may need human intervention

If no reasonable repair is possible, set confidence to 0.0 and explain why in the reasoning.
"""

SIMPLE_REPAIR_PROMPT = """An automation action failed. Suggest a fix.

Failed Action: {action_type} on {action_selector} with value "{action_value}"
Error: {error_message}

Current elements: {elements_summary}

Suggest a corrected action:
{{
	"suggested_action": {{
		"type": "corrected_action_type",
		"selector": "corrected_selector", 
		"value": "corrected_value"
	}},
	"reasoning": "Why it failed and how this fixes it",
	"confidence": 0.8
}}
"""

def format_repair_prompt(
	action_type: str,
	action_selector: str,
	action_value: str,
	action_reasoning: str,
	error_message: str,
	url: str,
	elements_summary: str,
	execution_context: Dict[str, Any] = None,
	simple_mode: bool = False
) -> str:
	"""Format the action repair prompt"""
    
	if simple_mode:
		return SIMPLE_REPAIR_PROMPT.format(
			action_type=action_type,
			action_selector=action_selector,
			action_value=action_value or "None",
			error_message=error_message,
			elements_summary=elements_summary
		)
    
	context_str = ""
	if execution_context:
		context_items = []
		for key, value in execution_context.items():
			context_items.append(f"- {key}: {value}")
		context_str = "\n".join(context_items)
	else:
		context_str = "- No additional execution context"
    
	return REPAIR_PROMPT.format(
		action_type=action_type,
		action_selector=action_selector,
		action_value=action_value or "None",
		action_reasoning=action_reasoning or "No reasoning provided",
		error_message=error_message,
		execution_context=context_str,
		url=url,
		elements_summary=elements_summary
	)

def classify_error_type(error_message: str) -> str:
	"""Classify the type of error based on error message"""
	error_lower = error_message.lower()
    
	if any(keyword in error_lower for keyword in ["not found", "no such element", "selector"]):
		return "selector_issue"
	elif any(keyword in error_lower for keyword in ["timeout", "not visible", "not enabled"]):
		return "timing_issue"
	elif any(keyword in error_lower for keyword in ["invalid", "format", "constraint"]):
		return "value_issue"
	elif any(keyword in error_lower for keyword in ["click", "type", "interaction"]):
		return "action_type_issue"
	else:
		return "unknown_issue"

def suggest_alternative_selectors(failed_selector: str, available_elements: str) -> list:
	"""Suggest alternative selectors based on failed selector and available elements"""
	alternatives = []
    
	# Extract element type from failed selector
	if "#" in failed_selector:
		# ID selector failed, look for name or data attributes
		element_name = failed_selector.replace("#", "")
		if f'name="{element_name}"' in available_elements:
			alternatives.append(f'[name="{element_name}"]')
    
	elif '[name=' in failed_selector:
		# Name selector failed, look for ID or placeholder
		element_name = failed_selector.split('"')[1]
		if f'id="{element_name}"' in available_elements:
			alternatives.append(f'#{element_name}')
    
	# Add xpath fallback suggestion
	alternatives.append("xpath_fallback_needed")
    
	return alternatives
