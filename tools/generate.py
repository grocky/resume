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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeGenerator:
    def __init__(self, project_root=None):
        """Initialize the resume generator with project paths"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.templates_dir = self.project_root / "templates"
        self.jobs_dir = self.project_root / "jobs"

        # Set up Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

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

    def select_and_filter_content(self, base_data, job_config):
        """Select and filter content based on job requirements"""
        logger.info("Selecting and filtering content for job requirements...")

        prompt_vars = job_config.get('prompt_vars', {})

        # Get content preferences
        max_achievements = prompt_vars.get('content_preferences', {}).get('max_achievements_per_role', 3)
        prioritize_quantified = prompt_vars.get('content_preferences', {}).get('prioritize_quantified', True)

        # Select roles (for now, include all roles)
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

    def generate(self, job_name, output_file=None):
        """Main generation function"""
        logger.info(f"Starting resume generation for job: {job_name}")

        # Load all data
        base_data = self.load_base_data()
        job_config = self.load_job_config(job_name)

        # Process content
        selected_roles = self.select_and_filter_content(base_data, job_config)
        context = self.prepare_template_context(base_data, selected_roles)

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
        return output_file

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate job-specific resume')
    parser.add_argument('--job', required=True, help='Job name (e.g., 2024-01-15_reddit_engineer)')
    parser.add_argument('--output', help='Output file path (optional)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        generator = ResumeGenerator()
        output_file = generator.generate(args.job, args.output)
        print(f"Resume generated: {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())