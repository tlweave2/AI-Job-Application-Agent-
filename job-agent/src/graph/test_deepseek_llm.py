#!/usr/bin/env python3
"""
Corrected test file for DeepSeek integration
Now imports from the correct deepseek_llm.py module
"""

import asyncio
import sys
import time
from pathlib import Path

# Add paths for imports (adjust as needed)
sys.path.insert(0, str(Path(__file__).parent))

async def test_deepseek_api():
    """Test DeepSeek API directly"""
    print("🧪 Testing DeepSeek API Integration")
    print("=" * 50)
    from deepseek_llm import DeepSeekLLMService
    api_key = "sk-317d3b46ff4b48589850a71ab85d00b4"
    llm_service = DeepSeekLLMService(api_key)
    print(f"🔑 Using API Key: {api_key[:20]}...")
    print(f"🌐 API Endpoint: https://api.deepseek.com/chat/completions")
    print(f"🤖 Model: deepseek-chat")
    test_prompt = """Analyze this job application form field and classify it.

FIELD DETAILS:
- HTML Tag: input
- Input Type: text
- CSS Selector: #firstName
- Placeholder Text: \"First Name\"
- Visible Text: \"\"
- Required Field: True
- Nearby Labels: Personal Information | First Name *

PAGE CONTEXT:
- Page Title: \"Software Engineer Application\"
- Page URL: https://company.com/careers/apply

CLASSIFICATION TASK:
Determine the best strategy for filling this field automatically.

AVAILABLE STRATEGIES:
1. \"simple_mapping\" - Direct user data (name, email, phone, address, etc.)
2. \"rag_generation\" - AI-generated content (essays, cover letters, explanations)
3. \"option_selection\" - Choose from dropdown/radio options
4. \"skip_field\" - Skip entirely (assessments, tests, out-of-scope)

RESPOND WITH VALID JSON ONLY:
{
    \"fill_strategy\": \"simple_mapping\",
    \"complexity\": \"trivial\",
    \"confidence\": 0.95,
    \"reasoning\": \"Clear first name field\",
    \"mapped_to\": \"personal.first_name\",
    \"requires_rag\": false,
    \"estimated_time\": 0.5,
    \"priority\": 80
}"""
    try:
        print("\n🚀 Sending test request to DeepSeek...")
        start_time = time.time()
        response = await llm_service.classify_field(test_prompt)
        end_time = time.time()
        duration = end_time - start_time
        print(f"✅ API Response received in {duration:.2f}s")
        print("\n📋 DeepSeek Classification Result:")
        print(f"   Strategy: {response.get('fill_strategy')}")
        print(f"   Complexity: {response.get('complexity')}")
        print(f"   Confidence: {response.get('confidence')}")
        print(f"   Reasoning: {response.get('reasoning')}")
        print(f"   Mapped To: {response.get('mapped_to')}")
        required_fields = ['fill_strategy', 'complexity', 'confidence', 'reasoning']
        missing_fields = [field for field in required_fields if field not in response]
        if missing_fields:
            print(f"⚠️  Warning: Missing fields in response: {missing_fields}")
        else:
            print("✅ Response format is valid")
        return True
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if hasattr(llm_service, 'session') and llm_service.session:
            await llm_service.session.close()

def main():
    print("\n🚀 Running DeepSeek API Test")
    asyncio.run(test_deepseek_api())

if __name__ == "__main__":
    main()
