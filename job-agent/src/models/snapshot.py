
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ActionableElement:
	"""Represents an element that can be interacted with"""
	tag: str
	type: Optional[str]
	selector: str
	text: str
	placeholder: str
	value: str
	required: bool
	visible: bool
	enabled: bool
	bounds: Dict[str, float]
	attributes: Dict[str, str]
    
	@property
	def is_input_field(self) -> bool:
		"""Check if this is an input field (text, email, etc.)"""
		return self.tag in ['input', 'textarea'] and self.type not in ['submit', 'button', 'checkbox', 'radio']
    
	@property
	def is_button(self) -> bool:
		"""Check if this is a clickable button"""
		return (self.tag == 'button' or 
				self.type in ['submit', 'button'] or
				'button' in self.attributes.get('role', ''))
    
	@property
	def is_select(self) -> bool:
		"""Check if this is a select dropdown"""
		return self.tag == 'select'
    
	@property
	def is_file_input(self) -> bool:
		"""Check if this is a file upload input"""
		return self.tag == 'input' and self.type == 'file'

@dataclass
class BrowserSnapshot:
	"""Structured representation of the page state"""
	url: str
	title: str
	actionable_elements: List[ActionableElement]
	form_count: int
	submit_buttons: List[ActionableElement]
	timestamp: float
    
	@property
	def input_fields(self) -> List[ActionableElement]:
		"""Get all input fields (text, email, etc.)"""
		return [el for el in self.actionable_elements if el.is_input_field]
    
	@property
	def buttons(self) -> List[ActionableElement]:
		"""Get all clickable buttons"""
		return [el for el in self.actionable_elements if el.is_button]
    
	@property
	def select_fields(self) -> List[ActionableElement]:
		"""Get all select dropdowns"""
		return [el for el in self.actionable_elements if el.is_select]
    
	@property
	def file_inputs(self) -> List[ActionableElement]:
		"""Get all file upload inputs"""
		return [el for el in self.actionable_elements if el.is_file_input]
    
	@property
	def required_fields(self) -> List[ActionableElement]:
		"""Get all required fields"""
		return [el for el in self.actionable_elements if el.required]
    
	def find_element_by_text(self, text: str, case_sensitive: bool = False) -> Optional[ActionableElement]:
		"""Find element by text content"""
		search_text = text if case_sensitive else text.lower()
        
		for element in self.actionable_elements:
			element_text = element.text if case_sensitive else element.text.lower()
			if search_text in element_text:
				return element
		return None
    
	def find_element_by_placeholder(self, placeholder: str, case_sensitive: bool = False) -> Optional[ActionableElement]:
		"""Find element by placeholder text"""
		search_placeholder = placeholder if case_sensitive else placeholder.lower()
        
		for element in self.actionable_elements:
			element_placeholder = element.placeholder if case_sensitive else element.placeholder.lower()
			if search_placeholder in element_placeholder:
				return element
		return None
    
	def get_summary(self) -> Dict[str, int]:
		"""Get a summary of elements on the page"""
		return {
			"total_elements": len(self.actionable_elements),
			"input_fields": len(self.input_fields),
			"buttons": len(self.buttons),
			"select_fields": len(self.select_fields),
			"file_inputs": len(self.file_inputs),
			"required_fields": len(self.required_fields),
			"submit_buttons": len(self.submit_buttons),
			"forms": self.form_count
		}
