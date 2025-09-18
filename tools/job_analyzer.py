#!/usr/bin/env python3
"""
Job Description Analysis System

Analyzes job descriptions using AI to extract:
- Required vs preferred skills
- Key responsibilities
- Company culture indicators
- Keywords for optimization
- Role focus (technical vs leadership)

This analysis is used to tailor resume content for specific job applications.
"""

import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ai_client import AIClient, PromptTemplates

logger = logging.getLogger(__name__)

@dataclass
class JobAnalysis:
    """Structured job analysis results"""
    required_skills: List[str]
    preferred_skills: List[str]
    key_responsibilities: List[str]
    company_culture: List[str]
    optimization_keywords: List[str]
    role_focus: str  # "technical", "leadership", "hybrid"
    experience_level: str  # "junior", "mid", "senior", "executive"
    industry_domain: str  # e.g., "fintech", "healthcare", "enterprise"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'JobAnalysis':
        """Create from dictionary"""
        return cls(**data)

class JobAnalyzer:
    """Analyzes job descriptions and extracts actionable insights"""

    def __init__(self, ai_client: Optional[AIClient] = None):
        """Initialize job analyzer"""
        self.ai_client = ai_client or AIClient()

    def analyze_job_description(self, job_description: str, use_ai: bool = True) -> JobAnalysis:
        """
        Analyze a job description and extract structured insights

        Args:
            job_description: Raw job description text
            use_ai: Whether to use AI analysis (fallback to rule-based if False)

        Returns:
            JobAnalysis object with structured insights
        """
        logger.info("Starting job description analysis...")

        if use_ai and self.ai_client.get_available_providers():
            return self._ai_analysis(job_description)
        else:
            logger.info("Using rule-based analysis (AI not available or disabled)")
            return self._rule_based_analysis(job_description)

    def _ai_analysis(self, job_description: str) -> JobAnalysis:
        """Use AI to analyze job description"""
        logger.info("Performing AI-powered job analysis...")

        # Generate analysis prompt
        prompt = PromptTemplates.job_analysis_prompt(job_description)

        # Get AI response
        response = self.ai_client.generate(prompt, max_tokens=1500)

        if not response.success:
            logger.warning(f"AI analysis failed: {response.error}")
            logger.info("Falling back to rule-based analysis")
            return self._rule_based_analysis(job_description)

        # Parse AI response
        try:
            analysis = self._parse_ai_response(response.content)
            logger.info("AI analysis completed successfully")
            return analysis
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")
            logger.info("Falling back to rule-based analysis")
            return self._rule_based_analysis(job_description)

    def _parse_ai_response(self, ai_response: str) -> JobAnalysis:
        """Parse structured AI response into JobAnalysis object"""

        # Initialize with empty lists
        required_skills = []
        preferred_skills = []
        key_responsibilities = []
        company_culture = []
        optimization_keywords = []
        role_focus = "hybrid"
        experience_level = "mid"
        industry_domain = "technology"

        # Parse sections using regex patterns
        sections = {
            'required_skills': r'(?:REQUIRED SKILLS|1\.\s*REQUIRED SKILLS)[:\s]*\n?(.*?)(?=\n\d+\.|$)',
            'preferred_skills': r'(?:PREFERRED SKILLS|2\.\s*PREFERRED SKILLS)[:\s]*\n?(.*?)(?=\n\d+\.|$)',
            'key_responsibilities': r'(?:KEY RESPONSIBILITIES|3\.\s*KEY RESPONSIBILITIES)[:\s]*\n?(.*?)(?=\n\d+\.|$)',
            'company_culture': r'(?:COMPANY CULTURE|4\.\s*COMPANY CULTURE)[:\s]*\n?(.*?)(?=\n\d+\.|$)',
            'optimization_keywords': r'(?:KEYWORDS|5\.\s*KEYWORDS)[:\s]*\n?(.*?)(?=\n\d+\.|$)',
            'role_focus': r'(?:ROLE FOCUS|6\.\s*ROLE FOCUS)[:\s]*\n?(.*?)(?=\n\d+\.|$)'
        }

        for section_name, pattern in sections.items():
            match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()

                # Extract list items
                items = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove bullet points and numbering
                        line = re.sub(r'^[-*•]\s*', '', line)
                        line = re.sub(r'^\d+\.\s*', '', line)
                        if line:
                            items.append(line)

                # Assign to appropriate variable
                if section_name == 'required_skills':
                    required_skills = items[:10]  # Limit to reasonable number
                elif section_name == 'preferred_skills':
                    preferred_skills = items[:8]
                elif section_name == 'key_responsibilities':
                    key_responsibilities = items[:8]
                elif section_name == 'company_culture':
                    company_culture = items[:6]
                elif section_name == 'optimization_keywords':
                    optimization_keywords = items[:15]
                elif section_name == 'role_focus':
                    # Extract role focus
                    focus_text = content.lower()
                    if 'technical' in focus_text and 'leadership' not in focus_text:
                        role_focus = "technical"
                    elif 'leadership' in focus_text and 'technical' not in focus_text:
                        role_focus = "leadership"
                    else:
                        role_focus = "hybrid"

        # Determine experience level from original description
        experience_level = self._extract_experience_level(ai_response)

        # Determine industry domain
        industry_domain = self._extract_industry_domain(ai_response)

        return JobAnalysis(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            key_responsibilities=key_responsibilities,
            company_culture=company_culture,
            optimization_keywords=optimization_keywords,
            role_focus=role_focus,
            experience_level=experience_level,
            industry_domain=industry_domain
        )

    def _rule_based_analysis(self, job_description: str) -> JobAnalysis:
        """Fallback rule-based analysis when AI is not available"""
        text = job_description.lower()

        # Extract skills using common patterns
        skill_patterns = [
            r'(?:experience with|knowledge of|proficient in|skilled in)\s+([^.]+)',
            r'(?:required|must have|essential).*?:\s*([^.]+)',
            r'(?:technologies|tools|languages).*?:\s*([^.]+)'
        ]

        skills = set()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract individual skills
                skill_items = re.split(r'[,;]|\s+and\s+|\s+or\s+', match)
                for skill in skill_items:
                    skill = skill.strip()
                    if len(skill) > 2 and len(skill) < 30:  # Reasonable skill name length
                        skills.add(skill.title())

        skills_list = list(skills)[:15]  # Limit to 15 skills

        # Simple role focus detection
        role_focus = "hybrid"
        if any(word in text for word in ['manager', 'lead', 'director', 'leadership', 'team']):
            if any(word in text for word in ['technical', 'engineering', 'development']):
                role_focus = "hybrid"
            else:
                role_focus = "leadership"
        elif any(word in text for word in ['engineer', 'developer', 'programmer', 'technical']):
            role_focus = "technical"

        # Experience level detection
        experience_level = self._extract_experience_level(job_description)

        # Industry domain detection
        industry_domain = self._extract_industry_domain(job_description)

        # Split skills into required vs preferred (first 60% as required)
        split_point = max(1, int(len(skills_list) * 0.6))
        required_skills = skills_list[:split_point]
        preferred_skills = skills_list[split_point:]

        # Extract key responsibilities (simple pattern matching)
        responsibilities = []
        resp_patterns = [
            r'(?:responsibilities|duties|will be responsible for).*?:\s*([^.]+)',
            r'(?:you will|the role involves|responsibilities include)\s+([^.]+)'
        ]

        for pattern in resp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                resp_items = re.split(r'[,;]', match)
                for resp in resp_items:
                    resp = resp.strip()
                    if len(resp) > 10:
                        responsibilities.append(resp.capitalize())

        return JobAnalysis(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            key_responsibilities=responsibilities[:8],
            company_culture=[],  # Difficult to extract without AI
            optimization_keywords=skills_list[:10],
            role_focus=role_focus,
            experience_level=experience_level,
            industry_domain=industry_domain
        )

    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from job description"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['entry level', 'junior', '0-2 years', 'new grad']):
            return "junior"
        elif any(word in text_lower for word in ['senior', '5+ years', '7+ years', 'experienced']):
            return "senior"
        elif any(word in text_lower for word in ['director', 'vp', 'executive', 'c-level']):
            return "executive"
        else:
            return "mid"

    def _extract_industry_domain(self, text: str) -> str:
        """Extract industry domain from job description"""
        text_lower = text.lower()

        domains = {
            'fintech': ['fintech', 'financial', 'banking', 'payments', 'crypto'],
            'healthcare': ['healthcare', 'medical', 'health', 'pharma', 'biotech'],
            'enterprise': ['enterprise', 'b2b', 'saas', 'cloud', 'infrastructure'],
            'consumer': ['consumer', 'b2c', 'mobile', 'social', 'gaming'],
            'ecommerce': ['ecommerce', 'retail', 'marketplace', 'commerce'],
            'media': ['media', 'streaming', 'content', 'entertainment', 'advertising']
        }

        for domain, keywords in domains.items():
            if any(keyword in text_lower for keyword in keywords):
                return domain

        return "technology"

    def save_analysis(self, analysis: JobAnalysis, job_name: str) -> Path:
        """Save job analysis to file"""
        project_root = Path(__file__).parent.parent
        job_dir = project_root / "jobs" / job_name

        analysis_file = job_dir / "analysis.yaml"
        analysis_file.parent.mkdir(parents=True, exist_ok=True)

        with open(analysis_file, 'w') as f:
            yaml.dump(analysis.to_dict(), f, default_flow_style=False, sort_keys=False)

        logger.info(f"Analysis saved to: {analysis_file}")
        return analysis_file

    def load_analysis(self, job_name: str) -> Optional[JobAnalysis]:
        """Load existing job analysis from file"""
        project_root = Path(__file__).parent.parent
        analysis_file = project_root / "jobs" / job_name / "analysis.yaml"

        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                data = yaml.safe_load(f)
                return JobAnalysis.from_dict(data)

        return None

def main():
    """Test the job analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze job description')
    parser.add_argument('--job', required=True, help='Job name')
    parser.add_argument('--force', action='store_true', help='Force re-analysis even if cached')

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    analyzer = JobAnalyzer()

    # Check for existing analysis
    if not args.force:
        existing_analysis = analyzer.load_analysis(args.job)
        if existing_analysis:
            print("Found existing analysis:")
            print(yaml.dump(existing_analysis.to_dict(), default_flow_style=False))
            return

    # Load job description
    project_root = Path(__file__).parent.parent
    job_desc_file = project_root / "jobs" / args.job / "job_description.md"

    if not job_desc_file.exists():
        print(f"Job description not found: {job_desc_file}")
        return

    with open(job_desc_file, 'r') as f:
        job_description = f.read()

    # Analyze
    analysis = analyzer.analyze_job_description(job_description)

    # Save and display
    analyzer.save_analysis(analysis, args.job)
    print("Analysis completed:")
    print(yaml.dump(analysis.to_dict(), default_flow_style=False))

if __name__ == "__main__":
    main()