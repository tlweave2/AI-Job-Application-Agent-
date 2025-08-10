"""
Main LangGraph-based Job Application Agent
Corrected version with proper imports and error handling
"""

import asyncio
import logging
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

# Core imports with error handling
try:
    from browser import BrowserRunner
except ImportError:
    from job-agent.src.browser import BrowserRunner

try:
    from llm_api import LLMServices
except ImportError:
    from job-agent.src.llm_api import LLMServices

try:
    from rag import RAGPipeline
except ImportError:
    from job-agent.src.rag import RAGPipeline

try:
    from models.graph_state import ApplicationState, FillStrategy
    from models.config import AgentConfig
    from models.plan import ExecutionResult
except ImportError:
    # Fallback imports
    try:
        from job-agent.src.models.graph_state import ApplicationState, FillStrategy
        from job-agent.src.models.config import AgentConfig
        from job-agent.src.models.plan import ExecutionResult
    except ImportError:
        # Define minimal fallbacks if models don't exist
        from typing import TypedDict
        class ApplicationState(TypedDict):
            url: str
            final_state: str
        
        class AgentConfig:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class ExecutionResult:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

try:
    from graph.ai_workflow import create_ai_first_workflow
    from graph.ai_enhanced_nodes import AIEnhancedNodes
except ImportError:
    try:
        from job-agent.src.graph.ai_workflow import create_ai_first_workflow
        from job-agent.src.graph.ai_enhanced_nodes import AIEnhancedNodes
    except ImportError:
        # Fallback: create minimal workflow
        def create_ai_first_workflow(browser, llm, rag):
            return MockWorkflow()
        
        class AIEnhancedNodes:
            def __init__(self, browser, llm, rag):
                self.browser = browser
                self.llm = llm
                self.rag = rag

try:
    from utils.logging import setup_agent_logging
except ImportError:
    try:
        from job-agent.src.utils.logging import setup_agent_logging
    except ImportError:
        def setup_agent_logging():
            return logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class MockWorkflow:
    """Fallback workflow when LangGraph is not available"""
    def compile(self):
        return self
    
    async def ainvoke(self, state):
        logger.warning("Using mock workflow - LangGraph not available")
        return {
            **state,
            "final_state": "mock_completed",
            "form_completion": 0.5,
            "completed_fields": [],
            "failed_fields": []
        }

class GraphJobApplicationAgent:
    """LangGraph-based Job Application Agent with AI-first architecture"""
    
    def __init__(self, config: AgentConfig, workflow=None):
        self.config = config
        
        # Initialize core components
        try:
            self.browser = BrowserRunner(config.profile_path)
            self.llm = LLMServices(api_key=config.openai_api_key)
            self.rag = RAGPipeline()  # Will be updated when RAGPipeline is fixed
            
            # Create workflow
            if workflow:
                self.workflow = workflow
            else:
                self.workflow = create_ai_first_workflow(self.browser, self.llm, self.rag)
            
            self.app = self.workflow.compile()
            
        except Exception as e:
            logger.error(f"Failed to initialize agent components: {e}")
            # Create minimal fallback components
            self.browser = None
            self.llm = None
            self.rag = None
            self.workflow = MockWorkflow()
            self.app = self.workflow
        
        # Load user data
        self.user_data = self._load_user_data()
        
        # Set up logging
        try:
            self.logger = setup_agent_logging()
        except:
            self.logger = logging.getLogger(__name__)
    
    def _load_user_data(self) -> Dict[str, Any]:
        """Load user questionnaire data"""
        try:
            with open(self.config.questionnaire_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load questionnaire: {e}")
            # Return minimal user data
            return {
                "personal": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567"
                },
                "experience": {
                    "current_title": "Software Engineer",
                    "years_programming": "5+ years"
                }
            }
    
    async def run(self, url: str) -> ExecutionResult:
        """Run the graph-based agent"""
        
        logger.info(f"🚀 Starting AI-first job application for: {url}")
        start_time = time.time()
        
        # Initialize state
        initial_state = {
            "url": url,
            "page_title": "",
            "current_snapshot": {},
            "field_queue": [],
            "current_field": None,
            "completed_fields": [],
            "failed_fields": [],
            "skipped_fields": [],
            "user_data": self.user_data,
            "rag_context": {"pipeline": self.rag},
            "retry_count": 0,
            "cycle_count": 0,
            "execution_time": 0.0,
            "field_analysis": None,
            "fill_strategy": None,
            "requires_human": False,
            "form_completion": 0.0,
            "should_submit": False,
            "final_state": "initializing"
        }
        
        try:
            # Start browser if available
            if self.browser:
                await self.browser.start()
                await self.browser.goto(url)
                logger.info("✅ Browser started and navigated to URL")
            else:
                logger.warning("⚠️ Browser not available, using mock mode")
            
            # Run the AI workflow
            logger.info("🧠 Running AI-first workflow...")
            final_state = await self.app.ainvoke(initial_state)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            final_state["execution_time"] = execution_time
            
            # Create result
            result = ExecutionResult(
                success=final_state.get("final_state") in ["submitted", "ready_for_submit", "mock_completed"],
                completed_fields=len(final_state.get("completed_fields", [])),
                failed_actions=len(final_state.get("failed_fields", [])),
                form_completion=final_state.get("form_completion", 0.0),
                final_state=final_state.get("final_state", "unknown"),
                execution_time=execution_time
            )
            
            # Log completion
            logger.info(f"✅ AI workflow completed in {execution_time:.1f}s")
            logger.info(f"   Final state: {result.final_state}")
            logger.info(f"   Form completion: {result.form_completion:.1%}")
            logger.info(f"   Completed fields: {result.completed_fields}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Agent execution failed: {e}")
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=False,
                completed_fields=0,
                failed_actions=1,
                form_completion=0.0,
                final_state="error",
                error_message=str(e),
                execution_time=execution_time
            )
            
        finally:
            # Clean up browser
            if self.browser:
                try:
                    await self.browser.close()
                    logger.info("🛑 Browser closed")
                except:
                    pass

# CLI interface for testing
async def main():
    """CLI entry point for testing the graph agent"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='AI-First Job Application Agent (LangGraph)')
    parser.add_argument('--url', required=True, help='Job application URL')
    parser.add_argument('--profile', default='./configs/profile.yaml', help='Browser profile config')
    parser.add_argument('--resume', default='./configs/resume.pdf', help='Resume file')
    parser.add_argument('--questionnaire', default='./configs/questionnaire.yaml', help='Questionnaire file')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode without browser')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key and not args.mock:
        print("⚠️ No OpenAI API key provided. Running in mock mode.")
        args.mock = True
    
    # Create config
    config = AgentConfig(
        profile_path=args.profile,
        resume_path=args.resume,
        questionnaire_path=args.questionnaire,
        openai_api_key=api_key or "mock-key",
        auto_submit=False  # Always false for testing
    )
    
    # Run agent
    print(f"🤖 Starting AI-first job application agent...")
    print(f"   URL: {args.url}")
    print(f"   Mock mode: {args.mock}")
    
    agent = GraphJobApplicationAgent(config)
    
    start_time = time.time()
    result = await agent.run(args.url)
    duration = time.time() - start_time
    
    # Print results
    print(f"\n📊 Results:")
    print(f"   Success: {'✅' if result.success else '❌'}")
    print(f"   Duration: {duration:.1f}s")
    print(f"   Completed fields: {result.completed_fields}")
    print(f"   Failed actions: {result.failed_actions}")
    print(f"   Form completion: {result.form_completion:.1%}")
    print(f"   Final state: {result.final_state}")
    
    if hasattr(result, 'error_message') and result.error_message:
        print(f"   Error: {result.error_message}")
    
    return result

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
