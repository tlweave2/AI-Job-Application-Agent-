#!/usr/bin/env python3
"""
Timothy's AI-First Job Application Agent - COMPLETE WORKING VERSION
TRUE AI-FIRST: Uses DeepSeek LLM for all classification and response generation

SETUP:
    pip install playwright aiohttp
    playwright install chromium
    
USAGE:
    python fixed_ai_browser_agent.py --help
    python fixed_ai_browser_agent.py "https://careers.veeva.com/job/..." --live --show-browser
    python fixed_ai_browser_agent.py "url" --live --show-browser  # AI fills forms in real browser
"""

import asyncio
import time
import sys
import argparse
import json
import aiohttp
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

print("=== AI-First Real Browser Script Starting ===")

# Check for Playwright
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
    print("[DEBUG] Playwright is available")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install chromium")

# Timothy's Profile (Real Data)
class TimothyProfile:
    def __init__(self):
        self.personal = {
            "first_name": "Timothy",
            "last_name": "Weaver", 
            "email": "tlweave2@asu.edu",
            "phone": "209-261-5308",
            "location": "Escalon, California",
            "linkedin": "linkedin.com/in/timweaversoftware",
            "website": "www.timothylweaver.com"
        }
        
        self.education = {
            "school": "Arizona State University",
            "degree": "Bachelor of Science in Software Engineering",
            "masters": "Master of Computer Science (starting August 2025)",
            "gpa": "3.83",
            "graduation": "May 2025",
            "academic_standing": "Dean's List"
        }
        
        self.experience = {
            "years_programming": "4+ years",
            "languages": ["Java", "JavaScript", "Python", "C++", "SQL"],
            "frameworks": ["Spring Boot", "React", "Node.js"],
            "databases": ["PostgreSQL", "MySQL", "MongoDB"]
        }

# Real DeepSeek LLM Service
class DeepSeekLLMService:
    """Real LLM service using DeepSeek API"""
    
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
                "content": """You are an expert AI system for analyzing web form fields in job applications. 
You must respond with valid JSON only, no additional text or explanation.
Your task is to classify fields and determine the best filling strategy."""
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
                print(f"[DEBUG] Making DeepSeek API request (attempt {attempt + 1})")
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        print(f"[DEBUG] Raw DeepSeek response: {content[:200]}...")
                        
                        try:
                            classification_data = json.loads(content)
                            print(f"[DEBUG] DeepSeek classification successful")
                            return classification_data
                        except json.JSONDecodeError as e:
                            print(f"[DEBUG] Failed to parse DeepSeek JSON response: {e}")
                            cleaned_response = self._extract_json_from_response(content)
                            if cleaned_response:
                                return cleaned_response
                    else:
                        error_text = await response.text()
                        print(f"[DEBUG] DeepSeek API error {response.status}: {error_text}")
                        if response.status == 429:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        elif response.status >= 500:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        else:
                            break
                            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"[DEBUG] DeepSeek API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    break
        
        print("[DEBUG] All DeepSeek API attempts failed, using fallback classification")
        return self._get_fallback_classification(prompt)
    
    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """Extract JSON from potentially malformed response"""
        import re
        
        # Try to clean the content first
        content = content.strip()
        
        # Look for JSON-like structures
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
            r'\{.*?\}',  # Greedy JSON match
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, try to build from key patterns
        if 'strategy' in content.lower():
            try:
                # Extract strategy if mentioned
                strategy_match = re.search(r'strategy["\']?\s*:\s*["\']?(\w+)', content, re.IGNORECASE)
                confidence_match = re.search(r'confidence["\']?\s*:\s*([0-9.]+)', content, re.IGNORECASE)
                value_match = re.search(r'value["\']?\s*:\s*["\']([^"\']+)', content, re.IGNORECASE)
                
                result = {
                    "strategy": strategy_match.group(1) if strategy_match else "simple_mapping",
                    "confidence": float(confidence_match.group(1)) if confidence_match else 0.8,
                    "reasoning": "Extracted from malformed response"
                }
                
                if value_match:
                    result["value"] = value_match.group(1)
                
                return result
            except:
                pass
        
        return None
    
    def _get_fallback_classification(self, prompt: str) -> Dict[str, Any]:
        """Provide fallback classification when API fails"""
        prompt_lower = prompt.lower()
        
        # Check for specific field patterns
        if any(indicator in prompt_lower for indicator in ["name", "first name", "fname", "given name"]):
            return {
                "strategy": "simple_mapping",
                "confidence": 0.80,
                "value": "Timothy",
                "reasoning": "API failed, fallback detected name field"
            }
        elif any(indicator in prompt_lower for indicator in ["email", "e-mail"]):
            return {
                "strategy": "simple_mapping", 
                "confidence": 0.80,
                "value": "tlweave2@asu.edu",
                "reasoning": "API failed, fallback detected email field"
            }
        elif any(indicator in prompt_lower for indicator in ["phone", "mobile", "telephone"]):
            return {
                "strategy": "simple_mapping",
                "confidence": 0.80, 
                "value": "209-261-5308",
                "reasoning": "API failed, fallback detected phone field"
            }
        elif any(indicator in prompt_lower for indicator in ["gpa", "3.7", "grade"]):
            return {
                "strategy": "option_selection",
                "confidence": 0.80,
                "value": "3.83",
                "reasoning": "API failed, fallback detected GPA field"
            }
        elif any(indicator in prompt_lower for indicator in ["university", "school", "college"]):
            return {
                "strategy": "option_selection",
                "confidence": 0.80,
                "value": "Arizona State University",
                "reasoning": "API failed, fallback detected university field"
            }
        elif "type: input[radio]" in prompt_lower:
            return {
                "strategy": "option_selection",
                "confidence": 0.60,
                "reasoning": "API failed, fallback for radio button"
            }
        elif "type: input[checkbox]" in prompt_lower:
            return {
                "strategy": "option_selection", 
                "confidence": 0.60,
                "reasoning": "API failed, fallback for checkbox"
            }
        elif "required: true" in prompt_lower:
            return {
                "strategy": "simple_mapping",
                "confidence": 0.50,
                "reasoning": "API failed, required field fallback"
            }
        
        return {
            "strategy": "skip_field",
            "confidence": 0.40,
            "reasoning": "API failed, fallback to skip non-essential field"
        }

"""
AI-FIRST FIELD DECISION SYSTEM
Every decision is made by AI, not hard-coded rules
"""

class AIFieldDecisionEngine:
    """AI Field Decision Engine using DeepSeek LLM"""
    
    def __init__(self, llm_service: DeepSeekLLMService):
        self.llm = llm_service
    
    async def decide_field_action(self, field_info) -> Dict[str, Any]:
        """Decide action for a form field using AI"""
        
        prompt = self._build_decision_prompt(field_info)
        
        try:
            decision = await self.llm.classify_field(prompt)
            return decision
        except Exception as e:
            print(f"❌ AI decision failed: {e}")
            return {
                "fill_strategy": "skip_field",
                "reasoning": f"Decision failed: {e}",
                "confidence": 0.0
            }
    
    def _build_decision_prompt(self, field_info):
        """Build AI prompt for field decision"""
        
        return f"""Determine the best action for this job application form field.

FIELD DETAILS:
- Selector: {field_info['selector']}
- Label: "{field_info['label']}"
- Type: {field_info['type']}
- Required: {field_info['required']}
- Placeholder: "{field_info['placeholder']}"
- Current Value: "{field_info['value']}"

TIMOTHY'S PROFILE:
- Name: Timothy Weaver
- Email: tlweave2@asu.edu
- Phone: 209-261-5308
- Education: Bachelor of Software Engineering, ASU (GPA: 3.83)
- Experience: 4+ years programming (Java, JavaScript, Python)
- Current Project: VidlyAI.Com (Spring Boot, React, PostgreSQL)

RESPOND WITH VALID JSON ONLY:
{{
    "strategy": "simple_mapping|rag_generation|option_selection|skip_field",
    "confidence": 0.95,
    "value": "Timothy|tlweave2@asu.edu|Arizona State University|null",
    "reasoning": "Why you chose this strategy"
}}

For text inputs use "simple_mapping" and provide a "value".
For radio/checkboxes use "option_selection" and provide a "value" if should be selected.
For skip use "skip_field" with no value.
For unknown fields use "skip_field"."""

class AIEnhancedBrowserInterface:
    """Enhanced browser interface with AI decision making"""
    
    def __init__(self, timothy_profile, llm_service, headless: bool = False, slow_mo: int = 500):
        self.browser = None
        self.page = None
        self.playwright = None
        self.headless = headless
        self.slow_mo = slow_mo
        self.timothy = timothy_profile
        self.llm_service = llm_service
        self.decision_engine = AIFieldDecisionEngine(llm_service)
        
    async def start(self, show_browser: bool = True):
        """Start real browser"""
        
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available. Install with: pip install playwright && playwright install chromium")
        
        print("🌐 Starting real browser...")
        
        self.playwright = await async_playwright().start()
        
        # Launch browser with visible window
        self.browser = await self.playwright.chromium.launch(
            headless=not show_browser,  # Show browser window
            slow_mo=self.slow_mo,       # Slow down for visibility
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
            ]
        )
        
        # Create new page
        self.page = await self.browser.new_page()
        
        # Set viewport
        await self.page.set_viewport_size({"width": 1280, "height": 720})
        
        print("✅ Browser window opened")
        
    async def navigate_to_url(self, url: str):
        """Navigate to specific URL"""
        
        print(f"📍 Navigating to: {url}")
        
        try:
            # Navigate to the URL
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for page to fully load
            await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # Additional wait for dynamic content
            
            # Get page title
            title = await self.page.title()
            current_url = self.page.url
            
            print(f"✅ Page loaded: {title}")
            print(f"📄 Current URL: {current_url}")
            
            return title, current_url
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            raise
    
    async def analyze_page_forms(self):
        """Analyze page for form elements"""
        
        print("🔍 Analyzing page for form elements...")
        
        try:
            # Wait for any forms to load
            await self.page.wait_for_selector('form, input, textarea, select', timeout=10000)
            
            # Find all form elements
            form_elements = []
            
            # Get input elements
            inputs = await self.page.query_selector_all('input:not([type="hidden"])')
            for input_el in inputs:
                element_info = await self._extract_element_info(input_el, 'input')
                if element_info:
                    form_elements.append(element_info)
            
            # Get textarea elements
            textareas = await self.page.query_selector_all('textarea')
            for textarea_el in textareas:
                element_info = await self._extract_element_info(textarea_el, 'textarea')
                if element_info:
                    form_elements.append(element_info)
            
            # Get select elements
            selects = await self.page.query_selector_all('select')
            for select_el in selects:
                element_info = await self._extract_element_info(select_el, 'select')
                if element_info:
                    form_elements.append(element_info)
            
            print(f"📋 Found {len(form_elements)} form elements")
            
            return form_elements
            
        except Exception as e:
            print(f"⚠️  Form analysis failed: {e}")
            return []
    
    async def _extract_element_info(self, element, tag_name):
        """Extract information from a form element"""
        
        try:
            # Check if element is visible
            is_visible = await element.is_visible()
            if not is_visible:
                return None
            
            # Get element attributes
            input_type = await element.get_attribute('type') or ''
            name = await element.get_attribute('name') or ''
            id_attr = await element.get_attribute('id') or ''
            placeholder = await element.get_attribute('placeholder') or ''
            required = await element.get_attribute('required') is not None
            value = await element.input_value() if tag_name in ['input', 'textarea'] else ''
            
            # Try to get label text
            label_text = ''
            try:
                if id_attr:
                    label = await self.page.query_selector(f'label[for="{id_attr}"]')
                    if label:
                        label_text = await label.text_content()
                
                # If no label found, try to find nearby text
                if not label_text:
                    parent_text = await element.evaluate('el => el.parentElement?.textContent || ""')
                    if parent_text and len(parent_text.strip()) < 100:
                        label_text = parent_text.strip()
            except:
                pass
            
            # Generate selector
            selector = f"#{id_attr}" if id_attr else f"[name='{name}']" if name else f"{tag_name}[type='{input_type}']"
            
            return {
                'selector': selector,
                'label': label_text or placeholder or name or f"{tag_name}_{input_type}",
                'type': f"{tag_name}[{input_type}]" if input_type else tag_name,
                'required': required,
                'placeholder': placeholder,
                'value': value,
                'name': name,
                'id': id_attr,
                'element_handle': element  # Keep reference for filling
            }
            
        except Exception as e:
            print(f"⚠️  Error extracting element info: {e}")
            return None
    
    async def fill_field(self, field_info, value):
        """Fill a specific field with a value"""
        
        try:
            element = field_info['element_handle']
            field_type = field_info['type']
            
            print(f"✏️  Filling {field_info['selector']}: {value[:50]}{'...' if len(value) > 50 else ''}")
            
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            
            # Handle different field types
            if 'input[text]' in field_type or 'input[email]' in field_type or 'textarea' in field_type:
                await element.fill("")
                await element.type(value, delay=50)
                return True
            elif 'input[radio]' in field_type:
                # Handle radio buttons
                try:
                    await element.check()
                    return True
                except Exception as e:
                    print(f"❌ Failed to select radio button: {e}")
                    return False
            elif 'input[checkbox]' in field_type:
                # Handle checkboxes
                try:
                    await element.check()
                    return True
                except Exception as e:
                    print(f"❌ Failed to check checkbox: {e}")
                    return False
            elif 'select' in field_type:
                try:
                    await element.select_option(value=value)
                    return True
                except:
                    try:
                        await element.select_option(label=value)
                        return True
                    except Exception as e:
                        print(f"❌ Failed to select option: {e}")
                        return False
            else:
                print(f"⚠️  Unknown field type: {field_type}")
                return False
            
        except Exception as e:
            print(f"❌ Failed to fill {field_info['selector']}: {e}")
            return False
    
    async def take_screenshot(self, filename: str = None):
        """Take a screenshot of current page"""
        
        if not filename:
            filename = f"screenshot_{int(time.time())}.png"
        
        await self.page.screenshot(path=filename, full_page=True)
        print(f"📷 Screenshot saved: {filename}")
        return filename
    
    async def close(self):
        """Close the browser"""
        
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🛑 Browser closed")

# AI Classifier using DeepSeek
class AIFirstFieldClassifier:
    """AI-First field classifier using DeepSeek LLM"""
    
    def __init__(self, llm_service, timothy_profile):
        self.llm = llm_service
        self.timothy = timothy_profile
    
    async def classify_field(self, field_info):
        """Classify field using real AI"""
        
        prompt = self._build_ai_prompt(field_info)
        
        try:
            classification = await self.llm.classify_field(prompt)
            
            # Add Timothy's value if we have a mapping
            if classification.get('mapped_to'):
                value = self._get_timothy_value(classification['mapped_to'])
                classification['value'] = value
            
            return classification
            
        except Exception as e:
            print(f"❌ AI classification failed: {e}")
            return {
                "strategy": "simple_mapping",
                "confidence": 0.50,
                "value": "",
                "reasoning": f"Classification failed: {e}"
            }
    
    def _build_ai_prompt(self, field_info):
        """Build AI prompt for field classification"""
        
        return f"""Analyze this job application form field and determine the best filling strategy.

FIELD DETAILS:
- Selector: {field_info['selector']}
- Label: "{field_info['label']}"
- Type: {field_info['type']}
- Required: {field_info['required']}
- Placeholder: "{field_info['placeholder']}"

TIMOTHY'S PROFILE:
- Name: Timothy Weaver
- Email: tlweave2@asu.edu
- Phone: 209-261-5308
- Education: Bachelor of Software Engineering, ASU (GPA: 3.83)
- Experience: 4+ years programming (Java, JavaScript, Python)
- Current Project: VidlyAI.Com (Spring Boot, React, PostgreSQL)

RESPOND WITH VALID JSON:
{{
    "fill_strategy": "simple_mapping|rag_generation|option_selection|skip_field",
    "confidence": 0.95,
    "reasoning": "Why you chose this strategy",
    "mapped_to": "personal.first_name|education.school|null",
    "requires_rag": false,
    "priority": 80
}}"""
    
    def _get_timothy_value(self, mapped_field):
        """Get Timothy's value for a mapped field"""
        
        if mapped_field == "personal.first_name":
            return self.timothy.personal["first_name"]
        elif mapped_field == "personal.last_name":
            return self.timothy.personal["last_name"]
        elif mapped_field == "personal.email":
            return self.timothy.personal["email"]
        elif mapped_field == "personal.phone":
            return self.timothy.personal["phone"]
        elif mapped_field == "education.school":
            return self.timothy.education["school"]
        elif mapped_field == "education.degree":
            return self.timothy.education["degree"]
        elif mapped_field == "education.gpa":
            return self.timothy.education["gpa"]
        else:
            return ""

# Main AI-First Agent
class AIFirstRealBrowserAgent:
    """AI-First job application agent with real browser and real AI"""
    
    def __init__(self, show_browser: bool = True, slow_mo: int = 500, api_key: str = None):
        print("[DEBUG] Initializing AIFirstRealBrowserAgent")
        self.timothy = TimothyProfile()
        self.browser = AIEnhancedBrowserInterface(timothy_profile=self.timothy, llm_service=None, headless=False, slow_mo=slow_mo)
        
        # Initialize DeepSeek LLM
        self.api_key = api_key or "sk-317d3b46ff4b48589850a71ab85d00b4"
        self.llm = DeepSeekLLMService(self.api_key)
        self.classifier = AIFirstFieldClassifier(self.llm, self.timothy)
        
        self.show_browser = show_browser
        print("[DEBUG] AIFirstRealBrowserAgent initialized successfully")
    
    async def apply_to_job(self, url: str, live_mode: bool = False, auto_submit: bool = False):
        """Apply to job with real browser and real AI"""
        
        print("🚀 Timothy's AI-First Job Application Agent - REAL BROWSER + REAL AI")
        print("=" * 75)
        print(f"🎯 Target URL: {url}")
        print(f"🌐 Show Browser: {self.show_browser}")
        print(f"🤖 Live Mode: {live_mode}")
        print(f"📤 Auto Submit: {auto_submit}")
        print(f"🧠 AI Engine: DeepSeek ({self.api_key[:20]}...)")
        print("=" * 75)
        
        try:
            # Step 1: Start real browser
            await self.browser.start(show_browser=self.show_browser)
            
            # Step 2: Navigate to job posting
            title, current_url = await self.browser.navigate_to_url(url)
            
            # Step 3: Analyze form elements
            form_elements = await self.browser.analyze_page_forms()
            
            if not form_elements:
                print("❌ No form elements found on this page")
                await self.browser.take_screenshot("no_forms_found.png")
                return False
            
            # Step 4: AI classify each field
            print(f"\n🧠 AI Field Classification with DeepSeek")
            print("─" * 60)
            
            classified_fields = []
            
            for i, field_info in enumerate(form_elements, 1):
                print(f"\n{i:2d}. {field_info['selector']:<25}")
                print(f"    Label: {field_info['label']}")
                print(f"    Type: {field_info['type']}")
                print(f"    Required: {field_info['required']}")
                
                # Real AI classification
                print(f"    🧠 Requesting AI classification...")
                classification = await self.classifier.classify_field(field_info)
                
                print(f"    🤖 DeepSeek Analysis:")
                strategy = classification.get('strategy') or classification.get('fill_strategy', 'unknown')
                print(f"       Strategy: {strategy}")
                print(f"       Confidence: {classification.get('confidence', 0):.2f}")
                if classification.get('value'):
                    display_value = classification['value'][:40] + ("..." if len(classification['value']) > 40 else "")
                    print(f"       Value: \"{display_value}\"")
                print(f"       Reasoning: {classification.get('reasoning', 'No reasoning provided')}")
                
                # Normalize the strategy field for consistency
                classification['strategy'] = strategy
                classification['fill_strategy'] = strategy
                
                classified_fields.append({
                    'field_info': field_info,
                    'classification': classification
                })
            
            # Step 5: Show execution plan
            await self._show_execution_plan(classified_fields)
            
            # Step 6: Fill form if live mode
            if live_mode:
                success = await self._execute_real_form_filling(classified_fields, auto_submit)
                return success
            else:
                print(f"\n🧪 Analysis completed - run with --live to fill the actual form")
                await self.browser.take_screenshot("ai_analysis_complete.png")
                
                # Keep browser open for 10 seconds to view
                print(f"🔍 Browser will stay open for 10 seconds for inspection...")
                await asyncio.sleep(10)
                
                return True
                
        except Exception as e:
            print(f"❌ Application failed: {e}")
            await self.browser.take_screenshot("error_state.png")
            return False
            
        finally:
            if hasattr(self.llm, 'session') and self.llm.session:
                await self.llm.session.close()
            await self.browser.close()
    
    async def _show_execution_plan(self, classified_fields):
        """Show AI execution plan"""
        
        print(f"\n📊 AI Analysis Results")
        print("=" * 50)
        
        fillable = []
        for f in classified_fields:
            classification = f['classification']
            strategy = classification.get('strategy') or classification.get('fill_strategy', 'skip_field')
            confidence = classification.get('confidence', 0)
            
            # Field is fillable if it has good confidence and a strategy that requires filling
            if confidence > 0.6 and strategy in ['simple_mapping', 'option_selection'] and classification.get('value'):
                fillable.append(f)
        
        print(f"📈 AI Analysis Summary:")
        print(f"   Total Fields Found: {len(classified_fields)}")
        print(f"   AI Classified: {len([f for f in classified_fields if f['classification'].get('confidence', 0) > 0.5])}")
        print(f"   Auto-Fillable: {len(fillable)}")
        print(f"   Automation Rate: {len(fillable)/len(classified_fields)*100:.1f}%")
        
        # Show what AI will fill
        print(f"\n📝 Fields Ready for AI Filling:")
        for field_data in fillable[:5]:  # Show first 5
            field_info = field_data['field_info']
            classification = field_data['classification']
            value = classification.get('value', '')
            
            display_value = value[:35] + "..." if len(value) > 35 else value
            print(f"   ✅ {field_info['label']:<25}: {display_value}")
    
    async def _execute_real_form_filling(self, classified_fields, auto_submit):
        """Execute real AI-driven form filling"""
        
        print(f"\n🤖 Executing AI-Driven Form Filling")
        print("─" * 40)
        print(f"🎬 Watch the browser window to see live AI form filling!")
        
        filled_count = 0
        
        for field_data in classified_fields:
            field_info = field_data['field_info']
            classification = field_data['classification']
            
            strategy = classification.get('strategy') or classification.get('fill_strategy', 'skip_field')
            confidence = classification.get('confidence', 0)
            value = classification.get('value')
            
            # Fill field if it meets the criteria
            if confidence > 0.6 and strategy in ['simple_mapping', 'option_selection'] and value:
                success = await self.browser.fill_field(field_info, value)
                if success:
                    filled_count += 1
                
                # Small delay between fields
                await asyncio.sleep(0.8)
        
        print(f"\n✅ AI form filling completed: {filled_count} fields filled")
        
        # Take screenshot of filled form
        await self.browser.take_screenshot("ai_form_filled.png")
        
        if auto_submit:
            print(f"🚀 Looking for submit button...")
            try:
                submit_btn = await self.browser.page.query_selector('input[type="submit"], button[type="submit"], button:has-text("Submit"), button:has-text("Apply")')
                if submit_btn:
                    print(f"📤 Found submit button - clicking...")
                    await submit_btn.click()
                    await asyncio.sleep(3)
                    print(f"✅ Application submitted!")
                else:
                    print(f"⚠️  No submit button found - manual submission required")
            except Exception as e:
                print(f"⚠️  Submit failed: {e}")
        else:
            print(f"⏸️  Form filled by AI - manual review and submission recommended")
            print(f"🔍 Browser will stay open for 30 seconds for review...")
            await asyncio.sleep(30)
        
        return True

# CLI Interface
async def main():
    """CLI interface for AI-first real browser mode"""
    
    print("[DEBUG] Entered main() function.")
    
    parser = argparse.ArgumentParser(description="Timothy's AI-First Job Agent - Real Browser + Real AI")
    parser.add_argument("url", nargs='?', help="Job application URL")
    parser.add_argument("--live", action="store_true", help="Actually fill the form with AI")
    parser.add_argument("--auto-submit", action="store_true", help="Auto-submit after AI filling")
    parser.add_argument("--show-browser", action="store_true", default=True, help="Show browser window")
    parser.add_argument("--fast", action="store_true", help="Fast mode (no delays)")
    parser.add_argument("--api-key", help="DeepSeek API key")
    
    args = parser.parse_args()
    print(f"[DEBUG] Parsed args: {args}")
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available!")
        print("📦 Install with:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return 1
    
    if not args.url:
        # Interactive mode
        print("🎬 AI-First Real Browser Job Application Agent")
        print("=" * 50)
        
        test_urls = [
            "https://jobs.lever.co/veeva/ef05bae6-d743-4a19-ac00-3ad9881cac2e/apply?lever-source=Linkedin",
            "https://jobs.lever.co/example",  # Generic Lever form
            "https://boards.greenhouse.io/example"  # Generic Greenhouse form
        ]
        
        print("🎯 Select URL to test with AI + real browser:")
        for i, url in enumerate(test_urls, 1):
            print(f"   {i}. {url[:70]}...")
        
        choice = input(f"\nEnter choice (1-{len(test_urls)}) or paste URL: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(test_urls):
            args.url = test_urls[int(choice) - 1]
        elif choice.startswith(("http://", "https://")):
            args.url = choice
        else:
            args.url = test_urls[0]
    
    # Initialize AI-first agent
    slow_mo = 100 if args.fast else 500
    agent = AIFirstRealBrowserAgent(
        show_browser=args.show_browser, 
        slow_mo=slow_mo,
        api_key=args.api_key
    )
    
    # Run with real browser + real AI
    success = await agent.apply_to_job(
        url=args.url,
        live_mode=args.live,
        auto_submit=args.auto_submit
    )
    
    if success:
        print(f"\n🎉 AI-first job application completed!")
    else:
        print(f"\n❌ Application failed")
        return 1

if __name__ == "__main__":
    print("[DEBUG] **name** == '__main__', running asyncio.run(main())")
    asyncio.run(main())