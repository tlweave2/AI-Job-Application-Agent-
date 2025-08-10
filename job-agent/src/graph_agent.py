from langgraph.graph import StateGraph
from .graph.workflow import create_job_application_graph
from .models.graph_state import ApplicationState

class GraphJobApplicationAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.workflow = create_job_application_graph()
        self.app = self.workflow.compile()
        
        # Initialize components (reuse existing)
        self.browser = BrowserRunner(config.profile_path)
        self.llm = LLMServices(config.openai_api_key)
        self.rag = RAGPipeline(config.openai_api_key)
        
    async def run(self, url: str) -> ExecutionResult:
        """Run the graph-based agent"""
        
        # Initialize state
        initial_state = ApplicationState(
            url=url,
            page_title="",
            current_snapshot={},
            field_queue=[],
            current_field=None,
            completed_fields=[],
            failed_fields=[],
            skipped_fields=[],
            user_data=self._load_user_data(),
            rag_context={"pipeline": self.rag},
            retry_count=0,
            cycle_count=0,
            execution_time=0.0,
            field_analysis=None,
            fill_strategy=None,
            requires_human=False,
            form_completion=0.0,
            should_submit=False,
            final_state="running"
        )
        
        # Start browser
        await self.browser.start()
        await self.browser.goto(url)
        
        # Run the graph
        try:
            final_state = await self.app.ainvoke(initial_state)
            
            return ExecutionResult(
                success=final_state["final_state"] in ["submitted", "ready_for_submit"],
                completed_fields=len(final_state["completed_fields"]),
                failed_actions=len(final_state["failed_fields"]),
                form_completion=final_state["form_completion"],
                final_state=final_state["final_state"]
            )
            
        finally:
            await self.browser.close()
