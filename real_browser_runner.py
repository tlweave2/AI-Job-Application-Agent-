#!/usr/bin/env python3
"""
Timothy's AI Job Application Agent - REAL BROWSER VERSION
Shows actual browser window and performs real form filling

SETUP:
    pip install playwright
    playwright install chromium

USAGE:
    python real_browser_runner.py "https://careers.veeva.com/job/..." --show-browser
    python real_browser_runner.py "url" --live --show-browser  # Actually fill forms
"""

import asyncio
import time
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

# Check for Playwright
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install chromium")

# Timothy's Profile (same as before)
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

# Real Browser Interface
class RealBrowserInterface:
    """Real browser automation using Playwright"""
    
    def __init__(self, timothy_profile, headless: bool = False, slow_mo: int = 500):
        self.browser = None
        self.page = None
        self.playwright = None
        self.headless = headless
        self.slow_mo = slow_mo
        self.timothy = timothy_profile
        
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
                    # Look for nearby text elements
                    parent = await element.evaluate('el => el.parentElement')
                    if parent:
                        parent_text = await element.evaluate('el => el.parentElement.textContent')
                        if parent_text and len(parent_text.strip()) < 100:
                            label_text = parent_text.strip()
            except:
                pass
            
            # Generate selector
            selector = f"#{id_attr}" if id_attr else f"[name='{name}']" if name else f"{tag_name}[type='{input_type}']"
            
            # Determine section based on field characteristics
            section = self._determine_section(label_text, placeholder, name, id_attr)
            
            return {
                'selector': selector,
                'label': label_text or placeholder or name or f"{tag_name}_{input_type}",
                'type': f"{tag_name}[{input_type}]" if input_type else tag_name,
                'section': section,
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
    
    def _determine_section(self, label, placeholder, name, id_attr):
        """Determine which section this field belongs to"""
        
        text_to_check = f"{label} {placeholder} {name} {id_attr}".lower()
        
        if any(keyword in text_to_check for keyword in ['first', 'last', 'name', 'email', 'phone', 'contact']):
            return 'personal'
        elif any(keyword in text_to_check for keyword in ['university', 'college', 'school', 'degree', 'gpa', 'graduation', 'education']):
            return 'education'
        elif any(keyword in text_to_check for keyword in ['cover', 'letter', 'why', 'motivation', 'interest', 'essay']):
            return 'essays'
        elif any(keyword in text_to_check for keyword in ['skill', 'language', 'programming', 'technical', 'framework']):
            return 'technical'
        elif any(keyword in text_to_check for keyword in ['experience', 'work', 'job', 'internship']):
            return 'experience'
        elif any(keyword in text_to_check for keyword in ['authorization', 'visa', 'citizen', 'legal']):
            return 'legal'
        elif any(keyword in text_to_check for keyword in ['resume', 'cv', 'upload', 'file', 'document']):
            return 'documents'
        else:
            return 'other'
    
    async def fill_field(self, field_info, value):
        """Fill a specific field with a value"""
        
        try:
            element = field_info['element_handle']
            field_type = field_info['type']
            input_type = await element.get_attribute('type') or ''
            label = field_info.get('label', '').lower()
            name_attr = field_info.get('name', '').lower()
            id_attr = field_info.get('id', '').lower()

            print(f"✏️  Filling {field_info['selector']}: {value[:50]}{'...' if len(value) > 50 else ''}")

            await element.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)

            # File input
            if 'file' in input_type or 'file' in field_type:
                resume_path = "resume5.pdf"
                try:
                    await element.set_input_files(resume_path)
                    print(f"📎 Uploaded file: {resume_path}")
                    return True
                except Exception as e:
                    print(f"❌ Failed to upload file: {e}")
                    return False

            # Checkbox (skills, languages, consent, etc.)
            elif input_type == "checkbox":
                try:
                    # Match skills/languages/frameworks
                    skills = [s.lower() for s in self.timothy.experience["languages"] + self.timothy.experience["frameworks"]]
                    if any(skill in label for skill in skills):
                        await element.check()
                        print(f"✅ Checked skill: {label}")
                    # Consent/marketing or EEO: default to checked for demo
                    elif "consent" in name_attr or "marketing" in name_attr or "privacy" in label:
                        await element.check()
                        print(f"✅ Checked consent/marketing: {label}")
                    else:
                        await element.uncheck()
                except Exception as e:
                    print(f"❌ Failed to set checkbox: {e}")
                    return False

            # Radio button (Yes/No, etc.)
            elif input_type == "radio":
                try:
                    if "yes" in label:
                        await element.check()
                        print(f"✅ Selected radio: Yes")
                    # Default: only select Yes for demo
                    return True
                except Exception as e:
                    print(f"❌ Failed to set radio: {e}")
                    return False

            # Select/Dropdown
            elif 'select' in field_type:
                try:
                    await element.select_option(value=value)
                    return True
                except Exception:
                    try:
                        await element.select_option(label=value)
                        return True
                    except Exception as e:
                        print(f"❌ Failed to select option: {e}")
                        return False

            # Text input/textarea (names, email, phone, etc.)
            elif 'input' in field_type or 'textarea' in field_type:
                try:
                    # Name fields
                    if any(x in label or x in name_attr or x in id_attr for x in ["first name", "firstname", "fname", "given"]):
                        value = self.timothy.personal["first_name"]
                    elif any(x in label or x in name_attr or x in id_attr for x in ["last name", "lastname", "lname", "surname", "family"]):
                        value = self.timothy.personal["last_name"]
                    elif "email" in label or "email" in name_attr or "email" in id_attr:
                        value = self.timothy.personal["email"]
                    elif "phone" in label or "phone" in name_attr or "phone" in id_attr:
                        value = self.timothy.personal["phone"]
                    # Fill the field
                    await element.fill("")
                    await element.type(value, delay=50)
                    return True
                except Exception as e:
                    print(f"❌ Failed to fill text field: {e}")
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

# AI Classifier (same as before but optimized for real elements)
class RealFormAIClassifier:
    """AI classifier optimized for real form elements"""
    
    def __init__(self, timothy_profile):
        self.timothy = timothy_profile
    
    async def classify_field(self, field_info):
        """Classify real form field"""
        
        # Simulate AI processing
        await asyncio.sleep(0.2)
        
        selector = field_info['selector'].lower()
        label = field_info['label'].lower()
        name = field_info.get('name', '').lower()
        placeholder = field_info.get('placeholder', '').lower()
        field_type = field_info['type'].lower()
        
        # Combine all text for analysis
        field_text = f"{selector} {label} {name} {placeholder}".lower()
        
        # Classification logic
        if any(keyword in field_text for keyword in ['first', 'fname', 'given']):
            return {
                "strategy": "simple_mapping",
                "confidence": 0.99,
                "value": self.timothy.personal["first_name"],
                "reasoning": "First name field detected"
            }
        
        elif any(keyword in field_text for keyword in ['last', 'surname', 'family', 'lname']):
            return {
                "strategy": "simple_mapping", 
                "confidence": 0.99,
                "value": self.timothy.personal["last_name"],
                "reasoning": "Last name field detected"
            }
        
        elif 'email' in field_text or 'input[email]' in field_type:
            return {
                "strategy": "simple_mapping",
                "confidence": 0.98,
                "value": self.timothy.personal["email"],
                "reasoning": "Email field detected"
            }
        
        elif any(keyword in field_text for keyword in ['phone', 'tel', 'mobile']):
            return {
                "strategy": "simple_mapping",
                "confidence": 0.96,
                "value": self.timothy.personal["phone"],
                "reasoning": "Phone field detected"
            }
        
        elif any(keyword in field_text for keyword in ['university', 'college', 'school']):
            return {
                "strategy": "simple_mapping",
                "confidence": 0.95,
                "value": self.timothy.education["school"],
                "reasoning": "University field detected"
            }
        
        elif 'gpa' in field_text:
            return {
                "strategy": "simple_mapping",
                "confidence": 0.94,
                "value": self.timothy.education["gpa"],
                "reasoning": "GPA field detected"
            }
        
        elif any(keyword in field_text for keyword in ['programming', 'languages', 'skills']):
            return {
                "strategy": "simple_mapping",
                "confidence": 0.91,
                "value": ", ".join(self.timothy.experience["languages"]),
                "reasoning": "Programming languages field"
            }
        
        elif 'textarea' in field_type and any(keyword in field_text for keyword in ['cover', 'why', 'interest', 'motivation']):
            if 'veeva' in field_text or 'company' in field_text:
                essay_content = """I'm particularly drawn to Veeva Systems because of your leadership in transforming the life sciences industry through innovative cloud software solutions. Your mission of helping life sciences companies bring therapies to patients faster resonates deeply with my desire to apply technology for meaningful impact."""
            else:
                essay_content = """I am excited about this opportunity because it aligns perfectly with my passion for software development and my goal to apply my technical skills in a collaborative, innovative environment. Through my VidlyAI project, I've demonstrated my ability to architect and build complete applications from concept to production."""
            
            return {
                "strategy": "rag_generation",
                "confidence": 0.94,
                "value": essay_content,
                "reasoning": "Essay field requiring personalized content"
            }
        
        elif 'select' in field_type and any(keyword in field_text for keyword in ['authorization', 'work', 'visa']):
            return {
                "strategy": "option_selection",
                "confidence": 0.92,
                "value": "US Citizen",
                "reasoning": "Work authorization selection"
            }
        
        elif 'file' in field_type:
            return {
                "strategy": "file_upload",
                "confidence": 0.87,
                "value": "Resume file ready",
                "reasoning": "File upload field"
            }
        
        else:
            return {
                "strategy": "simple_mapping",
                "confidence": 0.70,
                "value": "",
                "reasoning": "General field classification"
            }

# Main Real Browser Agent
class RealBrowserJobAgent:
    """Job application agent with real browser integration"""
    
    def __init__(self, show_browser: bool = True, slow_mo: int = 500):
        self.timothy = TimothyProfile()
        self.browser = RealBrowserInterface(timothy_profile=self.timothy, headless=False, slow_mo=slow_mo)
        self.classifier = RealFormAIClassifier(self.timothy)
        self.show_browser = show_browser
    
    async def apply_to_job(self, url: str, live_mode: bool = False, auto_submit: bool = False):
        """Apply to job with real browser"""
        
        print("🚀 Timothy's AI Job Application Agent - REAL BROWSER MODE")
        print("=" * 65)
        print(f"🎯 Target URL: {url}")
        print(f"🌐 Show Browser: {self.show_browser}")
        print(f"🤖 Live Mode: {live_mode}")
        print(f"📤 Auto Submit: {auto_submit}")
        print("=" * 65)
        
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
            
            # Step 4: Classify each field with AI
            print(f"\n🧠 AI Field Classification")
            print("─" * 60)
            
            classified_fields = []
            
            for i, field_info in enumerate(form_elements, 1):
                print(f"\n{i:2d}. {field_info['selector']:<25} [{field_info['section']}]")
                print(f"    Label: {field_info['label']}")
                print(f"    Type: {field_info['type']}")
                print(f"    Required: {field_info['required']}")
                
                # AI classify
                classification = await self.classifier.classify_field(field_info)
                
                print(f"    🤖 AI Analysis:")
                print(f"       Strategy: {classification['strategy']}")
                print(f"       Confidence: {classification['confidence']:.2f}")
                if classification.get('value'):
                    display_value = classification['value'][:40] + ("..." if len(classification['value']) > 40 else "")
                    print(f"       Value: \"{display_value}\"")
                print(f"       Reasoning: {classification['reasoning']}")
                
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
                await self.browser.take_screenshot("analysis_complete.png")
                
                # Keep browser open for 10 seconds to view
                print(f"🔍 Browser will stay open for 10 seconds for inspection...")
                await asyncio.sleep(10)
                
                return True
                
        except Exception as e:
            print(f"❌ Application failed: {e}")
            await self.browser.take_screenshot("error_state.png")
            return False
            
        finally:
            await self.browser.close()
    
    async def _show_execution_plan(self, classified_fields):
        """Show execution plan"""
        
        print(f"\n📊 Real Browser Analysis Results")
        print("=" * 50)
        
        fillable = [f for f in classified_fields if f['classification']['confidence'] > 0.8 and f['classification'].get('value')]
        
        print(f"📈 Analysis Summary:")
        print(f"   Total Fields Found: {len(classified_fields)}")
        print(f"   Auto-Fillable: {len(fillable)}")
        print(f"   Automation Rate: {len(fillable)/len(classified_fields)*100:.1f}%")
        
        # Show what will be filled
        print(f"\n📝 Fields Ready for Filling:")
        for field_data in fillable[:5]:  # Show first 5
            field_info = field_data['field_info']
            classification = field_data['classification']
            value = classification.get('value', '')
            
            display_value = value[:35] + "..." if len(value) > 35 else value
            print(f"   ✅ {field_info['label']:<25}: {display_value}")
    
    async def _execute_real_form_filling(self, classified_fields, auto_submit):
        """Execute real form filling"""
        
        print(f"\n🤖 Executing Real Form Filling")
        print("─" * 40)
        print(f"🎬 Watch the browser window to see live form filling!")
        
        filled_count = 0
        
        for field_data in classified_fields:
            field_info = field_data['field_info']
            classification = field_data['classification']
            
            if classification['confidence'] > 0.8 and classification.get('value'):
                success = await self.browser.fill_field(field_info, classification['value'])
                if success:
                    filled_count += 1
                
                # Small delay between fields
                await asyncio.sleep(0.5)
        
        print(f"\n✅ Form filling completed: {filled_count} fields filled")
        
        # Take screenshot of filled form
        await self.browser.take_screenshot("form_filled.png")
        
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
            print(f"⏸️  Form filled - manual review and submission recommended")
            print(f"🔍 Browser will stay open for 30 seconds for review...")
            await asyncio.sleep(30)
        
        return True

# CLI Interface
async def main():
    """CLI interface for real browser mode"""
    
    parser = argparse.ArgumentParser(description="Timothy's AI Job Agent - Real Browser Mode")
    parser.add_argument("url", nargs='?', help="Job application URL")
    parser.add_argument("--live", action="store_true", help="Actually fill the form")
    parser.add_argument("--auto-submit", action="store_true", help="Auto-submit after filling")
    parser.add_argument("--show-browser", action="store_true", default=True, help="Show browser window")
    parser.add_argument("--fast", action="store_true", help="Fast mode (no delays)")
    
    args = parser.parse_args()
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available!")
        print("📦 Install with:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return 1
    
    if not args.url:
        # Interactive mode
        print("🎬 Real Browser Job Application Agent")
        print("=" * 40)
        
        test_urls = [
            "https://jobs.lever.co/veeva/ef05bae6-d743-4a19-ac00-3ad9881cac2e/apply?lever-source=Linkedin",
            "https://jobs.lever.co/example",  # Generic Lever form
            "https://boards.greenhouse.io/example"  # Generic Greenhouse form
        ]
        
        print("🎯 Select URL to test with real browser:")
        for i, url in enumerate(test_urls, 1):
            print(f"   {i}. {url[:70]}...")
        
        choice = input(f"\nEnter choice (1-{len(test_urls)}) or paste URL: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(test_urls):
            args.url = test_urls[int(choice) - 1]
        elif choice.startswith(("http://", "https://")):
            args.url = choice
        else:
            args.url = test_urls[0]
    
    # Initialize agent
    slow_mo = 100 if args.fast else 500
    agent = RealBrowserJobAgent(show_browser=args.show_browser, slow_mo=slow_mo)
    
    # Run with real browser
    success = await agent.apply_to_job(
        url=args.url,
        live_mode=args.live,
        auto_submit=args.auto_submit
    )
    
    if success:
        print(f"\n🎉 Real browser job application completed!")
    else:
        print(f"\n❌ Application failed")
        return 1

if __name__ == "__main__":
    asyncio.run(main())
