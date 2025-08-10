
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml

from browser import BrowserRunner, Action
from llm_api import LLMServices, AuthState
from rag import RAGPipeline
from models.config import AgentConfig
from models.plan import ExecutionResult
from utils.logging import setup_agent_logging

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    profile_path: str
    resume_path: str
    questionnaire_path: str
    openai_api_key: str
    auto_submit: bool = False
    max_cycles: int = 10
    max_retries: int = 2

@dataclass
class ExecutionResult:
    success: bool
    completed_fields: int
    failed_actions: int
    form_completion: float
    final_state: str
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None

class JobApplicationAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.browser = BrowserRunner(config.profile_path)
        self.llm = LLMServices(api_key=config.openai_api_key)
        self.rag = RAGPipeline(api_key=config.openai_api_key)
        self.user_data = self._load_user_data()
        self.logger = setup_agent_logging()
        
        # Initialize RAG index
        self._initialize_rag()
        
        # Tracking
        self.cycle_count = 0
        self.completed_actions = []
        self.failed_actions = []
        
    def _initialize_rag(self):
        """Initialize RAG pipeline with resume and questionnaire"""
        try:
            # Check if pre-built index exists
            index_path = f"{self.config.resume_path}.index.json"
            if Path(index_path).exists():
                self.logger.logger.info("Loading pre-built RAG index")
                self.rag.load_index(index_path)
            else:
                self.logger.logger.info("Building new RAG index")
                success = self.rag.build_index(
                    self.config.resume_path,
                    self.user_data,
                    save_path=index_path
                )
                if not success:
                    self.logger.logger.warning("RAG index build failed - long answers may be limited")
        except Exception as e:
            self.logger.logger.error(f"RAG initialization failed: {e}")
    
    def _load_user_data(self) -> Dict[str, Any]:
        """Load user questionnaire data"""
        try:
            with open(self.config.questionnaire_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load questionnaire: {e}")
            return {}
    
    async def run(self, url: str) -> ExecutionResult:
        """Main orchestrator loop"""
        logger.info(f"Starting job application agent for: {url}")
        
        try:
            # 1. Initialize browser and navigate
            await self.browser.start()
            await self.browser.goto(url)
            
            # 2. Check auth state
            auth_result = await self._check_auth_state()
            if auth_result.next_action != "proceed":
                return ExecutionResult(
                    success=False,
                    completed_fields=0,
                    failed_actions=0,
                    form_completion=0.0,
                    final_state=auth_result.state.value,
                    error_message=f"Auth check failed: {auth_result.reason}"
                )
            
            # 3. Main form-filling loop
            while self.cycle_count < self.config.max_cycles:
                self.cycle_count += 1
                logger.info(f"Starting cycle {self.cycle_count}")
                
                # Take snapshot
                snapshot = await self.browser.snapshot()
                
                # Plan actions
                context = {
                    "user_data": self.user_data, 
                    "cycle": self.cycle_count,
                    "rag_available": self.rag.index_built
                }
                plan = await self.llm.plan_actions(snapshot, context)
                
                if not plan.actions:
                    logger.info("No more actions planned - form may be complete")
                    break
                
                # Execute actions
                cycle_success = await self._execute_action_cycle(plan.actions)
                
                # Check if we should submit
                if self._should_submit(plan, snapshot):
                    submit_success = await self._handle_submit(snapshot)
                    if submit_success:
                        return ExecutionResult(
                            success=True,
                            completed_fields=len(self.completed_actions),
                            failed_actions=len(self.failed_actions),
                            form_completion=plan.estimated_completion,
                            final_state="submitted",
                            screenshot_path=await self.browser.screenshot("final_success.png")
                        )
                
                # If no progress made, break
                if not cycle_success and not plan.actions:
                    logger.warning("No progress made in cycle, stopping")
                    break
            
            # Final screenshot and results
            screenshot_path = await self.browser.screenshot("final_state.png")
            
            return ExecutionResult(
                success=True,  # Completed filling, even if not submitted
                completed_fields=len(self.completed_actions),
                failed_actions=len(self.failed_actions),
                form_completion=self._estimate_completion(),
                final_state="form_filled",
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            screenshot_path = None
            try:
                screenshot_path = await self.browser.screenshot("error_state.png")
            except:
                pass
                
            return ExecutionResult(
                success=False,
                completed_fields=len(self.completed_actions),
                failed_actions=len(self.failed_actions),
                form_completion=0.0,
                final_state="error",
                screenshot_path=screenshot_path,
                error_message=str(e)
            )
        
        finally:
            await self.browser.close()
    
    async def _check_auth_state(self):
        """Check if authentication is required"""
        logger.info("Checking authentication state...")
        
        snapshot = await self.browser.snapshot()
        auth_result = await self.llm.classify_auth(snapshot)
        
        logger.info(f"Auth state: {auth_result.state} - {auth_result.reason}")
        
        if auth_result.state == AuthState.LOGIN_REQUIRED:
            logger.warning("Login required - pausing for human intervention")
            await self.browser.screenshot("login_required.png")
        elif auth_result.state in [AuthState.CAPTCHA_PRESENT, AuthState.TWO_FA_REQUIRED]:
            logger.warning(f"Security challenge detected: {auth_result.state}")
            await self.browser.screenshot("security_challenge.png")
        
        return auth_result
    
    async def _execute_action_cycle(self, actions: List[Action]) -> bool:
        """Execute a batch of actions with retries and repair"""
        cycle_success = False
        
        for action in actions:
            success = await self._execute_single_action(action)
            if success:
                cycle_success = True
            
            # Brief pause between actions
            await asyncio.sleep(0.5)
        
        return cycle_success
    
    async def _execute_single_action(self, action: Action) -> bool:
        """Execute a single action with retry and repair logic"""
        
        # Check if this is a long-form field that needs RAG
        if action.type == ActionType.TYPE and self._should_use_rag(action):
            action = await self._enhance_action_with_rag(action)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(f"Executing: {action.type} on {action.selector} = '{action.value}' (attempt {attempt + 1})")
                
                # Execute the action
                success = await self.browser.execute_action(action)
                
                if success:
                    # Verify the action worked (for form inputs)
                    if action.type in ['type', 'select'] and action.value:
                        verified, actual_value = await self.browser.verify_field(action.selector, action.value)
                        if verified:
                            logger.info(f"✅ Action verified successfully")
                            self.completed_actions.append(action)
                            return True
                        else:
                            logger.warning(f"⚠️  Action executed but verification failed. Expected: '{action.value}', Got: '{actual_value}'")
                            # For non-critical verification failures, still count as success
                            if self._is_close_enough(action.value, actual_value):
                                self.completed_actions.append(action)
                                return True
                    else:
                        # Non-verifiable actions (clicks, etc.)
                        self.completed_actions.append(action)
                        return True
                
                # If we get here, the action failed
                if attempt < self.config.max_retries:
                    logger.warning(f"Action failed, attempting repair...")
                    
                    # Get fresh snapshot for repair
                    snapshot = await self.browser.snapshot()
                    repair = await self.llm.repair_action(action, "Action execution failed", snapshot)
                    
                    if repair.confidence > 0.5:
                        logger.info(f"Trying repair: {repair.reasoning}")
                        action = repair.suggested_action
                        await asyncio.sleep(1)  # Wait before retry
                        continue
                
            except Exception as e:
                logger.error(f"Action execution error: {e}")
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2)  # Wait before retry
                    continue
        
        # All attempts failed
        logger.error(f"❌ Action failed after all retries: {action}")
        self.failed_actions.append(action)
        return False
    
    def _is_close_enough(self, expected: str, actual: str) -> bool:
        """Check if actual value is close enough to expected (for verification tolerance)"""
        if not expected or not actual:
            return expected == actual
        
        # Remove whitespace and compare
        expected_clean = expected.strip()
        actual_clean = actual.strip()
        
        # Exact match
        if expected_clean == actual_clean:
            return True
        
        # Case insensitive match
        if expected_clean.lower() == actual_clean.lower():
            return True
        
        # Check if one contains the other (for truncated fields)
        if expected_clean in actual_clean or actual_clean in expected_clean:
            return True
        
        return False
    
    def _should_submit(self, plan, snapshot) -> bool:
        """Decide whether to submit the form"""
        if not self.config.auto_submit:
            return False
        
        # Check if plan includes submit
        if not plan.includes_submit:
            return False
        
        # Check completion thresholds
        estimated_completion = plan.estimated_completion
        if estimated_completion < 0.9:  # Need 90% completion
            logger.info(f"Not submitting - completion only {estimated_completion:.2%}")
            return False
        
        # Check accuracy thresholds
        total_actions = len(self.completed_actions) + len(self.failed_actions)
        if total_actions == 0:
            return False
            
        success_rate = len(self.completed_actions) / total_actions
        if success_rate < 0.95:  # Need 95% success rate
            logger.info(f"Not submitting - success rate only {success_rate:.2%}")
            return False
        
        logger.info(f"✅ Auto-submit thresholds met: {estimated_completion:.2%} completion, {success_rate:.2%} success rate")
        return True
    
    async def _handle_submit(self, snapshot) -> bool:
        """Handle form submission"""
        logger.info("🚀 Attempting form submission...")
        
        # Find submit button
        submit_buttons = snapshot.submit_buttons
        if not submit_buttons:
            logger.error("No submit buttons found")
            return False
        
        # Try to click submit button
        submit_button = submit_buttons[0]  # Use first submit button
        submit_action = Action(type='click', selector=submit_button.selector)
        
        success = await self.browser.execute_action(submit_action)
        if success:
            # Wait for submission to process
            await self.browser.wait_for_stability()
            await asyncio.sleep(2)
            
            # Check if we're on a success page
            new_snapshot = await self.browser.snapshot()
            if new_snapshot.url != snapshot.url:
                logger.info("✅ Form submitted successfully - redirected to new page")
                return True
            else:
                logger.warning("⚠️  Submit clicked but no redirect - may have failed")
                return False
        
        return False
    
    def _estimate_completion(self) -> float:
        """Estimate how complete the form is based on our actions"""
        if not self.completed_actions:
            return 0.0
        
        # Simple heuristic: assume each completed action represents some % of form
        # This is rough - in practice you'd want more sophisticated completion detection
        completed_fields = len(self.completed_actions)
        return min(1.0, completed_fields * 0.15)  # Assume ~7 fields for complete form

    def _should_use_rag(self, action: Action) -> bool:
        """Determine if action should use RAG for content generation"""
        if not self.rag.index_built:
            return False
        
        # Check if this looks like a long-form field
        selector_lower = action.selector.lower()
        
        # Common patterns for long-form fields
        long_form_indicators = [
            'cover', 'letter', 'motivation', 'why', 'tell', 'describe',
            'explain', 'message', 'comment', 'additional', 'about'
        ]
        
        return any(indicator in selector_lower for indicator in long_form_indicators)

    async def _enhance_action_with_rag(self, action: Action) -> Action:
        """Enhance action value using RAG if appropriate"""
        try:
            # Get field context from selector and surrounding elements
            field_context = self._extract_field_context(action.selector)
            
            # Generate RAG response
            if field_context:
                rag_answer = self.rag.draft_answer(
                    question=field_context,
                    context=self.user_data,
                    max_length=500  # Default max length
                )
                
                if rag_answer and len(rag_answer) > 10:
                    self.logger.log_action(
                        action_type="rag_generation",
                        selector=action.selector,
                        value=f"Generated {len(rag_answer)} characters",
                        success=True
                    )
                    
                    # Create enhanced action
                    enhanced_action = Action(
                        type=action.type,
                        selector=action.selector,
                        value=rag_answer,
                        options=action.options,
                        reasoning=f"RAG-enhanced: {action.reasoning}"
                    )
                    return enhanced_action
        
        except Exception as e:
            self.logger.logger.warning(f"RAG enhancement failed: {e}")
        
        return action  # Return original if RAG fails

    def _extract_field_context(self, selector: str) -> str:
        """Extract context/question from field selector or nearby elements"""
        # This is a simplified version - in practice you'd analyze
        # the page structure to find labels, placeholders, etc.
        
        selector_lower = selector.lower()
        
        # Map common selectors to questions
        context_mapping = {
            'cover': "Write a cover letter introduction",
            'motivation': "Why are you interested in this position?",
            'why': "Why do you want to work at this company?",
            'experience': "Describe your relevant experience",
            'skills': "What are your key technical skills?",
            'challenge': "Describe a challenge you overcame",
            'project': "Tell us about a significant project",
            'goal': "What are your career goals?",
            'strength': "What are your key strengths?"
        }
        
        for keyword, question in context_mapping.items():
            if keyword in selector_lower:
                return question
        
        return "Tell us about yourself and your background"

# CLI interface
async def main():
    """CLI entry point"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='AI Job Application Agent')
    parser.add_argument('--url', required=True, help='Job application URL')
    parser.add_argument('--profile', default='./configs/profile.yaml', help='Browser profile config')
    parser.add_argument('--resume', default='./configs/resume.pdf', help='Resume file')
    parser.add_argument('--questionnaire', default='./configs/questionnaire.yaml', help='Questionnaire file')
    parser.add_argument('--auto-submit', action='store_true', help='Enable auto-submit')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key required. Set --api-key or OPENAI_API_KEY environment variable.")
        return
    
    # Create config
    config = AgentConfig(
        profile_path=args.profile,
        resume_path=args.resume,
        questionnaire_path=args.questionnaire,
        openai_api_key=api_key,
        auto_submit=args.auto_submit
    )
    
    # Run agent
    agent = JobApplicationAgent(config)
    
    print(f"🤖 Starting job application agent...")
    print(f"   URL: {args.url}")
    print(f"   Auto-submit: {args.auto_submit}")
    
    start_time = time.time()
    result = await agent.run(args.url)
    duration = time.time() - start_time
    
    # Print results
    print(f"\n📊 Results:")
    print(f"   Success: {result.success}")
    print(f"   Duration: {duration:.1f}s")
    print(f"   Completed fields: {result.completed_fields}")
    print(f"   Failed actions: {result.failed_actions}")
    print(f"   Form completion: {result.form_completion:.1%}")
    print(f"   Final state: {result.final_state}")
    
    if result.screenshot_path:
        print(f"   Screenshot: {result.screenshot_path}")
    
    if result.error_message:
        print(f"   Error: {result.error_message}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
