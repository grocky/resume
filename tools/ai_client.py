#!/usr/bin/env python3
"""
AI Client for Resume Generation

Provides a unified interface for interacting with AI APIs (OpenAI, Anthropic)
to analyze job descriptions and generate tailored resume content.

Features:
- Multi-provider support (OpenAI, Anthropic)
- Rate limiting and retry logic
- API key management
- Response validation and error handling
- Prompt template management
"""

import os
import time
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

# Optional imports - will be installed if needed
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int
    cost_estimate: float = 0.0
    success: bool = True
    error: Optional[str] = None

class AIClient:
    """Unified AI client supporting multiple providers"""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize AI client with configuration"""
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"

        # Load configuration
        self.settings = self._load_settings()
        self.api_keys = self._load_api_keys()

        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None

        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # seconds between requests

    def _load_settings(self) -> Dict:
        """Load AI settings from configuration"""
        settings_file = self.config_dir / "settings.yaml"
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('ai', {})
        return {}

    def _load_api_keys(self) -> Dict:
        """Load API keys from configuration or environment"""
        api_keys = {}

        # Try loading from api_keys.yaml
        api_keys_file = self.config_dir / "api_keys.yaml"
        if api_keys_file.exists():
            with open(api_keys_file, 'r') as f:
                api_keys = yaml.safe_load(f) or {}

        # Override with environment variables if available
        if os.getenv('OPENAI_API_KEY'):
            api_keys.setdefault('openai', {})['api_key'] = os.getenv('OPENAI_API_KEY')

        if os.getenv('ANTHROPIC_API_KEY'):
            api_keys.setdefault('anthropic', {})['api_key'] = os.getenv('ANTHROPIC_API_KEY')

        return api_keys

    def _get_openai_client(self):
        """Get or create OpenAI client"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")

        if self.openai_client is None:
            api_key = self.api_keys.get('openai', {}).get('api_key')
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or add to config/api_keys.yaml")

            self.openai_client = openai.OpenAI(api_key=api_key)

        return self.openai_client

    def _get_anthropic_client(self):
        """Get or create Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not available. Install with: pip install anthropic")

        if self.anthropic_client is None:
            api_key = self.api_keys.get('anthropic', {}).get('api_key')
            if not api_key:
                raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or add to config/api_keys.yaml")

            self.anthropic_client = anthropic.Anthropic(api_key=api_key)

        return self.anthropic_client

    def _rate_limit(self, provider: AIProvider):
        """Apply rate limiting between requests"""
        now = time.time()
        last_time = self.last_request_time.get(provider.value, 0)

        time_since_last = now - last_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {provider.value}")
            time.sleep(sleep_time)

        self.last_request_time[provider.value] = time.time()

    def _call_openai(self, prompt: str, model: str = None, max_tokens: int = 2000, temperature: float = 0.3) -> AIResponse:
        """Call OpenAI API"""
        try:
            client = self._get_openai_client()

            if model is None:
                model = self.settings.get('model_preferences', {}).get('openai', 'gpt-4')

            self._rate_limit(AIProvider.OPENAI)

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(f"OpenAI API call successful - Model: {model}, Tokens: {tokens_used}")

            return AIResponse(
                content=content,
                provider=AIProvider.OPENAI,
                model=model,
                tokens_used=tokens_used,
                success=True
            )

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return AIResponse(
                content="",
                provider=AIProvider.OPENAI,
                model=model or "unknown",
                tokens_used=0,
                success=False,
                error=str(e)
            )

    def _call_anthropic(self, prompt: str, model: str = None, max_tokens: int = 2000, temperature: float = 0.3) -> AIResponse:
        """Call Anthropic API"""
        try:
            client = self._get_anthropic_client()

            if model is None:
                model = self.settings.get('model_preferences', {}).get('anthropic', 'claude-3-sonnet-20240229')

            self._rate_limit(AIProvider.ANTHROPIC)

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens if response.usage else 0

            logger.info(f"Anthropic API call successful - Model: {model}, Tokens: {tokens_used}")

            return AIResponse(
                content=content,
                provider=AIProvider.ANTHROPIC,
                model=model,
                tokens_used=tokens_used,
                success=True
            )

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            return AIResponse(
                content="",
                provider=AIProvider.ANTHROPIC,
                model=model or "unknown",
                tokens_used=0,
                success=False,
                error=str(e)
            )

    def generate(self, prompt: str, provider: Union[str, AIProvider] = None, **kwargs) -> AIResponse:
        """Generate AI response using specified or default provider"""

        # Determine provider
        if provider is None:
            provider_str = self.settings.get('default_provider', 'openai')
            provider = AIProvider(provider_str)
        elif isinstance(provider, str):
            provider = AIProvider(provider)

        logger.info(f"Generating AI response using {provider.value}")

        # Route to appropriate provider
        if provider == AIProvider.OPENAI:
            return self._call_openai(prompt, **kwargs)
        elif provider == AIProvider.ANTHROPIC:
            return self._call_anthropic(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def is_provider_available(self, provider: Union[str, AIProvider]) -> bool:
        """Check if a provider is available and configured"""
        if isinstance(provider, str):
            provider = AIProvider(provider)

        try:
            if provider == AIProvider.OPENAI:
                return OPENAI_AVAILABLE and bool(self.api_keys.get('openai', {}).get('api_key'))
            elif provider == AIProvider.ANTHROPIC:
                return ANTHROPIC_AVAILABLE and bool(self.api_keys.get('anthropic', {}).get('api_key'))
            return False
        except:
            return False

    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available and configured providers"""
        providers = []
        for provider in AIProvider:
            if self.is_provider_available(provider):
                providers.append(provider)
        return providers

# Prompt templates for different AI tasks
class PromptTemplates:
    """Collection of prompt templates for resume generation tasks"""

    @staticmethod
    def job_analysis_prompt(job_description: str) -> str:
        """Generate prompt for analyzing job descriptions"""
        return f"""
Analyze this job description and extract key information for resume tailoring:

JOB DESCRIPTION:
{job_description}

Please provide a structured analysis with the following:

1. REQUIRED SKILLS (must-have technical and soft skills)
2. PREFERRED SKILLS (nice-to-have skills)
3. KEY RESPONSIBILITIES (main duties and expectations)
4. COMPANY CULTURE INDICATORS (work style, values, environment)
5. KEYWORDS FOR OPTIMIZATION (important terms that should appear in resume)
6. ROLE FOCUS (technical vs leadership vs hybrid)

Format your response as structured text that can be easily parsed.
Focus on actionable insights for resume customization.
"""

    @staticmethod
    def achievement_rewrite_prompt(achievement: str, job_requirements: List[str], company_context: str = "") -> str:
        """Generate prompt for rewriting achievements"""
        requirements_text = "\n".join([f"- {req}" for req in job_requirements])

        return f"""
Rewrite this professional achievement to better align with the target job requirements while maintaining accuracy and authenticity:

ORIGINAL ACHIEVEMENT:
{achievement}

TARGET JOB REQUIREMENTS:
{requirements_text}

{f"COMPANY CONTEXT: {company_context}" if company_context else ""}

Please rewrite the achievement to:
1. Emphasize aspects most relevant to the target role
2. Use keywords that align with job requirements
3. Maintain factual accuracy - do not exaggerate or fabricate
4. Keep the professional tone and impact-focused language
5. Ensure it remains authentic to the original accomplishment

Provide only the rewritten achievement without explanation.
"""

    @staticmethod
    def content_prioritization_prompt(achievements: List[str], skills: List[str], job_requirements: List[str]) -> str:
        """Generate prompt for content prioritization"""
        achievements_text = "\n".join([f"{i+1}. {ach}" for i, ach in enumerate(achievements)])
        skills_text = ", ".join(skills)
        requirements_text = "\n".join([f"- {req}" for req in job_requirements])

        return f"""
Given these professional achievements and skills, prioritize and rank them for relevance to the target job:

ACHIEVEMENTS:
{achievements_text}

SKILLS:
{skills_text}

TARGET JOB REQUIREMENTS:
{requirements_text}

Please provide:
1. RANKED ACHIEVEMENTS (list numbers in priority order, most relevant first)
2. PRIORITY SKILLS (list skills in order of relevance)
3. JUSTIFICATION (brief explanation of ranking rationale)

Focus on direct relevance to job requirements and potential impact.
"""