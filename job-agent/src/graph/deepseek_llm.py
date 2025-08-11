"""
DeepSeek LLM Service Integration for AI-First Field Classification
Real LLM service using DeepSeek API
"""

import json
import logging
import hashlib
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Define enums and data classes here to avoid import issues
class FieldComplexity(Enum):
    """Complexity levels for form fields"""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"

class FillStrategy(Enum):
    """Fill strategies for form fields"""
    SIMPLE_MAPPING = "simple_mapping"     # name, email, phone
    RAG_GENERATION = "rag_generation"     # essays, cover letters
    OPTION_SELECTION = "option_selection" # dropdowns, radio
    CONDITIONAL_LOGIC = "conditional"     # depends on other fields
    SKIP_FIELD = "skip"                   # assessments, out of scope

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

@dataclass
class AIFieldClassification:
    """AI-generated field classification result"""
    fill_strategy: FillStrategy
    complexity: FieldComplexity
    confidence: float
    reasoning: str
    mapped_to: Optional[str] = None
    requires_rag: bool = False
    estimated_time: float = 1.0
    max_length: Optional[int] = None
    question_extracted: Optional[str] = None
    priority: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill_strategy": self.fill_strategy.value,
            "complexity": self.complexity.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "mapped_to": self.mapped_to,
            "requires_rag": self.requires_rag,
            "estimated_time": self.estimated_time,
            "max_length": self.max_length,
            "question_extracted": self.question_extracted,
            "priority": self.priority
        }

class DeepSeekLLMService:
    """Real LLM service using DeepSeek API"""
    # (Full implementation from user message)
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.session = None
        self.default_params = {
            "temperature": 0.1,
            "max_tokens": 500,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        self.max_retries = 3
        self.retry_delay = 1.0
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    async def classify_field(self, prompt: str) -> Dict[str, Any]:
        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [
            {
                "role": "system",
                "content": """You are an expert AI system for analyzing web form fields in job applications. \nYou must respond with valid JSON only, no additional text or explanation.\nYour task is to classify fields and determine the best filling strategy."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            **self.default_params
        }
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making DeepSeek API request (attempt {attempt + 1})")
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        try:
                            classification_data = json.loads(content)
                            logger.info(f"DeepSeek classification successful")
                            return classification_data
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse DeepSeek JSON response: {e}")
                            logger.error(f"Raw response: {content}")
                            cleaned_response = self._extract_json_from_response(content)
                            if cleaned_response:
                                return cleaned_response
                    else:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API error {response.status}: {error_text}")
                        if response.status == 429:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        elif response.status >= 500:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        else:
                            break
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"DeepSeek API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    break
        logger.warning("All DeepSeek API attempts failed, using fallback classification")
        return self._get_fallback_classification(prompt)
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        import re
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        return None
    def _get_fallback_classification(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        if any(indicator in prompt_lower for indicator in ["first name", "fname", "given name"]):
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "trivial",
                "confidence": 0.70,
                "reasoning": "API failed, fallback detected first name field",
                "mapped_to": "personal.first_name",
                "requires_rag": False,
                "estimated_time": 0.5,
                "priority": 80
            }
        elif any(indicator in prompt_lower for indicator in ["email", "e-mail"]) or "type=\"email\"" in prompt_lower:
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "trivial",
                "confidence": 0.75,
                "reasoning": "API failed, fallback detected email field",
                "mapped_to": "personal.email",
                "requires_rag": False,
                "estimated_time": 0.5,
                "priority": 85
            }
        elif ("tag=\"textarea\"" in prompt_lower) and any(indicator in prompt_lower for indicator in ["cover letter", "why", "motivation"]):
            return {
                "fill_strategy": "rag_generation",
                "complexity": "complex",
                "confidence": 0.65,
                "reasoning": "API failed, fallback detected essay field",
                "mapped_to": None,
                "requires_rag": True,
                "estimated_time": 5.0,
                "priority": 60
            }
        elif any(indicator in prompt_lower for indicator in ["assessment", "test", "quiz", "coding"]):
            return {
                "fill_strategy": "skip_field",
                "complexity": "expert",
                "confidence": 0.80,
                "reasoning": "API failed, fallback detected assessment field",
                "mapped_to": None,
                "requires_rag": False,
                "estimated_time": 0.1,
                "priority": 5
            }
        else:
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "medium",
                "confidence": 0.40,
                "reasoning": "API failed, fallback to default classification",
                "mapped_to": None,
                "requires_rag": False,
                "estimated_time": 2.0,
                "priority": 50
            }

class DeepSeekFieldClassifier:
    """Field classifier using DeepSeek LLM"""
    def __init__(self, llm_service: DeepSeekLLMService):
        self.llm_service = llm_service
    async def classify(self, field_name: str, field_type: str, placeholder: str = "", required: bool = False) -> AIFieldClassification:
        prompt = f"""
        You are an expert AI system for analyzing web form fields in job applications.
        Classify the following field and suggest a filling strategy:

        Field Name: {field_name}
        Field Type: {field_type}
        Placeholder: {placeholder}
        Required: {required}

        Respond with valid JSON only, no additional text or explanation.
        """
        logger.info(f"Classifying field: {field_name} (type: {field_type})")
        classification_result = await self.llm_service.classify_field(prompt)
        return AIFieldClassification(**classification_result)
class IntelligentFieldClassifier:
    """Intelligent field classifier using DeepSeek LLM with context awareness"""
    def __init__(self, llm_service: DeepSeekLLMService, context: Optional[Dict[str, Any]] = None):
        self.llm_service = llm_service
        self.context = context or {}
    def update_context(self, new_context: Dict[str, Any]):
        self.context.update(new_context)
    async def classify(self, field_name: str, field_type: str, placeholder: str = "", required: bool = False) -> AIFieldClassification:
        context_str = json.dumps(self.context)
        prompt = f"""
        You are an expert AI system for analyzing web form fields in job applications.
        You have the following context about the applicant: {context_str}
        Classify the following field and suggest a filling strategy:

        Field Name: {field_name}
        Field Type: {field_type}
        Placeholder: {placeholder}
        Required: {required}

        Respond with valid JSON only, no additional text or explanation.
        """
        logger.info(f"Intelligently classifying field: {field_name} (type: {field_type}) with context: {self.context}")
        classification_result = await self.llm_service.classify_field(prompt)
        return AIFieldClassification(**classification_result)

# ...demo code from user message...
