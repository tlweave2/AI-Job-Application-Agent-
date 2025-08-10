"""
AI-First Field Classification - No Hard-Coded Patterns
Every classification decision is made by AI, not predetermined rules
"""

import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio

from models.snapshot import ActionableElement, BrowserSnapshot
from models.graph_state import FieldType, FillStrategy, ApplicationState
from models.plan import Action

logger = logging.getLogger(__name__)

@dataclass
class AIClassification:
    """AI-generated field classification"""
    fill_strategy: FillStrategy
    confidence: float
    reasoning: str
    mapped_to: Optional[str] = None
    requires_rag: bool = False
    estimated_time: float = 1.0
    max_length: Optional[int] = None
    question_extracted: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill_strategy": self.fill_strategy.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "mapped_to": self.mapped_to,
            "requires_rag": self.requires_rag,
            "estimated_time": self.estimated_time,
            "max_length": self.max_length,
            "question_extracted": self.question_extracted
        }

class AIFieldClassifier:
    """AI-powered field classifier with no hard-coded patterns"""
    
    def __init__(self, llm_services):
        self.llm = llm_services
        self.classification_cache = {}
        
    async def classify_field_with_ai(self, element: ActionableElement, 
                                   page_context: Dict[str, Any]) -> AIClassification:
        """Main AI classification method"""
        
        # Check cache first
        cache_key = self._generate_cache_key(element, page_context)
        if cache_key in self.classification_cache:
            logger.debug(f"Cache hit for field {element.selector}")
            return self.classification_cache[cache_key]
        
        # Prepare context for AI
        field_context = self._prepare_field_context(element, page_context)
        
        # Get AI classification
        classification = await self._ai_classify_field(field_context)
        
        # Cache result
        self.classification_cache[cache_key] = classification
        
        logger.info(f"AI classified field {element.selector}: {classification.fill_strategy.value} "
                   f"(confidence: {classification.confidence:.2f})")
        
        return classification
    
    def _prepare_field_context(self, element: ActionableElement, 
                              page_context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive context for AI analysis"""
        
        # Extract all available context signals
        context = {
            "element": {
                "tag": element.tag,
                "type": element.type,
                "selector": element.selector,
                "placeholder": element.placeholder,
                "text": element.text,
                "required": element.required,
                "attributes": element.attributes
            },
            "page": {
                "title": page_context.get("title", ""),
                "url": page_context.get("url", ""),
                "form_count": page_context.get("form_count", 0)
            },
            "nearby_context": page_context.get("nearby_text", {}).get(element.selector, []),
            "user_profile_available": bool(page_context.get("user_data")),
            "rag_available": page_context.get("rag_available", False)
        }
        
        return context
    
    async def _ai_classify_field(self, field_context: Dict[str, Any]) -> AIClassification:
        """Use AI to classify the field"""
        
        prompt = self._build_classification_prompt(field_context)
        
        try:
            response = await self.llm.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            
            # Convert to our classification object
            return AIClassification(
                fill_strategy=FillStrategy(ai_result["fill_strategy"]),
                confidence=ai_result["confidence"],
                reasoning=ai_result["reasoning"],
                mapped_to=ai_result.get("mapped_to"),
                requires_rag=ai_result.get("requires_rag", False),
                estimated_time=ai_result.get("estimated_time", 1.0),
                max_length=ai_result.get("max_length"),
                question_extracted=ai_result.get("question_extracted")
            )
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            # Fallback to conservative classification
            return AIClassification(
                fill_strategy=FillStrategy.SIMPLE_MAPPING,
                confidence=0.3,
                reasoning=f"AI classification failed: {e}. Using fallback.",
                estimated_time=2.0
            )
    
    def _build_classification_prompt(self, field_context: Dict[str, Any]) -> str:
        """Build the AI classification prompt"""
        
        element = field_context["element"]
        page = field_context["page"]
        nearby = field_context["nearby_context"]
        
        prompt = f"""You are an expert at analyzing web form fields for job application automation.

FIELD TO ANALYZE:
- Tag: {element['tag']}
- Type: {element['type']}
- Selector: {element['selector']}
- Placeholder: \"{element['placeholder']}\"
- Text: \"{element['text']}\"
- Required: {element['required']}
- Attributes: {json.dumps(element['attributes'], indent=2)}

PAGE CONTEXT:
- Title: \"{page['title']}\"
- URL: {page['url']}
- Nearby text: {nearby}

TASK: Determine the best strategy to fill this field for a job application.

AVAILABLE STRATEGIES:
1. \"simple_mapping\" - Direct mapping from user data (name, email, phone, etc.)
2. \"rag_generation\" - Generate content using AI/RAG (essays, cover letters, etc.)
3. \"option_selection\" - Choose from dropdown/radio options
4. \"skip_field\" - Skip this field (assessments, out of scope, etc.)

ANALYSIS FRAMEWORK:
1. What information is this field requesting?
2. Is this a standard personal/professional field or custom content?
3. Can this be filled with simple user data or does it need generated content?
4. Should this field be skipped for any reason (assessment, legal, etc.)?

Respond with JSON in this exact format:
{{
    "fill_strategy": "simple_mapping|rag_generation|option_selection|skip_field",
    "confidence": 0.95,
    "reasoning": "Clear explanation of why you chose this strategy based on the field analysis",
    "mapped_to": "personal.first_name|experience.current_title|null",
    "requires_rag": true,
    "estimated_time": 2.5,
    "max_length": 500,
    "question_extracted": "What question is this field asking? (for RAG fields)"
}}

IMPORTANT GUIDELINES:
- Use "simple_mapping" for standard fields (name, email, phone, address, etc.)
- Use "rag_generation" for essays, cover letters, motivation questions, experience descriptions
- Use "option_selection" for dropdowns, radio buttons, selects
- Use "skip_field" for technical assessments, coding challenges, personality tests
- Be specific about the "mapped_to" field for simple mappings
- Extract the question for RAG fields to help with content generation
- Confidence should reflect how certain you are about the classification"""

        return prompt
    
    def _generate_cache_key(self, element: ActionableElement, 
                           page_context: Dict[str, Any]) -> str:
        """Generate cache key for element and context"""
        
        # Create a stable hash of the element and relevant context
        cache_data = {
            "selector": element.selector,
            "type": element.type,
            "placeholder": element.placeholder,
            "text": element.text,
            "page_title": page_context.get("title", ""),
            "nearby_text": page_context.get("nearby_text", {}).get(element.selector, [])
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def classify_multiple_fields(self, elements: List[ActionableElement], 
                                     page_context: Dict[str, Any]) -> List[AIClassification]:
        """Batch classify multiple fields for efficiency"""
        
        # For now, process individually (could be optimized with batch prompts)
        classifications = []
        
        for element in elements:
            classification = await self.classify_field_with_ai(element, page_context)
            classifications.append(classification)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return classifications
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get classification cache statistics"""
        return {
            "total_cached": len(self.classification_cache),
            "cache_size_bytes": len(str(self.classification_cache))
        }
