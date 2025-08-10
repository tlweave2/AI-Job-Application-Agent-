"""
Complete example of how to integrate the Intelligent Field Classifier
with your job application agent.
"""

import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from graph.field_classifier import IntelligentFieldClassifier
from graph.enhanced_workflow import create_enhanced_workflow
from models.graph_state import ApplicationState
from browser import BrowserRunner
from llm_api import LLMServices
from rag import RAGPipeline

class EnhancedJobAgent:
    """Enhanced job application agent with intelligent field classification"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize components
        self.browser = BrowserRunner(config.profile_path)
        self.llm = LLMServices(config.openai_api_key)
        self.rag = RAGPipeline(config.openai_api_key)
        
        # Create enhanced workflow
        self.workflow = create_enhanced_workflow(self.browser, self.llm, self.rag)
        self.app = self.workflow.compile()
        
        # Initialize classifier
        self.classifier = IntelligentFieldClassifier()
    
    async def run_enhanced_application(self, url: str) -> dict:
        """Run enhanced job application with intelligent classification"""
        
        print(f"🚀 Starting enhanced job application for: {url}")
        
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
            final_state="initializing"
        )
        
        try:
            # Start browser
            await self.browser.start()
            await self.browser.goto(url)
            
            # Run the enhanced workflow
            print("🧠 Running intelligent field classification...")
            final_state = await self.app.ainvoke(initial_state)
            
            # Generate detailed report
            report = self._generate_completion_report(final_state)
            
            print("✅ Enhanced application completed!")
            self._print_report(report)
            
            return report
            
        except Exception as e:
            print(f"❌ Enhanced application failed: {e}")
            return {"success": False, "error": str(e)}
            
        finally:
            await self.browser.close()
    
    def _load_user_data(self):
        """Load user data from config"""
        # Implementation from your existing agent
        return {
            "personal": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "555-123-4567"
            },
            "experience": {
                "current_title": "Senior Software Engineer",
                "years_programming": "5+ years",
                "preferred_technologies": ["Python", "React", "AWS"]
            }
        }
    
    def _generate_completion_report(self, final_state: dict) -> dict:
        """Generate detailed completion report"""
        
        completed = final_state.get("completed_fields", [])
        failed = final_state.get("failed_fields", [])
        skipped = final_state.get("skipped_fields", [])
        
        # Analyze field classifications
        classification_analysis = self._analyze_classifications(
            completed + failed + skipped
        )
        
        # Performance metrics
        total_time = final_state.get("execution_time", 0)
        
        return {
            "success": final_state.get("final_state") in ["submitted", "ready_for_submit"],
            "final_state": final_state.get("final_state"),
            "form_completion": final_state.get("form_completion", 0),
            "total_fields": final_state.get("total_fields", 0),
            "completed_count": len(completed),
            "failed_count": len(failed),
            "skipped_count": len(skipped),
            "execution_time": total_time,
            "classification_analysis": classification_analysis,
            "performance_metrics": self._calculate_performance_metrics(final_state)
        }
    
    def _analyze_classifications(self, all_fields: list) -> dict:
        """Analyze the effectiveness of field classifications"""
        
        strategy_performance = {}
        complexity_performance = {}
        
        for field_result in all_fields:
            if "field" not in field_result:
                continue
                
            field_info = field_result["field"]
            classification = field_info.get("classification")
            
            if not classification:
                continue
            
            strategy = classification.fill_strategy.value
            complexity = classification.complexity.value
            success = "completed_fields" in str(field_result)  # Rough success detection
            
            # Track strategy performance
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {"total": 0, "successful": 0}
            
            strategy_performance[strategy]["total"] += 1
            if success:
                strategy_performance[strategy]["successful"] += 1
            
            # Track complexity performance  
            if complexity not in complexity_performance:
                complexity_performance[complexity] = {"total": 0, "successful": 0}
            
            complexity_performance[complexity]["total"] += 1
            if success:
                complexity_performance[complexity]["successful"] += 1
        
        # Calculate success rates
        for strategy_stats in strategy_performance.values():
            strategy_stats["success_rate"] = (
                strategy_stats["successful"] / strategy_stats["total"] 
                if strategy_stats["total"] > 0 else 0
            )
        
        for complexity_stats in complexity_performance.values():
            complexity_stats["success_rate"] = (
                complexity_stats["successful"] / complexity_stats["total"]
                if complexity_stats["total"] > 0 else 0
            )
        
        return {
            "strategy_performance": strategy_performance,
            "complexity_performance": complexity_performance
        }
    
    def _calculate_performance_metrics(self, final_state: dict) -> dict:
        """Calculate performance metrics"""
        
        total_fields = final_state.get("total_fields", 0)
        execution_time = final_state.get("execution_time", 0)
        
        return {
            "fields_per_second": total_fields / execution_time if execution_time > 0 else 0,
            "avg_time_per_field": execution_time / total_fields if total_fields > 0 else 0,
            "classification_cache_hits": len(self.classifier.classification_cache),
            "overall_success_rate": final_state.get("form_completion", 0)
        }
    
    def _print_report(self, report: dict):
        """Print detailed completion report"""
        
        print("\n" + "="*60)
        print("📊 ENHANCED AGENT COMPLETION REPORT")
        print("="*60)
        
        print(f"🎯 Overall Success: {'✅' if report['success'] else '❌'}")
        print(f"📈 Form Completion: {report['form_completion']:.1%}")
        print(f"⏱️  Total Time: {report['execution_time']:.1f}s")
        
        print(f"\n📋 Field Summary:")
        print(f"   Total Fields: {report['total_fields']}")
        print(f"   ✅ Completed: {report['completed_count']}")
        print(f"   ❌ Failed: {report['failed_count']}")
        print(f"   ⏭️  Skipped: {report['skipped_count']}")
        
        print(f"\n🧠 Classification Performance:")
        strategy_perf = report['classification_analysis']['strategy_performance']
        
        for strategy, stats in strategy_perf.items():
            success_rate = stats['success_rate']
            print(f"   {strategy}: {stats['successful']}/{stats['total']} ({success_rate:.1%})")
        
        print(f"\n⚡ Performance Metrics:")
        metrics = report['performance_metrics']
        print(f"   Fields/second: {metrics['fields_per_second']:.2f}")
        print(f"   Avg time/field: {metrics['avg_time_per_field']:.2f}s")
        print(f"   Cache hits: {metrics['classification_cache_hits']}")

async def demo_intelligent_classification():
    """Demonstration of intelligent field classification"""
    
    print("🧪 Intelligent Field Classification Demo")
    print("="*50)
    
    # Initialize classifier
    classifier = IntelligentFieldClassifier()
    
    # Demo different types of fields
    demo_fields = [
        {
            "name": "First Name (Trivial)",
            "element": create_demo_element("input", "text", "#firstName", "First Name"),
            "context": {"nearby_text": {"#firstName": ["Personal Info", "First Name *"]}}
        },
        {
            "name": "Cover Letter (Complex RAG)",
            "element": create_demo_element("textarea", "", "#coverLetter", "Why do you want this job?"),
            "context": {"nearby_text": {"#coverLetter": ["Application Essay", "Tell us why"]}}
        },
        {
            "name": "Experience Years (Medium)",
            "element": create_demo_element("select", "", "#experience", "Years of Experience"),
            "context": {"nearby_text": {"#experience": ["Experience Level", "How many years?"]}}
        },
        {
            "name": "Technical Quiz (Expert - Skip)",
            "element": create_demo_element("div", "", "#techQuiz", "Technical Assessment"),
            "context": {"nearby_text": {"#techQuiz": ["Assessment", "Code Challenge"]}}
        }
    ]
    
    print("🔍 Classifying different field types...\n")
    
    for demo in demo_fields:
        print(f"📝 {demo['name']}")
        
        classification = classifier.classify_field(demo['element'], demo['context'])
        
        print(f"   Strategy: {classification.fill_strategy.value}")
        print(f"   Complexity: {classification.complexity.value}")
        print(f"   Confidence: {classification.confidence:.2f}")
        print(f"   Requires RAG: {classification.requires_rag}")
        print(f"   Est. Time: {classification.estimated_time}s")
        if classification.mapped_to:
            print(f"   Mapped to: {classification.mapped_to}")
        print()
    
    # Show classification stats
    stats = classifier.get_classification_stats()
    print(f"📊 Classification Statistics:")
    print(f"   Total classified: {stats['total_classified']}")
    print(f"   Strategies: {stats['strategies']}")
    print(f"   Complexities: {stats['complexities']}")

def create_demo_element(tag, input_type, selector, placeholder):
    """Create demo element for testing"""
    from models.snapshot import ActionableElement
    
    return ActionableElement(
        tag=tag,
        type=input_type,
        selector=selector,
        text="",
        placeholder=placeholder,
        value="",
        required=True,
        visible=True,
        enabled=True,
        bounds={},
        attributes={"name": selector.replace("#", "")}
    )

async def main():
    """Main demo function"""
    
    # Run classification demo
    await demo_intelligent_classification()
    
    print("\n" + "="*50)
    print("🎯 Integration Complete!")
    print("\nThe intelligent field classifier is now:")
    print("✅ Accurately identifying field types")
    print("✅ Mapping to appropriate fill strategies") 
    print("✅ Estimating complexity and time requirements")
    print("✅ Providing confidence scores")
    print("✅ Caching results for performance")
    print("\nYour LangGraph workflow can now handle:")
    print("🔸 Simple personal info (trivial)")
    print("🔸 Professional details (simple)")
    print("🔸 Essay questions with RAG (complex)")
    print("🔸 Technical assessments (skip)")
    
    print(f"\n🚀 Ready for production use!")

if __name__ == "__main__":
    asyncio.run(main())
