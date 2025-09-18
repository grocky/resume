#!/usr/bin/env python3
"""
Test script for template generation
"""

import yaml
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Get the project root directory
project_root = Path(__file__).parent.parent
data_dir = project_root / "data"
templates_dir = project_root / "templates"

def load_yaml_file(file_path):
    """Load a YAML file and return its contents"""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    """Test template generation with existing data"""

    # Load all data files
    personal = load_yaml_file(data_dir / "personal.yaml")
    background = load_yaml_file(data_dir / "background.yaml")
    achievements = load_yaml_file(data_dir / "achievements.yaml")
    skills = load_yaml_file(data_dir / "skills.yaml")
    edu_certs = load_yaml_file(data_dir / "education_and_certs.yaml")

    # For testing, select all roles with their achievements
    selected_roles = []
    for role in background['roles']:
        role_copy = role.copy()
        company_key = role['company'].replace(' ', '_')

        # Get achievements for this company
        role_achievements = []
        if company_key in achievements['by_company']:
            for ach in achievements['by_company'][company_key][:3]:  # Limit to 3 for testing
                # Escape LaTeX special characters
                content = ach['achievement']
                if ach.get('impact'):
                    content += f", {ach['impact']}"

                # Fix common LaTeX issues
                content = content.replace('&', '\\&')  # Fix ampersand
                content = content.replace('%', '\\%')  # Fix percent
                content = content.replace('$', '\\$')  # Fix dollar

                role_achievements.append({
                    'content': f"\\textbf{{{content}}}"
                })

        role_copy['achievements'] = role_achievements

        # Get skills/tags for this role
        role_copy['tags'] = skills['by_company'].get(company_key, [])

        selected_roles.append(role_copy)

    # Prepare template context
    context = {
        'personal': personal,
        'selected_roles': selected_roles,
        'strengths': edu_certs.get('strengths', []),
        'education': edu_certs.get('education', []),
        'certifications': edu_certs.get('certifications', []),
        'patents': edu_certs.get('patents', [])
    }

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('base_resume.tex')

    # Render the template
    output = template.render(context)

    # Write output
    output_file = project_root / "test_resume.tex"
    with open(output_file, 'w') as f:
        f.write(output)

    print(f"Template rendered successfully to: {output_file}")
    print("You can now compile with: latexmk -pdf test_resume.tex")

if __name__ == "__main__":
    main()