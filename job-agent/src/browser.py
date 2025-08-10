
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page, ElementHandle
import yaml

logger = logging.getLogger(__name__)

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
class BrowserSnapshot:
    """Structured representation of the page state"""
    url: str
    title: str
    actionable_elements: List[ActionableElement]
    form_count: int
    submit_buttons: List[ActionableElement]
    timestamp: float

@dataclass
class Action:
    """Represents an action to be executed"""
    type: str  # 'click', 'type', 'select', 'upload', 'wait'
    selector: str
    value: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class BrowserRunner:
    def __init__(self, config_path: str = None):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.config = self._load_config(config_path)
        self.playwright = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load browser configuration"""
        default_config = {
            'browser': {
                'headful': True,
                'user_data_dir': './data/browser_profile',
                'viewport': {'width': 1280, 'height': 720}
            },
            'timeouts': {
                'default': 10000,
                'navigation': 30000,
                'action': 5000
            },
            'thresholds': {
                'short_field_accuracy': 0.99,
                'long_answer_confidence': 0.90
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge configs
                default_config.update(user_config)
        
        return default_config
    
    async def start(self):
        """Initialize browser and create persistent context"""
        self.playwright = await async_playwright().start()
        
        browser_config = self.config['browser']
        user_data_dir = Path(browser_config['user_data_dir'])
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Launch browser with persistent context
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=not browser_config.get('headful', True),
            viewport=browser_config.get('viewport', {'width': 1280, 'height': 720}),
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
            # Disable automation detection
            use_mobile=False,
        )
        
        # Create or get page
        if len(self.browser.pages) > 0:
            self.page = self.browser.pages[0]
        else:
            self.page = await self.browser.new_page()
            
        # Set default timeout
        self.page.set_default_timeout(self.config['timeouts']['default'])
        
        logger.info("Browser started successfully")
    
    async def goto(self, url: str) -> None:
        """Navigate to URL"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
            
        try:
            await self.page.goto(url, timeout=self.config['timeouts']['navigation'])
            await self.wait_for_stability()
            logger.info(f"Navigated to: {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
    
    async def snapshot(self) -> BrowserSnapshot:
        """Return actionable elements only"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            # Wait for page to be ready
            await self.page.wait_for_load_state('networkidle', timeout=5000)
        except:
            # Continue if timeout - page might still be usable
            pass
        
        # Get basic page info
        url = self.page.url
        title = await self.page.title()
        
        # Find all actionable elements
        actionable_elements = []
        
        # Input elements
        inputs = await self.page.query_selector_all('input:not([type="hidden"])')
        for input_el in inputs:
            element = await self._extract_element_info(input_el, 'input')
            if element and element.visible:
                actionable_elements.append(element)
        
        # Textareas
        textareas = await self.page.query_selector_all('textarea')
        for textarea_el in textareas:
            element = await self._extract_element_info(textarea_el, 'textarea')
            if element and element.visible:
                actionable_elements.append(element)
        
        # Select elements
        selects = await self.page.query_selector_all('select')
        for select_el in selects:
            element = await self._extract_element_info(select_el, 'select')
            if element and element.visible:
                actionable_elements.append(element)
        
        # Buttons and clickable elements
        buttons = await self.page.query_selector_all('button, input[type="submit"], input[type="button"], [role="button"]')
        clickable_elements = []
        for button_el in buttons:
            element = await self._extract_element_info(button_el, 'button')
            if element and element.visible:
                clickable_elements.append(element)
                actionable_elements.append(element)
        
        # Count forms
        forms = await self.page.query_selector_all('form')
        form_count = len(forms)
        
        # Identify submit buttons
        submit_buttons = [el for el in clickable_elements 
                         if 'submit' in el.text.lower() or 
                         el.type == 'submit' or
                         'apply' in el.text.lower()]
        
        snapshot = BrowserSnapshot(
            url=url,
            title=title,
            actionable_elements=actionable_elements,
            form_count=form_count,
            submit_buttons=submit_buttons,
            timestamp=asyncio.get_event_loop().time()
        )
        
        logger.info(f"Snapshot taken: {len(actionable_elements)} actionable elements found")
        return snapshot
    
    async def _extract_element_info(self, element: ElementHandle, tag: str) -> Optional[ActionableElement]:
        """Extract information from an element"""
        try:
            # Check if element is visible and enabled
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            if not is_visible:
                return None
            
            # Get element attributes
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            element_type = await element.get_attribute('type') or ''
            text = (await element.text_content() or '').strip()
            placeholder = await element.get_attribute('placeholder') or ''
            value = await element.input_value() if tag_name in ['input', 'textarea'] else (await element.get_attribute('value') or '')
            required = await element.get_attribute('required') is not None
            
            # Get bounding box
            box = await element.bounding_box()
            bounds = box if box else {'x': 0, 'y': 0, 'width': 0, 'height': 0}
            
            # Generate selector
            selector = await self._generate_selector(element)
            
            # Get all attributes for debugging
            attributes = await element.evaluate('''
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            ''')
            
            return ActionableElement(
                tag=tag_name,
                type=element_type,
                selector=selector,
                text=text,
                placeholder=placeholder,
                value=value,
                required=required,
                visible=is_visible,
                enabled=is_enabled,
                bounds=bounds,
                attributes=attributes
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract element info: {e}")
            return None
    
    async def _generate_selector(self, element: ElementHandle) -> str:
        """Generate a reliable selector for the element"""
        try:
            # Try different selector strategies in order of preference
            selectors_to_try = [
                # ID selector
                'el => el.id ? `#${el.id}` : null',
                # Name attribute
                'el => el.name ? `[name="${el.name}"]` : null',
                # Data attributes
                '''el => {
                    for (let attr of el.attributes) {
                        if (attr.name.startsWith('data-testid') || attr.name.startsWith('data-test')) {
                            return `[${attr.name}="${attr.value}"]`;
                        }
                    }
                    return null;
                }''',
                # Placeholder
                'el => el.placeholder ? `[placeholder="${el.placeholder}"]` : null',
                # Type + other attributes
                '''el => {
                    if (el.type) {
                        const tag = el.tagName.toLowerCase();
                        return `${tag}[type="${el.type}"]`;
                    }
                    return null;
                }''',
            ]
            
            for selector_js in selectors_to_try:
                selector = await element.evaluate(selector_js)
                if selector:
                    # Verify selector works and is unique
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if len(elements) == 1:
                            return selector
                    except:
                        continue
            
            # Fallback to xpath
            xpath = await element.evaluate('''
                el => {
                    const getElementXPath = (element) => {
                        if (element.id !== '') {
                            return `//*[@id="${element.id}"]`;
                        }
                        if (element === document.body) {
                            return '/html/body';
                        }
                        let ix = 0;
                        const siblings = element.parentNode ? element.parentNode.childNodes : [];
                        for (let i = 0; i < siblings.length; i++) {
                            const sibling = siblings[i];
                            if (sibling === element) {
                                return getElementXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                            }
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                                ix++;
                            }
                        }
                        return '';
                    };
                    return getElementXPath(el);
                }
            ''')
            return f"xpath={xpath}"
            
        except Exception as e:
            logger.warning(f"Failed to generate selector: {e}")
            return "unknown"
    
    async def execute_action(self, action: Action) -> bool:
        """Execute an action and return success status"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            selector = action.selector
            timeout = self.config['timeouts']['action']
            
            if action.type == 'click':
                await self.page.click(selector, timeout=timeout)
                logger.info(f"Clicked: {selector}")
                
            elif action.type == 'type':
                # Clear field first, then type
                await self.page.fill(selector, '', timeout=timeout)
                await self.page.type(selector, action.value or '', timeout=timeout)
                logger.info(f"Typed in {selector}: {action.value}")
                
            elif action.type == 'select':
                await self.page.select_option(selector, action.value, timeout=timeout)
                logger.info(f"Selected in {selector}: {action.value}")
                
            elif action.type == 'upload':
                await self.page.set_input_files(selector, action.value, timeout=timeout)
                logger.info(f"Uploaded to {selector}: {action.value}")
                
            elif action.type == 'wait':
                wait_time = float(action.value) if action.value else 1.0
                await asyncio.sleep(wait_time)
                logger.info(f"Waited: {wait_time} seconds")
                
            else:
                logger.error(f"Unknown action type: {action.type}")
                return False
            
            # Wait for any immediate effects
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute action {action.type} on {action.selector}: {e}")
            return False
    
    async def verify_field(self, selector: str, expected: str) -> Tuple[bool, str]:
        """Verify field content and return (success, actual_value)"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            element = await self.page.query_selector(selector)
            if not element:
                return False, "Element not found"
            
            # Get actual value based on element type
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            
            if tag_name in ['input', 'textarea']:
                actual_value = await element.input_value()
            else:
                actual_value = await element.text_content() or ''
            
            actual_value = actual_value.strip()
            expected = expected.strip()
            
            success = actual_value == expected
            if not success:
                logger.warning(f"Verification failed for {selector}. Expected: '{expected}', Got: '{actual_value}'")
            
            return success, actual_value
            
        except Exception as e:
            logger.error(f"Failed to verify field {selector}: {e}")
            return False, str(e)
    
    async def wait_for_stability(self, timeout: float = 5.0) -> None:
        """Wait for page to be stable (network idle + DOM stable)"""
        if not self.page:
            return
        
        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state('networkidle', timeout=timeout * 1000)
        except:
            # Continue if timeout
            pass
        
        # Additional stability check - wait for DOM to stop changing
        try:
            await self.page.wait_for_function(
                '''() => {
                    return new Promise(resolve => {
                        let lastMutationTime = Date.now();
                        const observer = new MutationObserver(() => {
                            lastMutationTime = Date.now();
                        });
                        observer.observe(document.body, { childList: true, subtree: true });
                        
                        const checkStability = () => {
                            if (Date.now() - lastMutationTime > 1000) {
                                observer.disconnect();
                                resolve(true);
                            } else {
                                setTimeout(checkStability, 100);
                            }
                        };
                        checkStability();
                    });
                }''',
                timeout=timeout * 1000
            )
        except:
            # Continue if timeout - page might still be usable
            pass
    
    async def screenshot(self, path: str = None) -> str:
        """Take a screenshot and return the path"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        if not path:
            import time
            path = f"screenshot_{int(time.time())}.png"
        
        await self.page.screenshot(path=path, full_page=True)
        logger.info(f"Screenshot saved: {path}")
        return path
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
        if self.playwright:
            await self.playwright.stop()

# Utility function for testing
async def test_browser():
    """Simple test function"""
    browser = BrowserRunner()
    try:
        await browser.start()
        await browser.goto("https://httpbin.org/forms/post")
        snapshot = await browser.snapshot()
        
        print(f"Found {len(snapshot.actionable_elements)} actionable elements:")
        for i, element in enumerate(snapshot.actionable_elements[:5]):  # Show first 5
            print(f"  {i+1}. {element.tag}[{element.type}] - {element.selector} - '{element.text}' / '{element.placeholder}'")
        
        await browser.screenshot("test_screenshot.png")
        
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_browser())
