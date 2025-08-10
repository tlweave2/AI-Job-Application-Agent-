
from typing import Dict, Any

AUTH_CLASSIFIER_PROMPT = """You are an expert at analyzing web pages to determine authentication state for job application automation.

Given this page snapshot, determine the authentication state and recommend the next action.

PAGE INFORMATION:
URL: {url}
Title: {title}
Forms Present: {form_count}

ELEMENTS FOUND:
{elements_summary}

CONTEXT:
{auth_context}

ANALYSIS INSTRUCTIONS:
1. Look for clear indicators of each auth state:
   - LOGIN_REQUIRED: Login forms, sign-in buttons, "please log in" messages
   - CAPTCHA_PRESENT: CAPTCHA challenges, "I'm not a robot" checkboxes
   - TWO_FA_REQUIRED: 2FA prompts, SMS code inputs, authenticator requests
   - BLOCKED: Access denied, IP blocked, rate limiting messages
   - SESSION_EXPIRED: Session timeout messages, "please log in again"
   - REGISTRATION_REQUIRED: "Create account" required before proceeding
   - READY: Job application form is visible and accessible

2. Consider element types and text content carefully
3. Be conservative - if uncertain, classify as UNKNOWN rather than READY

RESPONSE FORMAT:
Respond with JSON in this exact format:
{{
	"state": "ready|login_required|captcha_present|two_fa_required|blocked|session_expired|registration_required|unknown",
	"next_action": "proceed|pause_for_human|skip_page|retry_later|terminate",
	"reason": "Clear explanation of why you chose this state based on specific elements found",
	"confidence": 0.95,
	"detected_elements": {{
		"login_indicators": ["specific selectors or text that indicate login needed"],
		"form_indicators": ["selectors for job application form elements"],
		"blocking_indicators": ["selectors or text that indicate blocking"]
	}},
	"suggested_wait_time": 30
}}

STATE DEFINITIONS:
- ready: Page shows job application form, no auth barriers
- login_required: Must log in to access application form
- captcha_present: CAPTCHA challenge is blocking access
- two_fa_required: Two-factor authentication prompt visible
- blocked: Access denied, IP blocked, or similar blocking
- session_expired: Previous session expired, need to re-authenticate
- registration_required: Must create account before applying
- unknown: Cannot determine state with confidence

NEXT ACTION DEFINITIONS:
- proceed: Continue with form filling automation
- pause_for_human: Stop and require human intervention
- skip_page: Skip this application entirely
- retry_later: Wait and try again (for temporary blocks)
- terminate: End the automation process

CONFIDENCE GUIDELINES:
- 0.9-1.0: Very clear indicators present
- 0.7-0.9: Good indicators but some ambiguity
- 0.5-0.7: Moderate confidence, some uncertainty
- 0.0-0.5: Low confidence, mostly guessing
"""

SIMPLE_AUTH_PROMPT = """Analyze this job application page and determine if it's ready for form filling.

URL: {url}
Title: {title}

Elements: {elements_summary}

Is this page ready for job application form filling, or does it require authentication?

Respond with JSON:
{{
	"state": "ready|login_required|captcha_present|blocked|unknown",
	"next_action": "proceed|pause_for_human|skip_page",
	"reason": "Brief explanation",
	"confidence": 0.85
}}
"""

def format_auth_prompt(
	url: str,
	title: str,
	form_count: int,
	elements_summary: str,
	auth_context: Dict[str, Any] = None,
	simple_mode: bool = False
) -> str:
	"""Format the authentication classification prompt"""
    
	if simple_mode:
		return SIMPLE_AUTH_PROMPT.format(
			url=url,
			title=title,
			elements_summary=elements_summary
		)
    
	context_str = ""
	if auth_context:
		context_items = []
		for key, value in auth_context.items():
			context_items.append(f"- {key}: {value}")
		context_str = "\n".join(context_items)
	else:
		context_str = "- No additional context provided"
    
	return AUTH_CLASSIFIER_PROMPT.format(
		url=url,
		title=title,
		form_count=form_count,
		elements_summary=elements_summary,
		auth_context=context_str
	)
