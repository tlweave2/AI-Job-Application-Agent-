import pytest
import asyncio
from typing import Dict, List
import time

from models.snapshot import ActionableElement
from graph.field_classifier import IntelligentFieldClassifier, FieldComplexity
from models.graph_state import FillStrategy

class TestFieldClassifier:
    """Comprehensive tests for the intelligent field classifier"""
    
    @pytest.fixture
    def classifier(self):
        return IntelligentFieldClassifier()
    
    @pytest.fixture
    def sample_elements(self):
        """Sample form elements for testing"""
        return [
            # Trivial personal info
            ActionableElement(
                tag="input", type="text", selector="#firstName",
                text="", placeholder="First Name", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "firstName", "id": "firstName"}
            ),
            ActionableElement(
                tag="input", type="email", selector="#emailAddress",
                text="", placeholder="Enter your email", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "email", "id": "emailAddress"}
            ),
            ActionableElement(
                tag="input", type="tel", selector="#phoneNumber",
                text="", placeholder="Phone Number", value="",
                required=False, visible=True, enabled=True,
                bounds={}, attributes={"name": "phone", "id": "phoneNumber"}
            ),
            
            # Professional info
            ActionableElement(
                tag="input", type="text", selector="#currentTitle",
                text="", placeholder="Current Job Title", value="",
                required=False, visible=True, enabled=True,
                bounds={}, attributes={"name": "jobTitle", "id": "currentTitle"}
            ),
            ActionableElement(
                tag="select", type="", selector="#experienceYears",
                text="Years of Experience", placeholder="", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "experience", "id": "experienceYears"}
            ),
            
            # Complex RAG fields
            ActionableElement(
                tag="textarea", type="", selector="#coverLetter",
                text="", placeholder="Tell us why you're interested in this position", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "coverLetter", "maxlength": "2000"}
            ),
            ActionableElement(
                tag="textarea", type="", selector="#workExperience",
                text="", placeholder="Describe your relevant work experience", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "experience", "maxlength": "1500"}
            ),
            ActionableElement(
                tag="textarea", type="", selector="#challengeExample",
                text="", placeholder="Give an example of a time when you overcame a significant challenge", value="",
                required=False, visible=True, enabled=True,
                bounds={}, attributes={"name": "behavioral", "maxlength": "1000"}
            ),
            
            # Assessment fields (should be skipped)
            ActionableElement(
                tag="div", type="", selector="#technicalQuiz",
                text="Technical Assessment", placeholder="", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"class": "technical-test", "data-test": "coding-challenge"}
            ),
            ActionableElement(
                tag="textarea", type="", selector="#codingSample",
                text="", placeholder="Please solve this coding problem", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "codingTest", "data-assessment": "true"}
            )
        ]
    
    @pytest.fixture
    def page_contexts(self):
        """Different page contexts for testing"""
        return {
            "basic_form": {
                "title": "Job Application Form",
                "url": "https://company.com/apply",
                "nearby_text": {
                    "#firstName": ["Personal Information", "First Name *"],
                    "#emailAddress": ["Contact Details", "Email Address"],
                    "#phoneNumber": ["Contact Information", "Phone Number"],
                    "#currentTitle": ["Work Experience", "Current Position"],
                    "#experienceYears": ["Experience Level", "Years in Industry"],
                    "#coverLetter": ["Application Essays", "Cover Letter"],
                    "#workExperience": ["Professional Background", "Work History"],
                    "#challengeExample": ["Behavioral Questions", "Challenge Example"],
                    "#technicalQuiz": ["Assessments", "Technical Evaluation"],
                    "#codingSample": ["Code Test", "Programming Challenge"]
                }
            },
            "developer_role": {
                "title": "Senior Software Engineer Application",
                "url": "https://techcorp.com/careers/senior-engineer",
                "nearby_text": {
                    "#coverLetter": ["Why do you want to work at TechCorp?"],
                    "#workExperience": ["Describe your software development experience"],
                    "#challengeExample": ["Tell us about a technical challenge you solved"]
                }
            }
        }
    
    def test_personal_info_classification(self, classifier, sample_elements, page_contexts):
        """Test classification of personal information fields"""
        
        context = page_contexts["basic_form"]
        
        # Test first name
        firstName_element = sample_elements[0]
        classification = classifier.classify_field(firstName_element, context)
        
        assert classification.fill_strategy == FillStrategy.SIMPLE_MAPPING
        assert classification.complexity == FieldComplexity.TRIVIAL
        assert classification.confidence >= 0.9
        assert classification.mapped_to == "personal.first_name"
        assert not classification.requires_rag
        
        # Test email
        email_element = sample_elements[1]
        classification = classifier.classify_field(email_element, context)
        
        assert classification.fill_strategy == FillStrategy.SIMPLE_MAPPING
        assert classification.complexity == FieldComplexity.TRIVIAL
        assert classification.confidence >= 0.9
        assert classification.mapped_to == "personal.email"
        
        # Test phone
        phone_element = sample_elements[2]
        classification = classifier.classify_field(phone_element, context)
        
        assert classification.fill_strategy == FillStrategy.SIMPLE_MAPPING
        assert classification.mapped_to == "personal.phone"
    
    def test_professional_info_classification(self, classifier, sample_elements, page_contexts):
        """Test classification of professional information fields"""
        
        context = page_contexts["basic_form"]
        
        # Test current title
        title_element = sample_elements[3]
        classification = classifier.classify_field(title_element, context)
        
        assert classification.fill_strategy == FillStrategy.SIMPLE_MAPPING
        assert classification.complexity in [FieldComplexity.SIMPLE, FieldComplexity.TRIVIAL]
        assert classification.mapped_to == "experience.current_title"
        
        # Test experience years (dropdown)
        exp_element = sample_elements[4]
        classification = classifier.classify_field(exp_element, context)
        
        assert classification.fill_strategy == FillStrategy.OPTION_SELECTION
        assert classification.complexity == FieldComplexity.MEDIUM
    
    def test_rag_field_classification(self, classifier, sample_elements, page_contexts):
        """Test classification of fields requiring RAG"""
        
        context = page_contexts["basic_form"]
        
        # Test cover letter
        cover_element = sample_elements[5]
        classification = classifier.classify_field(cover_element, context)
        
        assert classification.fill_strategy == FillStrategy.RAG_GENERATION
        assert classification.complexity == FieldComplexity.COMPLEX
        assert classification.requires_rag
        assert classification.max_length == 2000
        assert classification.estimated_time >= 3.0
        
        # Test work experience
        work_element = sample_elements[6]
        classification = classifier.classify_field(work_element, context)
        
        assert classification.fill_strategy == FillStrategy.RAG_GENERATION
        assert classification.requires_rag
        
        # Test behavioral question
        behavioral_element = sample_elements[7]
        classification = classifier.classify_field(behavioral_element, context)
        
        assert classification.fill_strategy == FillStrategy.RAG_GENERATION
        assert classification.requires_rag
    
    def test_assessment_field_classification(self, classifier, sample_elements, page_contexts):
        """Test that assessment fields are correctly identified and skipped"""
        
        context = page_contexts["basic_form"]
        
        # Test technical quiz
        quiz_element = sample_elements[8]
        classification = classifier.classify_field(quiz_element, context)
        
        assert classification.fill_strategy == FillStrategy.SKIP_FIELD
        assert classification.complexity == FieldComplexity.EXPERT
        assert not classification.requires_rag
        
        # Test coding sample
        code_element = sample_elements[9]
        classification = classifier.classify_field(code_element, context)
        
        assert classification.fill_strategy == FillStrategy.SKIP_FIELD
        assert classification.complexity == FieldComplexity.EXPERT
    
    def test_confidence_scores(self, classifier, sample_elements, page_contexts):
        """Test that confidence scores are reasonable"""
        
        context = page_contexts["basic_form"]
        
        confidences = []
        for element in sample_elements[:7]:  # Exclude assessment fields
            classification = classifier.classify_field(element, context)
            confidences.append(classification.confidence)
        
        # All confidences should be reasonable
        assert all(0.3 <= conf <= 1.0 for conf in confidences)
        
        # Personal info should have highest confidence
        personal_confidences = confidences[:3]
        assert all(conf >= 0.8 for conf in personal_confidences)
    
    def test_classification_caching(self, classifier, sample_elements, page_contexts):
        """Test that classification results are cached properly"""
        
        context = page_contexts["basic_form"]
        element = sample_elements[0]
        
        # First classification
        start_time = time.time()
        classification1 = classifier.classify_field(element, context)
        first_time = time.time() - start_time
        
        # Second classification (should be cached)
        start_time = time.time()
        classification2 = classifier.classify_field(element, context)
        second_time = time.time() - start_time
        
        # Results should be identical
        assert classification1.fill_strategy == classification2.fill_strategy
        assert classification1.confidence == classification2.confidence
        
        # Second call should be faster (cached)
        assert second_time < first_time or second_time < 0.001
    
    def test_context_sensitivity(self, classifier, page_contexts):
        """Test that classification adapts to different contexts"""
        
        # Create same element with different contexts
        cover_letter_element = ActionableElement(
            tag="textarea", type="", selector="#coverLetter",
            text="", placeholder="Tell us about yourself", value="",
            required=True, visible=True, enabled=True,
            bounds={}, attributes={"name": "coverLetter"}
        )
        
        # Test with basic form context
        basic_classification = classifier.classify_field(
            cover_letter_element, page_contexts["basic_form"]
        )
        
        # Test with developer role context
        dev_classification = classifier.classify_field(
            cover_letter_element, page_contexts["developer_role"]
        )
        
        # Both should be RAG generation but may have different confidence
        assert basic_classification.fill_strategy == FillStrategy.RAG_GENERATION
        assert dev_classification.fill_strategy == FillStrategy.RAG_GENERATION
        assert both_classifications_reasonable(basic_classification, dev_classification)
    
    def test_edge_cases(self, classifier):
        """Test edge cases and unusual field configurations"""
        
        # Element with minimal information
        minimal_element = ActionableElement(
            tag="input", type="text", selector="#unknown",
            text="", placeholder="", value="",
            required=False, visible=True, enabled=True,
            bounds={}, attributes={}
        )
        
        minimal_context = {"title": "", "url": "", "nearby_text": {}}
        
        classification = classifier.classify_field(minimal_element, minimal_context)
        
        # Should still provide a classification with low confidence
        assert classification.fill_strategy in [
            FillStrategy.SIMPLE_MAPPING, 
            FillStrategy.SKIP_FIELD
        ]
        assert classification.confidence < 0.5
    
    def test_performance_benchmarks(self, classifier, sample_elements, page_contexts):
        """Test classification performance benchmarks"""
        
        context = page_contexts["basic_form"]
        
        # Benchmark classification speed
        start_time = time.time()
        
        for _ in range(100):  # Classify 100 times
            for element in sample_elements[:5]:  # Use first 5 elements
                classifier.classify_field(element, context)
        
        total_time = time.time() - start_time
        avg_time_per_classification = total_time / 500
        
        # Should be fast (under 10ms per classification with caching)
        assert avg_time_per_classification < 0.01
        
        # Test memory usage doesn't grow unbounded
        initial_cache_size = len(classifier.classification_cache)
        
        # Classify many different elements
        for i in range(50):
            test_element = ActionableElement(
                tag="input", type="text", selector=f"#field{i}",
                text="", placeholder=f"Field {i}", value="",
                required=False, visible=True, enabled=True,
                bounds={}, attributes={"name": f"field{i}"}
            )
            classifier.classify_field(test_element, context)
        
        final_cache_size = len(classifier.classification_cache)
        
        # Cache should grow but not excessively
        assert final_cache_size > initial_cache_size
        assert final_cache_size < initial_cache_size + 100  # Reasonable growth

def both_classifications_reasonable(class1, class2):
    """Helper function to check if both classifications are reasonable"""
    return (
        class1.confidence > 0.3 and class2.confidence > 0.3 and
        class1.fill_strategy == class2.fill_strategy
    )

class TestIntegrationWithGraph:
    """Integration tests with the graph workflow"""
    
    @pytest.fixture
    def mock_graph_state(self):
        return {
            "url": "https://company.com/apply",
            "field_queue": [],
            "completed_fields": [],
            "failed_fields": [],
            "skipped_fields": [],
            "user_data": {
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
        }
    
    @pytest.mark.asyncio
    async def test_enhanced_page_analysis(self, mock_graph_state):
        """Test enhanced page analysis with classification"""
        
        # Mock browser and services
        mock_browser = MockBrowser()
        mock_llm = MockLLMServices()
        mock_rag = MockRAGPipeline()
        
        from graph.enhanced_nodes import EnhancedGraphNodes
        enhanced_nodes = EnhancedGraphNodes(mock_browser, mock_llm, mock_rag)
        
        # Run page analysis
        result_state = await enhanced_nodes.enhanced_page_analysis_node(mock_graph_state)
        
        # Verify results
        assert "field_queue" in result_state
        assert "classification_stats" in result_state
        assert result_state["total_fields"] > 0
        
        # Check that fields are properly classified and prioritized
        field_queue = result_state["field_queue"]
        
        # Required fields should come first
        first_field = field_queue[0]
        assert first_field["element"].required or first_field["priority"] > 50
        
        # Fields should have classifications
        for field_info in field_queue:
            assert "classification" in field_info
            classification = field_info["classification"]
            assert hasattr(classification, 'fill_strategy')
            assert hasattr(classification, 'confidence')
    
    @pytest.mark.asyncio
    async def test_intelligent_field_routing(self, mock_graph_state):
        """Test that fields are routed to appropriate handlers"""
        
        from graph.enhanced_workflow import route_after_field_analysis
        
        # Test simple mapping field
        simple_field_state = {
            **mock_graph_state,
            "current_field": {
                "classification": MockClassification(FillStrategy.SIMPLE_MAPPING)
            }
        }
        
        route = route_after_field_analysis(simple_field_state)
        assert route == "simple_fill"
        
        # Test RAG field
        rag_field_state = {
            **mock_graph_state,
            "current_field": {
                "classification": MockClassification(FillStrategy.RAG_GENERATION)
            }
        }
        
        route = route_after_field_analysis(rag_field_state)
        assert route == "rag_fill"
        
        # Test skip field
        skip_field_state = {
            **mock_graph_state,
            "current_field": {
                "classification": MockClassification(FillStrategy.SKIP_FIELD)
            }
        }
        
        route = route_after_field_analysis(skip_field_state)
        assert route == "field_analysis"  # Skip and continue

# Mock classes for testing

class MockClassification:
    def __init__(self, fill_strategy):
        self.fill_strategy = fill_strategy
        self.confidence = 0.9
        self.complexity = FieldComplexity.SIMPLE
        self.requires_rag = (fill_strategy == FillStrategy.RAG_GENERATION)

class MockBrowser:
    async def snapshot(self):
        from models.snapshot import BrowserSnapshot, ActionableElement
        
        elements = [
            ActionableElement(
                tag="input", type="text", selector="#firstName",
                text="", placeholder="First Name", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "firstName"}
            ),
            ActionableElement(
                tag="textarea", type="", selector="#coverLetter",
                text="", placeholder="Cover Letter", value="",
                required=True, visible=True, enabled=True,
                bounds={}, attributes={"name": "coverLetter"}
            )
        ]
        
        return BrowserSnapshot(
            url="https://test.com",
            title="Test Form",
            actionable_elements=elements,
            form_count=1,
            submit_buttons=[],
            timestamp=time.time()
        )

class MockLLMServices:
    pass

class MockRAGPipeline:
    pass

# Benchmark test
def test_classifier_benchmark():
    """Benchmark test for production readiness"""
    
    classifier = IntelligentFieldClassifier()
    
    # Create many test elements
    test_elements = []
    for i in range(100):
        element = ActionableElement(
            tag="input", type="text", selector=f"#field{i}",
            text="", placeholder=f"Test Field {i}", value="",
            required=(i % 3 == 0), visible=True, enabled=True,
            bounds={}, attributes={"name": f"field{i}"}
        )
        test_elements.append(element)
    
    context = {
        "title": "Benchmark Test",
        "url": "https://test.com",
        "nearby_text": {}
    }
    
    # Benchmark classification
    start_time = time.time()
    
    classifications = []
    for element in test_elements:
        classification = classifier.classify_field(element, context)
        classifications.append(classification)
    
    total_time = time.time() - start_time
    
    print(f"\n📊 Classifier Benchmark Results:")
    print(f"   Classified {len(test_elements)} fields in {total_time:.3f}s")
    print(f"   Average time per field: {total_time/len(test_elements)*1000:.2f}ms")
    
    # Analyze classification distribution
    strategy_counts = {}
    complexity_counts = {}
    
    for classification in classifications:
        strategy = classification.fill_strategy.value
        complexity = classification.complexity.value
        
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
    
    print(f"   Strategy distribution: {strategy_counts}")
    print(f"   Complexity distribution: {complexity_counts}")
    
    # Performance assertions
    assert total_time < 1.0  # Should complete in under 1 second
    assert all(c.confidence > 0 for c in classifications)  # All should have confidence

if __name__ == "__main__":
    # Run the benchmark if called directly
    test_classifier_benchmark()
