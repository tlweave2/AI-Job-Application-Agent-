
from typing import Dict, Any, List

RAG_DRAFTER_PROMPT = """You are an expert at writing compelling job application responses using provided context.

Your task is to draft a response to a job application question using information from the candidate's resume and questionnaire.

QUESTION/PROMPT:
{question}

FIELD CONTEXT:
- Field Type: {field_type}
- Character Limit: {char_limit}
- Required: {is_required}
- Placeholder Text: "{placeholder}"

RETRIEVED CONTEXT:
{retrieved_context}

USER PROFILE:
{user_profile}

WRITING GUIDELINES:
1. **Stay Grounded**: Only use information from the provided context
2. **Be Specific**: Include concrete examples and details from resume/experience
3. **Match Tone**: Professional but personable for job applications
4. **Honor Limits**: Respect character/word limits strictly
5. **Answer Directly**: Address the specific question asked
6. **Show Value**: Highlight relevant skills and experience

RESPONSE REQUIREMENTS:
- Length: {target_length}
- Format: {response_format}
- Tone: Professional, enthusiastic, authentic
- Perspective: First person ("I", "my")

COMMON QUESTION PATTERNS:
- **Experience Questions**: Draw from work history, projects, achievements
- **Motivation Questions**: Connect personal goals with company/role
- **Skills Questions**: Provide specific examples of skill application
- **Challenge Questions**: Describe problems solved and lessons learned
- **Goals Questions**: Align career aspirations with opportunity

RESPONSE FORMAT:
{{
	"response": "The drafted response text that directly answers the question",
	"confidence": 0.95,
	"word_count": 150,
	"grounding_sources": ["specific resume sections or questionnaire items used"],
	"suggestions": ["optional suggestions for improvement or alternatives"]
}}

QUALITY CHECKS:
- Does the response directly answer the question?
- Is all information grounded in provided context?
- Does it stay within length limits?
- Is the tone appropriate for job applications?
- Are there specific, concrete examples?

If the provided context is insufficient to answer the question well, indicate this in the confidence score and suggestions.
"""

SIMPLE_RAG_PROMPT = """Write a job application response using the provided information.

Question: {question}
Character limit: {char_limit}

Your background:
{user_profile}

Relevant context:
{retrieved_context}

Write a professional response that answers the question using your background information:

{{
	"response": "Your response here",
	"confidence": 0.9,
	"word_count": 120
}}
"""

COVER_LETTER_PROMPT = """Draft a compelling cover letter section using the candidate's background.

Section: {section_type}
Target Length: {target_length}

Candidate Information:
{user_profile}

Relevant Experience:
{retrieved_context}

Job Context:
{job_context}

Write a {section_type} section that:
- Connects candidate experience to role requirements
- Shows enthusiasm for the opportunity  
- Demonstrates value the candidate would bring
- Uses specific examples from their background

{{
	"response": "Cover letter section content",
	"confidence": 0.95,
	"key_points": ["main points covered"],
	"word_count": 100
}}
"""

def format_rag_prompt(
	question: str,
	field_type: str,
	char_limit: int,
	is_required: bool,
	placeholder: str,
	retrieved_context: List[str],
	user_profile: Dict[str, Any],
	target_length: str = "medium",
	response_format: str = "paragraph",
	simple_mode: bool = False
) -> str:
	"""Format the RAG drafting prompt"""
    
	if simple_mode:
		return SIMPLE_RAG_PROMPT.format(
			question=question,
			char_limit=char_limit,
			user_profile=format_user_profile(user_profile),
			retrieved_context="\n".join(retrieved_context) if retrieved_context else "No specific context retrieved"
		)
    
	# Format retrieved context
	context_str = ""
	if retrieved_context:
		context_items = []
		for i, context in enumerate(retrieved_context, 1):
			context_items.append(f"{i}. {context}")
		context_str = "\n".join(context_items)
	else:
		context_str = "No specific context retrieved from resume/questionnaire"
    
	# Determine target length description
	if char_limit:
		if char_limit <= 100:
			target_length = f"Very brief ({char_limit} characters max)"
		elif char_limit <= 300:
			target_length = f"Short ({char_limit} characters max)"
		elif char_limit <= 500:
			target_length = f"Medium ({char_limit} characters max)"
		else:
			target_length = f"Long ({char_limit} characters max)"
	else:
		target_length = "Medium length (2-3 sentences)"
    
	return RAG_DRAFTER_PROMPT.format(
		question=question,
		field_type=field_type,
		char_limit=char_limit or "None specified",
		is_required=is_required,
		placeholder=placeholder,
		retrieved_context=context_str,
		user_profile=format_user_profile(user_profile),
		target_length=target_length,
		response_format=response_format
	)

def format_user_profile(user_profile: Dict[str, Any]) -> str:
	"""Format user profile information for RAG context"""
	if not user_profile:
		return "No user profile information available"
    
	profile_lines = []
    
	# Basic information
	if 'personal' in user_profile:
		personal = user_profile['personal']
		profile_lines.append("PERSONAL:")
		if personal.get('current_title'):
			profile_lines.append(f"  Current Role: {personal['current_title']}")
		if personal.get('current_company'):
			profile_lines.append(f"  Current Company: {personal['current_company']}")
    
	# Experience summary
	if 'experience' in user_profile:
		exp = user_profile['experience']
		profile_lines.append("EXPERIENCE:")
		if exp.get('years_programming'):
			profile_lines.append(f"  Programming Experience: {exp['years_programming']}")
		if exp.get('preferred_technologies'):
			tech_list = exp['preferred_technologies']
			if isinstance(tech_list, list):
				profile_lines.append(f"  Technologies: {', '.join(tech_list)}")
    
	# Preferences
	if 'preferences' in user_profile:
		prefs = user_profile['preferences']
		if prefs.get('remote_work'):
			profile_lines.append(f"Work Preferences: {prefs['remote_work']}")
    
	return "\n".join(profile_lines) if profile_lines else "Basic profile information available"

def identify_question_type(question: str) -> str:
	"""Identify the type of question being asked"""
	question_lower = question.lower()
    
	if any(word in question_lower for word in ["experience", "background", "worked", "projects"]):
		return "experience"
	elif any(word in question_lower for word in ["why", "interested", "motivation", "want"]):
		return "motivation"
	elif any(word in question_lower for word in ["skills", "strengths", "abilities", "capable"]):
		return "skills"
	elif any(word in question_lower for word in ["challenge", "difficult", "problem", "overcome"]):
		return "challenge"
	elif any(word in question_lower for word in ["goals", "future", "career", "aspir"]):
		return "goals"
	elif any(word in question_lower for word in ["cover letter", "introduction", "about yourself"]):
		return "cover_letter"
	else:
		return "general"

def get_length_guidelines(char_limit: int) -> Dict[str, Any]:
	"""Get writing guidelines based on character limit"""
	if char_limit <= 100:
		return {
			"sentences": "1-2 sentences",
			"style": "very concise",
			"focus": "single key point"
		}
	elif char_limit <= 300:
		return {
			"sentences": "2-3 sentences", 
			"style": "concise",
			"focus": "main point with brief example"
		}
	elif char_limit <= 500:
		return {
			"sentences": "3-4 sentences",
			"style": "balanced",
			"focus": "main point with supporting details"
		}
	else:
		return {
			"sentences": "4-6 sentences",
			"style": "detailed",
			"focus": "comprehensive answer with examples"
		}
