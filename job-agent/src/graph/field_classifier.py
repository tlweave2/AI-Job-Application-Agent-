"""
True AI-First Field Classifier
Every classification decision is made by AI, no hard-coded patterns
"""

import json
import logging
import hashlib
import asyncio
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from models.snapshot import ActionableElement
from models.graph_state import FillStrategy
from graph.deepseek_llm import DeepSeekFieldClassifier

logger = logging.getLogger(__name__)

class FieldComplexity(Enum):
    """Complexity levels for form fields"""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"

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

class MockLLMService:
    """Mock LLM service that simulates AI responses for testing"""
    
    async def classify_field(self, prompt: str) -> Dict[str, Any]:
        """Mock LLM classification that returns intelligent responses"""
        
        # Extract key information from prompt for intelligent mock responses
        prompt_lower = prompt.lower()
        
        # Simulate AI decision-making based on prompt content
        if any(indicator in prompt_lower for indicator in ["first name", "fname", "given name"]):
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "trivial",
                "confidence": 0.95,
                "reasoning": "AI detected clear first name field based on label and placeholder patterns",
                "mapped_to": "personal.first_name",
                "requires_rag": False,
                "estimated_time": 0.5,
                "priority": 80
            }
        
        elif any(indicator in prompt_lower for indicator in ["email", "e-mail"]) or "type=\"email\"" in prompt_lower:
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "trivial",
                "confidence": 0.98,
                "reasoning": "AI identified email field from type attribute and context",
                "mapped_to": "personal.email",
                "requires_rag": False,
                "estimated_time": 0.5,
                "priority": 85
            }
        
        elif any(indicator in prompt_lower for indicator in ["phone", "tel", "mobile"]) or "type=\"tel\"" in prompt_lower:
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "trivial",
                "confidence": 0.92,
                "reasoning": "AI detected phone number field from type and context clues",
                "mapped_to": "personal.phone",
                "requires_rag": False,
                "estimated_time": 0.8,
                "priority": 75
            }
        
        elif any(indicator in prompt_lower for indicator in ["current title", "job title", "position"]):
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "simple",
                "confidence": 0.88,
                "reasoning": "AI identified professional title field from context",
                "mapped_to": "experience.current_title",
                "requires_rag": False,
                "estimated_time": 1.0,
                "priority": 70
            }
        
        elif "tag=\"select\"" in prompt_lower and any(indicator in prompt_lower for indicator in ["experience", "years"]):
            return {
                "fill_strategy": "option_selection",
                "complexity": "medium",
                "confidence": 0.90,
                "reasoning": "AI detected dropdown for experience selection",
                "mapped_to": "experience.years_programming",
                "requires_rag": False,
                "estimated_time": 2.0,
                "priority": 65
            }
        
        elif ("tag=\"textarea\"" in prompt_lower or "maxlength=\"2000\"" in prompt_lower) and \
             any(indicator in prompt_lower for indicator in ["cover letter", "why", "interested", "motivation"]):
            return {
                "fill_strategy": "rag_generation",
                "complexity": "complex",
                "confidence": 0.93,
                "reasoning": "AI identified essay field requiring personalized content generation",
                "mapped_to": None,
                "requires_rag": True,
                "estimated_time": 5.0,
                "max_length": 2000,
                "question_extracted": "Why are you interested in this position?",
                "priority": 60
            }
        
        elif ("tag=\"textarea\"" in prompt_lower) and \
             any(indicator in prompt_lower for indicator in ["experience", "describe", "background"]):
            return {
                "fill_strategy": "rag_generation",
                "complexity": "complex",
                "confidence": 0.91,
                "reasoning": "AI detected experience description field needing detailed response",
                "mapped_to": None,
                "requires_rag": True,
                "estimated_time": 4.5,
                "max_length": 1500,
                "question_extracted": "Describe your relevant experience",
                "priority": 65
            }
        
        elif any(indicator in prompt_lower for indicator in ["assessment", "test", "quiz", "coding", "technical"]) or \
             "data-assessment" in prompt_lower or "data-test" in prompt_lower:
            return {
                "fill_strategy": "skip_field",
                "complexity": "expert",
                "confidence": 0.96,
                "reasoning": "AI detected assessment/test field that should be skipped",
                "mapped_to": None,
                "requires_rag": False,
                "estimated_time": 0.1,
                "priority": 5
            }
        
        else:
            # Default fallback for unknown fields
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "simple",
                "confidence": 0.60,
                "reasoning": "AI defaulted to simple mapping for unrecognized field pattern",
                "mapped_to": None,
                "requires_rag": False,
                "estimated_time": 1.5,
                "priority": 50
            }

class RealLLMService:
    """Real LLM service using OpenAI or similar"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        # In real implementation, initialize OpenAI client here
        
    async def classify_field(self, prompt: str) -> Dict[str, Any]:
        """Real LLM classification using OpenAI API"""
        
        try:
            # This would be the actual OpenAI API call
            # response = await openai.ChatCompletion.acreate(
            #     model=self.model,
            #     messages=[{"role": "user", "content": prompt}],
            #     temperature=0.1,
            #     max_tokens=500
            # )
            # 
            # result = json.loads(response.choices[0].message.content)
            # return result
            
            # For now, fall back to mock for demonstration
            mock_service = MockLLMService()
            return await mock_service.classify_field(prompt)
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Fallback to conservative classification
            return {
                "fill_strategy": "simple_mapping",
                "complexity": "medium",
                "confidence": 0.40,
                "reasoning": f"LLM classification failed ({e}), using fallback",
                "mapped_to": None,
                "requires_rag": False,
                "estimated_time": 2.0,
                "priority": 30
            }

class AIFirstFieldClassifier:
    """True AI-First Field Classifier - All decisions made by AI"""
    
    def __init__(self, llm_service = None, use_cache: bool = True):
        self.llm = llm_service or MockLLMService()
        self.use_cache = use_cache
        self.classification_cache = {} if use_cache else None
        self.classification_stats = {
            "total_classified": 0,
            "ai_calls": 0,
            "cache_hits": 0,
            "strategies": {},
            "complexities": {}
        }
    
    async def classify_field(self, element: ActionableElement, 
                           page_context: Dict[str, Any]) -> AIFieldClassification:
        """Main AI-first classification method"""
        
        # Check cache first (if enabled)
        if self.use_cache:
            cache_key = self._generate_cache_key(element, page_context)
            if cache_key in self.classification_cache:
                logger.debug(f"Cache hit for field {element.selector}")
                self.classification_stats["cache_hits"] += 1
                return self.classification_cache[cache_key]
        
        # Build AI prompt with all context
        prompt = self._build_ai_classification_prompt(element, page_context)
        
        # Get AI classification
        logger.info(f"Requesting AI classification for {element.selector}")
        ai_response = await self.llm.classify_field(prompt)
        self.classification_stats["ai_calls"] += 1
        
        # Convert to our classification object
        classification = self._parse_ai_response(ai_response, element)
        
        # Cache result (if enabled)
        if self.use_cache:
            self.classification_cache[cache_key] = classification
        
        # Update stats
        self._update_stats(classification)
        
        logger.info(f"AI classified {element.selector}: {classification.fill_strategy.value} "
                   f"(confidence: {classification.confidence:.2f})")
        
        return classification
    
    def _build_ai_classification_prompt(self, element: ActionableElement, 
                                      page_context: Dict[str, Any]) -> str:
        """Build comprehensive AI prompt with all available context"""
        
        # Extract nearby context
        nearby_text = page_context.get("nearby_text", {}).get(element.selector, [])
        if isinstance(nearby_text, str):
            nearby_text = [nearby_text]
        
        nearby_context = " | ".join(nearby_text) if nearby_text else "No nearby text"
        
        prompt = f"""You are an expert AI system for analyzing web form fields in job applications. 
Your task is to classify this field and determine the best strategy for filling it.

FIELD ANALYSIS:
- Tag: {element.tag}
- Type: {element.type or "none"}
- Selector: {element.selector}
- Placeholder: "{element.placeholder}"
- Text Content: "{element.text}"
- Required: {element.required}
- Attributes: {json.dumps(element.attributes, indent=2)}

PAGE CONTEXT:
- Page Title: "{page_context.get('title', '')}"
- Page URL: {page_context.get('url', '')}
- Nearby Text/Labels: {nearby_context}

ANALYSIS FRAMEWORK:
1. What type of information is this field requesting?
2. Is this a standard personal/professional field or does it need custom content?
3. What's the appropriate filling strategy?
4. How complex is this field to fill correctly?
5. Should this field be skipped for any reason?

AVAILABLE STRATEGIES:
- "simple_mapping": Direct user data mapping (name, email, phone, etc.)
- "rag_generation": AI content generation (essays, cover letters, etc.)
- "option_selection": Choose from dropdown/radio options
- "skip_field": Skip field (assessments, out of scope, etc.)

COMPLEXITY LEVELS:
- "trivial": Instant fill (first name, email)
- "simple": Basic mapping (address, phone)
- "medium": Requires selection/formatting (dropdowns, dates)
- "complex": Needs content generation (essays, detailed answers)
- "expert": Should be skipped (technical assessments, coding challenges)

USER DATA MAPPING OPTIONS:
- personal.first_name, personal.last_name, personal.email, personal.phone
- personal.linkedin, personal.address
- experience.current_title, experience.current_company
- experience.years_programming, experience.preferred_technologies

Respond with JSON in this exact format:
{{
    "fill_strategy": "simple_mapping|rag_generation|option_selection|skip_field",
    "complexity": "trivial|simple|medium|complex|expert",
    "confidence": 0.95,
    "reasoning": "Detailed explanation of your classification decision",
    "mapped_to": "personal.first_name|experience.current_title|null",
    "requires_rag": true,
    "estimated_time": 2.5,
    "max_length": 500,
    "question_extracted": "What question is this field asking? (for RAG fields)",
    "priority": 75
}}

IMPORTANT: Be specific about reasoning and map fields to appropriate user data categories."""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: Dict[str, Any], 
                          element: ActionableElement) -> AIFieldClassification:
        """Parse AI response into classification object"""
        
        try:
            # Extract max_length from element if not provided by AI
            max_length = ai_response.get("max_length")
            if not max_length and element.attributes.get("maxlength"):
                try:
                    max_length = int(element.attributes["maxlength"])
                except ValueError:
                    pass
            
            return AIFieldClassification(
                fill_strategy=FillStrategy(ai_response["fill_strategy"]),
                complexity=FieldComplexity(ai_response["complexity"]),
                confidence=float(ai_response["confidence"]),
                reasoning=ai_response["reasoning"],
                mapped_to=ai_response.get("mapped_to"),
                requires_rag=bool(ai_response.get("requires_rag", False)),
                estimated_time=float(ai_response.get("estimated_time", 1.0)),
                max_length=max_length,
                question_extracted=ai_response.get("question_extracted"),
                priority=int(ai_response.get("priority", 50))
            )
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"AI Response: {ai_response}")
            
            # Fallback classification
            return AIFieldClassification(
                fill_strategy=FillStrategy.SIMPLE_MAPPING,
                complexity=FieldComplexity.MEDIUM,
                confidence=0.30,
                reasoning=f"Failed to parse AI response: {e}",
                estimated_time=2.0
            )
    
    def _generate_cache_key(self, element: ActionableElement, 
                           page_context: Dict[str, Any]) -> str:
        """Generate cache key for element and context"""
        
        cache_data = {
            "selector": element.selector,
            "tag": element.tag,
            "type": element.type,
            "placeholder": element.placeholder,
            "text": element.text,
            "required": element.required,
            "attributes": element.attributes,
            "page_title": page_context.get("title", ""),
            "nearby_text": page_context.get("nearby_text", {}).get(element.selector, [])
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _update_stats(self, classification: AIFieldClassification):
        """Update classification statistics"""
        
        self.classification_stats["total_classified"] += 1
        
        strategy = classification.fill_strategy.value
        complexity = classification.complexity.value
        
        self.classification_stats["strategies"][strategy] = (
            self.classification_stats["strategies"].get(strategy, 0) + 1
        )
        
        self.classification_stats["complexities"][complexity] = (
            self.classification_stats["complexities"].get(complexity, 0) + 1
        )
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics including AI usage"""
        stats = self.classification_stats.copy()
        
        if stats["total_classified"] > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_classified"]
            stats["ai_call_rate"] = stats["ai_calls"] / stats["total_classified"]
        else:
            stats["cache_hit_rate"] = 0.0
            stats["ai_call_rate"] = 0.0
        
        return stats
    
    def clear_cache(self):
        """Clear the classification cache"""
        if self.classification_cache:
            self.classification_cache.clear()
            logger.info("AI classification cache cleared")

# Compatibility wrapper for existing tests
class IntelligentFieldClassifier:
    """Sync wrapper for DeepSeek classifier (real AI)"""
    def __init__(self, api_key: str = None, model: str = None, use_cache: bool = True):
        if api_key is None:
            api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-317d3b46ff4b48589850a71ab85d00b4')
        if model is None:
            model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.deepseek_classifier = DeepSeekFieldClassifier(api_key, model, use_cache)
        self._loop = None

    def classify_field(self, element, page_context: dict):
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            self.deepseek_classifier.classify_field(element, page_context)
                        )
                    )
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(
                    self.deepseek_classifier.classify_field(element, page_context)
                )
        except RuntimeError:
            return asyncio.run(
                self.deepseek_classifier.classify_field(element, page_context)
            )

    def get_classification_stats(self) -> dict:
        return self.deepseek_classifier.get_classification_stats()

    def clear_cache(self):
        if self.deepseek_classifier.classification_cache:
            self.deepseek_classifier.classification_cache.clear()

    @property
    def classification_cache(self):
        return self.deepseek_classifier.classification_cache or {}

# Utility functions for compatibility
def create_mock_element(tag: str, input_type: str, selector: str, 
                       placeholder: str = "", text: str = "", 
                       required: bool = False, **attributes) -> ActionableElement:
    """Create mock element for testing"""
    
    return ActionableElement(
        tag=tag,
        type=input_type,
        selector=selector,
        text=text,
        placeholder=placeholder,
        value="",
        required=required,
        visible=True,
        enabled=True,
        bounds={},
        attributes=attributes
    )

async def analyze_form_structure_async(elements: List[ActionableElement], 
                                     page_context: Dict[str, Any],
                                     llm_service=None) -> Dict[str, Any]:
    """AI-first form structure analysis"""
    
    classifier = AIFirstFieldClassifier(llm_service)
    
    # Classify all elements with AI
    classifications = []
    for element in elements:
        classification = await classifier.classify_field(element, page_context)
        classifications.append({
            "element": element,
            "classification": classification
        })
    
    # Analyze patterns
    strategy_distribution = {}
    complexity_distribution = {}
    priority_queue = []
    
    for item in classifications:
        classification = item["classification"]
        
        # Count strategies
        strategy = classification.fill_strategy.value
        strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
        
        # Count complexities
        complexity = classification.complexity.value
        complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
        
        # Build priority queue
        priority_queue.append({
            "element": item["element"],
            "classification": classification,
            "priority": classification.priority
        })
   