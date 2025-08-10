
import re
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
	"""Result of field validation"""
	is_valid: bool
	normalized_value: str
	error_message: Optional[str] = None
	confidence: float = 1.0

class FieldValidator:
	"""Utilities for validating and normalizing form field values"""
    
	# Common regex patterns
	EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
	PHONE_PATTERN = re.compile(r'^[\+]?[1-9]?[\d\s\-\(\)\.]{7,15}$')
	# (Removed invalid regex line)
	URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].*$', re.IGNORECASE)

	@staticmethod
	def validate_email(value: str) -> ValidationResult:
		"""Validate and normalize email address"""
		if not value:
			return ValidationResult(False, "", "Email is required")
        
		# Basic cleanup
		email = value.strip().lower()
        
		# Check format
		if not FieldValidator.EMAIL_PATTERN.match(email):
			return ValidationResult(False, email, "Invalid email format")
        
		return ValidationResult(True, email)
    
	@staticmethod
	def validate_phone(value: str) -> ValidationResult:
		"""Validate and normalize phone number"""
		if not value:
			return ValidationResult(False, "", "Phone number is required")
        
		# Remove common formatting
		phone = re.sub(r'[^\d\+]', '', value.strip())
        
		# Add US country code if missing and looks like US number
		if len(phone) == 10 and phone.isdigit():
			phone = "1" + phone
		elif len(phone) == 11 and phone.startswith("1"):
			pass  # Already has country code
        
		# Validate length and format
		if len(phone) < 10 or len(phone) > 15:
			return ValidationResult(False, phone, "Invalid phone number length")
        
		# Format for display (US format)
		if len(phone) == 11 and phone.startswith("1"):
			formatted = f"({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
		else:
			formatted = phone
        
		return ValidationResult(True, formatted)
    
	@staticmethod
	def validate_name(value: str, field_name: str = "name") -> ValidationResult:
		"""Validate name fields"""
		if not value:
			return ValidationResult(False, "", f"{field_name} is required")
        
		# Basic cleanup
		name = value.strip().title()
        
		# Check for reasonable name patterns
		if len(name) < 2:
			return ValidationResult(False, name, f"{field_name} too short")
        
		if len(name) > 50:
			return ValidationResult(False, name, f"{field_name} too long")
        
		# Check for valid characters (letters, spaces, hyphens, apostrophes)
		if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
			return ValidationResult(False, name, f"{field_name} contains invalid characters")
        
		return ValidationResult(True, name)
    
	@staticmethod
	def validate_url(value: str, field_name: str = "URL") -> ValidationResult:
		"""Validate URL fields (LinkedIn, portfolio, etc.)"""
		if not value:
			return ValidationResult(True, "", "")  # Usually optional
        
		# Add protocol if missing
		url = value.strip()
		EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
		PHONE_PATTERN = re.compile(r'^[\+]?[1-9]?[\d\s\-\(\)\.]{7,15}$')
		URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].*$', re.IGNORECASE)
		if not FieldValidator.URL_PATTERN.match(url):
			return ValidationResult(False, url, f"Invalid {field_name} format")
        
		return ValidationResult(True, url)
    
	@staticmethod
	def validate_text_length(value: str, max_length: int, field_name: str = "field") -> ValidationResult:
		"""Validate text field length"""
		if not value:
			return ValidationResult(False, "", f"{field_name} is required")
		text = value.strip()
		if len(text) > max_length:
			# Truncate with ellipsis
			truncated = text[:max_length-3] + "..."
			return ValidationResult(
				False, 
				truncated, 
				f"{field_name} too long (max {max_length} characters)",
				confidence=0.7
			)
		return ValidationResult(True, text)


class FormVerifier:
	"""Utilities for verifying form field values after entry"""
	@staticmethod
	def verify_field_value(expected: str, actual: str, field_type: str = "text") -> Tuple[bool, str]:
		"""Verify that a field contains the expected value"""
		if not expected and not actual:
			return True, "Both empty - OK"
        
		# Normalize values for comparison
		expected_norm = expected.strip() if expected else ""
		actual_norm = actual.strip() if actual else ""
        
		# Exact match
		if expected_norm == actual_norm:
			return True, "Exact match"
        
		# Type-specific verification
		if field_type == "email":
			return FormVerifier._verify_email_match(expected_norm, actual_norm)
		elif field_type == "phone":
			return FormVerifier._verify_phone_match(expected_norm, actual_norm)
		elif field_type == "url":
			return FormVerifier._verify_url_match(expected_norm, actual_norm)
		else:
			return FormVerifier._verify_text_match(expected_norm, actual_norm)
    
	@staticmethod
	def _verify_email_match(expected: str, actual: str) -> Tuple[bool, str]:
		"""Verify email field match with normalization"""
		exp_email = expected.lower().strip()
		act_email = actual.lower().strip()
        
		if exp_email == act_email:
			return True, "Email match"
        
		# Check if it's close (minor formatting differences)
		if exp_email.replace('.', '').replace('_', '') == act_email.replace('.', '').replace('_', ''):
			return True, "Email match (formatting differences)"
        
		return False, f"Email mismatch: expected '{expected}', got '{actual}'"
    
	@staticmethod
	def _verify_phone_match(expected: str, actual: str) -> Tuple[bool, str]:
		"""Verify phone field match with normalization"""
		# Extract just digits for comparison
		exp_digits = re.sub(r'\D', '', expected)
		act_digits = re.sub(r'\D', '', actual)
        
		# Remove country code if present for comparison
		if exp_digits.startswith('1') and len(exp_digits) == 11:
			exp_digits = exp_digits[1:]
		if act_digits.startswith('1') and len(act_digits) == 11:
			act_digits = act_digits[1:]
        
		if exp_digits == act_digits:
			return True, "Phone match"
        
		return False, f"Phone mismatch: expected '{expected}', got '{actual}'"
    
	@staticmethod
	def _verify_url_match(expected: str, actual: str) -> Tuple[bool, str]:
		"""Verify URL field match with normalization"""
		# Normalize protocols
		exp_url = expected.replace('http://', 'https://').strip('/')
		act_url = actual.replace('http://', 'https://').strip('/')
        
		if exp_url == act_url:
			return True, "URL match"
        
		return False, f"URL mismatch: expected '{expected}', got '{actual}'"
    
	@staticmethod
	def _verify_text_match(expected: str, actual: str) -> Tuple[bool, str]:
		"""Verify text field match with some tolerance"""
		# Case insensitive comparison
		if expected.lower() == actual.lower():
			return True, "Text match (case insensitive)"
        
		# Check if one contains the other (for truncated fields)
		if expected.lower() in actual.lower() or actual.lower() in expected.lower():
			return True, "Text match (partial)"
        
		# Check similarity for typos
		similarity = FormVerifier._calculate_similarity(expected.lower(), actual.lower())
		if similarity > 0.85:
			return True, f"Text match (similar: {similarity:.2f})"
        
		return False, f"Text mismatch: expected '{expected}', got '{actual}'"
    
	@staticmethod
	def _calculate_similarity(str1: str, str2: str) -> float:
		"""Calculate simple string similarity (Levenshtein-based)"""
		if not str1 and not str2:
			return 1.0
		if not str1 or not str2:
			return 0.0
        
		# Simple similarity calculation
		longer = str1 if len(str1) > len(str2) else str2
		shorter = str2 if len(str1) > len(str2) else str1
        
		if len(longer) == 0:
			return 1.0
        
		# Count matching characters
		matches = sum(1 for a, b in zip(longer, shorter) if a == b)
		return matches / len(longer)

def validate_user_data(user_data: Dict[str, Any]) -> Dict[str, ValidationResult]:
	"""Validate all user data fields"""
	results = {}
    
	if 'personal' in user_data:
		personal = user_data['personal']
        
		# Validate required personal fields
		if 'first_name' in personal:
			results['first_name'] = FieldValidator.validate_name(personal['first_name'], "First name")
        
		if 'last_name' in personal:
			results['last_name'] = FieldValidator.validate_name(personal['last_name'], "Last name")
        
		if 'email' in personal:
			results['email'] = FieldValidator.validate_email(personal['email'])
        
		if 'phone' in personal:
			results['phone'] = FieldValidator.validate_phone(personal['phone'])
        
		if 'linkedin' in personal:
			results['linkedin'] = FieldValidator.validate_url(personal['linkedin'], "LinkedIn URL")
    
	return results

# Test function
def test_validation():
	"""Test validation functions"""
	test_cases = [
		("john.doe@example.com", FieldValidator.validate_email, True),
		("invalid-email", FieldValidator.validate_email, False),
		("555-123-4567", FieldValidator.validate_phone, True),
		("123", FieldValidator.validate_phone, False),
		("John", FieldValidator.validate_name, True),
		("", FieldValidator.validate_name, False),
	]
    
	print("🧪 Testing validation functions:")
	for value, validator, should_pass in test_cases:
		result = validator(value)
		status = "✅" if result.is_valid == should_pass else "❌"
		print(f"  {status} {validator.__name__}('{value}') -> {result.is_valid}")

if __name__ == "__main__":
	test_validation()
