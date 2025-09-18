#!/usr/bin/env python3
"""
AI-Powered Content Optimization Engine

Optimizes resume content for specific job applications by:
- Rewriting achievements to emphasize relevant aspects
- Prioritizing content based on job requirements
- Optimizing keywords while maintaining authenticity
- Tailoring content tone and focus

Maintains strict authenticity - never fabricates or exaggerates information.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ai_client import AIClient, PromptTemplates
from job_analyzer import JobAnalysis, JobAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class OptimizedContent:
    """Container for optimized resume content"""
    original_achievement: str
    optimized_achievement: str
    relevance_score: float
    optimization_notes: str

@dataclass
class ContentStrategy:
    """Strategy for content optimization based on job analysis"""
    focus_areas: List[str]  # What to emphasize
    keywords_to_include: List[str]  # Important keywords
    tone: str  # "technical", "leadership", "results-focused"
    max_achievements_per_role: int
    prioritize_quantified: bool

class ContentOptimizer:
    """AI-powered content optimization for job-specific resumes"""

    def __init__(self, ai_client: Optional[AIClient] = None):
        """Initialize content optimizer"""
        self.ai_client = ai_client or AIClient()

    def create_optimization_strategy(self, job_analysis: JobAnalysis, role_data: Dict) -> ContentStrategy:
        """Create optimization strategy based on job analysis"""
        logger.info("Creating content optimization strategy...")

        # Determine focus areas based on job requirements
        focus_areas = []
        focus_areas.extend(job_analysis.required_skills[:5])  # Top required skills
        focus_areas.extend(job_analysis.key_responsibilities[:3])  # Key responsibilities

        # Keywords to emphasize
        keywords = []
        keywords.extend(job_analysis.optimization_keywords[:10])
        keywords.extend(job_analysis.required_skills[:5])

        # Determine tone based on role focus
        tone_mapping = {
            "technical": "technical",
            "leadership": "leadership",
            "hybrid": "results-focused"
        }
        tone = tone_mapping.get(job_analysis.role_focus, "results-focused")

        # Achievement limits based on experience level
        max_achievements = {
            "junior": 2,
            "mid": 3,
            "senior": 4,
            "executive": 5
        }.get(job_analysis.experience_level, 3)

        strategy = ContentStrategy(
            focus_areas=focus_areas,
            keywords_to_include=keywords,
            tone=tone,
            max_achievements_per_role=max_achievements,
            prioritize_quantified=True
        )

        logger.info(f"Strategy created - Focus: {strategy.tone}, Max achievements: {strategy.max_achievements_per_role}")
        return strategy

    def optimize_achievement(self, achievement: str, job_requirements: List[str],
                           company_context: str = "", use_ai: bool = True) -> OptimizedContent:
        """
        Optimize a single achievement for job relevance

        Args:
            achievement: Original achievement text
            job_requirements: List of job requirements to align with
            company_context: Additional context about the company/role
            use_ai: Whether to use AI optimization

        Returns:
            OptimizedContent with original and optimized versions
        """
        logger.debug(f"Optimizing achievement: {achievement[:50]}...")

        if use_ai and self.ai_client.get_available_providers():
            return self._ai_optimize_achievement(achievement, job_requirements, company_context)
        else:
            return self._rule_based_optimize_achievement(achievement, job_requirements)

    def _ai_optimize_achievement(self, achievement: str, job_requirements: List[str],
                               company_context: str) -> OptimizedContent:
        """Use AI to optimize achievement"""
        try:
            # Generate optimization prompt
            prompt = PromptTemplates.achievement_rewrite_prompt(
                achievement, job_requirements, company_context
            )

            # Get AI response
            response = self.ai_client.generate(prompt, max_tokens=300, temperature=0.3)

            if response.success:
                optimized = response.content.strip()

                # Basic validation - ensure we didn't get explanation text
                if len(optimized) > len(achievement) * 3:  # Too long, probably includes explanation
                    # Try to extract just the achievement
                    lines = optimized.split('\n')
                    optimized = lines[0].strip()

                # Calculate relevance score based on keyword overlap
                relevance_score = self._calculate_relevance_score(optimized, job_requirements)

                return OptimizedContent(
                    original_achievement=achievement,
                    optimized_achievement=optimized,
                    relevance_score=relevance_score,
                    optimization_notes=f"AI optimized for: {', '.join(job_requirements[:3])}"
                )
            else:
                logger.warning(f"AI optimization failed: {response.error}")
                return self._rule_based_optimize_achievement(achievement, job_requirements)

        except Exception as e:
            logger.warning(f"AI optimization error: {e}")
            return self._rule_based_optimize_achievement(achievement, job_requirements)

    def _rule_based_optimize_achievement(self, achievement: str, job_requirements: List[str]) -> OptimizedContent:
        """Fallback rule-based optimization"""
        optimized = achievement

        # Simple keyword emphasis (add keywords if relevant)
        relevant_keywords = []
        achievement_lower = achievement.lower()

        for req in job_requirements:
            req_lower = req.lower()
            if any(word in achievement_lower for word in req_lower.split()):
                relevant_keywords.append(req)

        # Calculate relevance score
        relevance_score = len(relevant_keywords) / max(len(job_requirements), 1)

        return OptimizedContent(
            original_achievement=achievement,
            optimized_achievement=optimized,
            relevance_score=relevance_score,
            optimization_notes=f"Rule-based optimization. Keywords found: {', '.join(relevant_keywords)}"
        )

    def _calculate_relevance_score(self, text: str, requirements: List[str]) -> float:
        """Calculate relevance score based on requirement keyword overlap"""
        if not requirements:
            return 0.5

        text_lower = text.lower()
        matches = 0

        for req in requirements:
            req_words = req.lower().split()
            if any(word in text_lower for word in req_words):
                matches += 1

        return min(1.0, matches / len(requirements))

    def prioritize_achievements(self, achievements: List[Dict], job_analysis: JobAnalysis,
                              use_ai: bool = True) -> List[Dict]:
        """
        Prioritize achievements based on job relevance

        Args:
            achievements: List of achievement dictionaries
            job_analysis: Job analysis results
            use_ai: Whether to use AI for prioritization

        Returns:
            Sorted list of achievements by relevance
        """
        logger.info(f"Prioritizing {len(achievements)} achievements for job relevance...")

        if use_ai and self.ai_client.get_available_providers():
            return self._ai_prioritize_achievements(achievements, job_analysis)
        else:
            return self._rule_based_prioritize_achievements(achievements, job_analysis)

    def _ai_prioritize_achievements(self, achievements: List[Dict], job_analysis: JobAnalysis) -> List[Dict]:
        """Use AI to prioritize achievements"""
        try:
            # Prepare data for AI
            achievement_texts = [ach['achievement'] for ach in achievements]
            all_skills = job_analysis.required_skills + job_analysis.preferred_skills
            job_requirements = job_analysis.required_skills + job_analysis.key_responsibilities

            # Generate prioritization prompt
            prompt = PromptTemplates.content_prioritization_prompt(
                achievement_texts, all_skills, job_requirements
            )

            # Get AI response
            response = self.ai_client.generate(prompt, max_tokens=800)

            if response.success:
                # Parse AI ranking
                ranking = self._parse_ranking_response(response.content, len(achievements))

                if ranking:
                    # Reorder achievements based on AI ranking
                    reordered = []
                    for rank in ranking:
                        if 0 <= rank < len(achievements):
                            reordered.append(achievements[rank])

                    # Add any missing achievements
                    used_indices = set(ranking)
                    for i, ach in enumerate(achievements):
                        if i not in used_indices:
                            reordered.append(ach)

                    logger.info("AI prioritization completed successfully")
                    return reordered

        except Exception as e:
            logger.warning(f"AI prioritization failed: {e}")

        # Fallback to rule-based
        return self._rule_based_prioritize_achievements(achievements, job_analysis)

    def _parse_ranking_response(self, ai_response: str, num_achievements: int) -> Optional[List[int]]:
        """Parse AI ranking response to extract achievement order"""
        import re

        # Look for numbered rankings
        ranking_pattern = r'(?:RANKED ACHIEVEMENTS|1\.\s*RANKED)[:\s]*\n?(.*?)(?=\n\d+\.|$)'
        match = re.search(ranking_pattern, ai_response, re.DOTALL | re.IGNORECASE)

        if match:
            ranking_text = match.group(1)

            # Extract numbers
            numbers = re.findall(r'\b(\d+)\b', ranking_text)
            ranking = []

            for num_str in numbers:
                num = int(num_str) - 1  # Convert to 0-based index
                if 0 <= num < num_achievements:
                    ranking.append(num)

            return ranking

        return None

    def _rule_based_prioritize_achievements(self, achievements: List[Dict], job_analysis: JobAnalysis) -> List[Dict]:
        """Rule-based achievement prioritization"""

        # Score each achievement
        scored_achievements = []
        all_requirements = job_analysis.required_skills + job_analysis.key_responsibilities

        for ach in achievements:
            score = 0
            text = ach['achievement'].lower()

            # Score based on keyword matches
            for req in all_requirements:
                req_words = req.lower().split()
                if any(word in text for word in req_words):
                    score += 1

            # Bonus for quantified achievements
            if ach.get('quantified', False):
                score += 0.5

            # Bonus for impact keywords
            impact_keywords = ['led', 'managed', 'increased', 'reduced', 'improved', 'generated', 'delivered']
            if any(keyword in text for keyword in impact_keywords):
                score += 0.3

            scored_achievements.append((score, ach))

        # Sort by score (descending)
        scored_achievements.sort(key=lambda x: x[0], reverse=True)

        logger.info("Rule-based prioritization completed")
        return [ach for score, ach in scored_achievements]

    def optimize_role_content(self, role_data: Dict, achievements: List[Dict],
                            strategy: ContentStrategy, job_analysis: JobAnalysis) -> Dict:
        """
        Optimize all content for a specific role

        Args:
            role_data: Role information (title, company, etc.)
            achievements: List of achievements for this role
            strategy: Optimization strategy
            job_analysis: Job analysis results

        Returns:
            Optimized role data with tailored achievements
        """
        logger.info(f"Optimizing content for {role_data.get('company', 'Unknown')} role...")

        # Prioritize achievements
        prioritized_achievements = self.prioritize_achievements(achievements, job_analysis)

        # Select top achievements based on strategy
        selected_achievements = prioritized_achievements[:strategy.max_achievements_per_role]

        # Optimize each selected achievement
        optimized_achievements = []
        job_requirements = job_analysis.required_skills + job_analysis.key_responsibilities

        for ach in selected_achievements:
            company_context = f"Role: {role_data.get('title', '')}, Company: {role_data.get('company', '')}"

            optimized = self.optimize_achievement(
                ach['achievement'],
                job_requirements[:5],  # Use top 5 requirements
                company_context
            )

            # Create achievement entry for template
            achievement_entry = {
                'content': f"\\textbf{{{optimized.optimized_achievement}}}",
                'relevance_score': optimized.relevance_score,
                'optimization_notes': optimized.optimization_notes
            }
            optimized_achievements.append(achievement_entry)

        # Create optimized role data
        optimized_role = role_data.copy()
        optimized_role['achievements'] = optimized_achievements

        logger.info(f"Optimized {len(optimized_achievements)} achievements for role")
        return optimized_role

def main():
    """Test the content optimizer"""
    import argparse

    parser = argparse.ArgumentParser(description='Test content optimization')
    parser.add_argument('--job', required=True, help='Job name for testing')

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    # Load job analysis
    analyzer = JobAnalyzer()
    job_analysis = analyzer.load_analysis(args.job)

    if not job_analysis:
        print(f"No job analysis found for: {args.job}")
        print("Run job analyzer first")
        return

    # Test content optimization
    optimizer = ContentOptimizer()

    # Create strategy
    strategy = optimizer.create_optimization_strategy(job_analysis, {})
    print(f"Strategy: {strategy}")

    # Test achievement optimization
    test_achievement = "Led a team of 5 engineers to build a new payment processing system"
    optimized = optimizer.optimize_achievement(
        test_achievement,
        job_analysis.required_skills[:3]
    )

    print(f"\nOriginal: {optimized.original_achievement}")
    print(f"Optimized: {optimized.optimized_achievement}")
    print(f"Relevance: {optimized.relevance_score:.2f}")

if __name__ == "__main__":
    main()