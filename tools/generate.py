#!/usr/bin/env python3
"""
Resume Generation Engine

Generates job-specific resumes by:
1. Loading structured data from YAML files
2. Processing job-specific requirements
3. Selecting and filtering relevant content
4. Rendering Jinja2 templates to LaTeX
5. Preparing output for compilation

Usage:
    python tools/generate.py --job=2024-01-15_reddit_engineer
    python tools/generate.py --job=2024-01-15_reddit_engineer --output=custom.tex
"""

import argparse
import yaml
import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging

# AI-enhanced imports
from ai_client import AIClient
from job_analyzer import JobAnalyzer, JobAnalysis
from content_optimizer import ContentOptimizer, ContentStrategy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeGenerator:
    def __init__(self, project_root=None, enable_ai=True):
        """Initialize the resume generator with project paths"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.templates_dir = self.project_root / "templates"
        self.jobs_dir = self.project_root / "jobs"

        # Set up Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

        # Initialize AI components
        self.enable_ai = enable_ai
        if self.enable_ai:
            try:
                self.ai_client = AIClient()
                self.job_analyzer = JobAnalyzer(self.ai_client)
                self.content_optimizer = ContentOptimizer(self.ai_client)

                available_providers = self.ai_client.get_available_providers()
                if available_providers:
                    logger.info(f"AI enabled with providers: {[p.value for p in available_providers]}")
                else:
                    logger.warning("AI components initialized but no providers configured")
                    self.enable_ai = False
            except Exception as e:
                logger.warning(f"Failed to initialize AI components: {e}")
                self.enable_ai = False

        if not self.enable_ai:
            logger.info("AI features disabled - using rule-based generation")

    def load_yaml_file(self, file_path):
        """Load a YAML file and return its contents"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return {}

    def load_base_data(self):
        """Load all base data files"""
        logger.info("Loading base data files...")

        data = {
            'personal': self.load_yaml_file(self.data_dir / "personal.yaml"),
            'background': self.load_yaml_file(self.data_dir / "background.yaml"),
            'achievements': self.load_yaml_file(self.data_dir / "achievements.yaml"),
            'skills': self.load_yaml_file(self.data_dir / "skills.yaml"),
            'education_certs': self.load_yaml_file(self.data_dir / "education_and_certs.yaml")
        }

        logger.info(f"Loaded {len(data['background']['roles'])} roles")
        logger.info(f"Loaded achievements for {len(data['achievements']['by_company'])} companies")

        return data

    def load_job_config(self, job_name):
        """Load job-specific configuration"""
        job_dir = self.jobs_dir / job_name

        if not job_dir.exists():
            logger.error(f"Job directory does not exist: {job_dir}")
            return {}

        config = {}

        # Load prompt variables
        prompt_vars_file = job_dir / "prompt_vars.yaml"
        if prompt_vars_file.exists():
            config['prompt_vars'] = self.load_yaml_file(prompt_vars_file)
        else:
            logger.warning(f"No prompt_vars.yaml found for job: {job_name}")
            config['prompt_vars'] = {}

        # Load job description
        job_desc_file = job_dir / "job_description.md"
        if job_desc_file.exists():
            with open(job_desc_file, 'r') as f:
                config['job_description'] = f.read()
        else:
            logger.warning(f"No job_description.md found for job: {job_name}")
            config['job_description'] = ""

        return config

    def escape_latex(self, text):
        """Escape special LaTeX characters"""
        if not isinstance(text, str):
            return text

        # Common LaTeX character escapes
        replacements = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
            '\\': '\\textbackslash{}'
        }

        result = text
        for char, replacement in replacements.items():
            result = result.replace(char, replacement)

        return result

    def select_and_filter_content(self, base_data, job_config, job_analysis=None):
        """Select and filter content based on job requirements with AI optimization"""
        logger.info("Selecting and filtering content for job requirements...")

        prompt_vars = job_config.get('prompt_vars', {})

        # AI-enhanced content selection
        if self.enable_ai and job_analysis:
            return self._ai_enhanced_content_selection(base_data, job_config, job_analysis)
        else:
            return self._basic_content_selection(base_data, job_config)

    def _ai_enhanced_content_selection(self, base_data, job_config, job_analysis):
        """AI-enhanced content selection and optimization"""
        logger.info("Using AI-enhanced content selection...")

        # Create optimization strategy
        strategy = self.content_optimizer.create_optimization_strategy(job_analysis, {})

        selected_roles = []

        for role in base_data['background']['roles']:
            company_key = role['company'].replace(' ', '_')
            company_achievements = base_data['achievements']['by_company'].get(company_key, [])

            if company_achievements:
                # Use AI to optimize role content
                optimized_role = self.content_optimizer.optimize_role_content(
                    role, company_achievements, strategy, job_analysis
                )

                # Get skills/tags for this role
                optimized_role['tags'] = base_data['skills']['by_company'].get(company_key, [])

                selected_roles.append(optimized_role)
            else:
                # No achievements for this role, include basic info
                role_copy = role.copy()
                role_copy['achievements'] = []
                role_copy['tags'] = base_data['skills']['by_company'].get(company_key, [])
                selected_roles.append(role_copy)

        logger.info(f"AI-optimized {len(selected_roles)} roles")
        return selected_roles

    def _basic_content_selection(self, base_data, job_config):
        """Basic content selection without AI (fallback)"""
        logger.info("Using basic content selection...")

        prompt_vars = job_config.get('prompt_vars', {})

        # Get content preferences
        max_achievements = prompt_vars.get('content_preferences', {}).get('max_achievements_per_role', 3)
        prioritize_quantified = prompt_vars.get('content_preferences', {}).get('prioritize_quantified', True)

        selected_roles = []

        for role in base_data['background']['roles']:
            role_copy = role.copy()
            company_key = role['company'].replace(' ', '_')

            # Get achievements for this company
            role_achievements = []
            company_achievements = base_data['achievements']['by_company'].get(company_key, [])

            # Sort achievements by quantified status if prioritizing
            if prioritize_quantified:
                company_achievements = sorted(
                    company_achievements,
                    key=lambda x: x.get('quantified', False),
                    reverse=True
                )

            # Select top achievements
            for ach in company_achievements[:max_achievements]:
                content = ach['achievement']
                if ach.get('impact'):
                    content += f", {ach['impact']}"

                # Escape LaTeX special characters
                content = self.escape_latex(content)

                role_achievements.append({
                    'content': f"\\textbf{{{content}}}"
                })

            role_copy['achievements'] = role_achievements

            # Get skills/tags for this role
            role_copy['tags'] = base_data['skills']['by_company'].get(company_key, [])

            selected_roles.append(role_copy)

        logger.info(f"Selected {len(selected_roles)} roles with achievements")
        return selected_roles

    def prepare_template_context(self, base_data, selected_roles):
        """Prepare the context for template rendering"""
        education_certs = base_data['education_certs']

        context = {
            'personal': base_data['personal'],
            'selected_roles': selected_roles,
            'strengths': education_certs.get('strengths', []),
            'education': education_certs.get('education', []),
            'certifications': education_certs.get('certifications', []),
            'patents': education_certs.get('patents', [])
        }

        logger.info("Template context prepared")
        return context

    def render_resume(self, context, template_name='base_resume.tex'):
        """Render the resume template with the given context"""
        logger.info(f"Rendering template: {template_name}")

        try:
            template = self.env.get_template(template_name)
            output = template.render(context)
            logger.info("Template rendered successfully")
            return output
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise

    def analyze_job_description(self, job_name):
        """Analyze job description and save results"""
        if not self.enable_ai:
            logger.info("Job analysis skipped - AI disabled")
            return None

        # Check for existing analysis
        existing_analysis = self.job_analyzer.load_analysis(job_name)
        if existing_analysis:
            logger.info("Using existing job analysis")
            return existing_analysis

        # Load job description
        job_desc_file = self.jobs_dir / job_name / "job_description.md"
        if not job_desc_file.exists():
            logger.warning(f"Job description not found: {job_desc_file}")
            return None

        with open(job_desc_file, 'r') as f:
            job_description = f.read()

        # Perform analysis
        logger.info("Analyzing job description with AI...")
        job_analysis = self.job_analyzer.analyze_job_description(job_description)

        # Save analysis
        self.job_analyzer.save_analysis(job_analysis, job_name)
        logger.info("Job analysis completed and saved")

        return job_analysis

    def generate(self, job_name, output_file=None, force_reanalysis=False):
        """Main generation function with AI enhancement"""
        logger.info(f"Starting resume generation for job: {job_name}")

        # Load all data
        base_data = self.load_base_data()
        job_config = self.load_job_config(job_name)

        # Analyze job description (AI-enhanced)
        job_analysis = None
        if self.enable_ai:
            if force_reanalysis:
                # Force re-analysis by removing existing file
                analysis_file = self.jobs_dir / job_name / "analysis.yaml"
                if analysis_file.exists():
                    analysis_file.unlink()

            job_analysis = self.analyze_job_description(job_name)

        # Process content with AI optimization
        selected_roles = self.select_and_filter_content(base_data, job_config, job_analysis)
        context = self.prepare_template_context(base_data, selected_roles)

        # Add job analysis to context for potential template use
        if job_analysis:
            context['job_analysis'] = job_analysis.to_dict()

        # Render template
        output = self.render_resume(context)

        # Determine output file
        if not output_file:
            output_file = self.jobs_dir / job_name / "generated" / "resume.tex"
        else:
            output_file = Path(output_file)

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write output
        with open(output_file, 'w') as f:
            f.write(output)

        logger.info(f"Resume generated successfully: {output_file}")

        # Log generation summary
        if self.enable_ai and job_analysis:
            logger.info(f"AI Enhancement Summary:")
            logger.info(f"  - Role focus: {job_analysis.role_focus}")
            logger.info(f"  - Required skills: {len(job_analysis.required_skills)}")
            logger.info(f"  - Optimization keywords: {len(job_analysis.optimization_keywords)}")

        return output_file

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate job-specific resume with AI optimization')
    parser.add_argument('--job', required=True, help='Job name (e.g., 2024-01-15_reddit_engineer)')
    parser.add_argument('--output', help='Output file path (optional)')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI features')
    parser.add_argument('--force-reanalysis', action='store_true', help='Force re-analysis of job description')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        generator = ResumeGenerator(enable_ai=not args.no_ai)
        output_file = generator.generate(
            args.job,
            args.output,
            force_reanalysis=args.force_reanalysis
        )
        print(f"Resume generated: {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())