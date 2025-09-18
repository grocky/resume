#!/usr/bin/env python3
"""
Test script for AI client functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from ai_client import AIClient, PromptTemplates, AIProvider

def test_ai_client():
    """Test AI client basic functionality"""
    print("Testing AI Client...")

    # Initialize client
    client = AIClient()

    # Check available providers
    available_providers = client.get_available_providers()
    print(f"Available providers: {[p.value for p in available_providers]}")

    if not available_providers:
        print("No AI providers configured. Please set up API keys in config/api_keys.yaml or environment variables.")
        print("Example:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Test job analysis prompt
    sample_job_description = """
    Senior Software Engineer - Platform Team

    We're looking for an experienced software engineer to join our platform team.

    Requirements:
    - 5+ years of software development experience
    - Strong experience with Python, Go, or Java
    - Experience with cloud platforms (AWS, GCP, Azure)
    - Knowledge of containerization (Docker, Kubernetes)
    - Experience with API design and development
    - Strong system design skills

    Nice to have:
    - Leadership experience
    - Experience with microservices architecture
    - DevOps experience
    """

    print("\nTesting job description analysis...")
    analysis_prompt = PromptTemplates.job_analysis_prompt(sample_job_description)
    print(f"Generated prompt (first 200 chars): {analysis_prompt[:200]}...")

    # Test with available provider
    provider = available_providers[0]
    print(f"\nTesting API call with {provider.value}...")

    try:
        response = client.generate(
            prompt="Test prompt: Please respond with 'AI client is working correctly!'",
            provider=provider,
            max_tokens=100
        )

        if response.success:
            print(f"✅ Success! Response: {response.content[:100]}...")
            print(f"   Model: {response.model}")
            print(f"   Tokens: {response.tokens_used}")
        else:
            print(f"❌ API call failed: {response.error}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    print("\nAI Client test completed!")

if __name__ == "__main__":
    test_ai_client()