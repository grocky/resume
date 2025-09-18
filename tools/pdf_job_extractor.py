#!/usr/bin/env python3
"""
PDF Job Requisition Extractor

Extracts job information from PDF job postings using AI to automatically
populate job descriptions and analysis data. Eliminates manual copying
and ensures comprehensive information extraction.

Features:
- PDF text extraction with multiple fallback methods
- AI-powered intelligent job information extraction
- Automatic job folder creation and setup
- Integration with existing job analysis pipeline
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

# PDF processing imports
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ai_client import AIClient, PromptTemplates

logger = logging.getLogger(__name__)

@dataclass
class ExtractedJobInfo:
    """Container for extracted job information"""
    company: str
    role: str
    location: str
    job_type: str
    raw_description: str
    key_requirements: list
    nice_to_have: list
    company_culture: str
    salary_range: str = ""
    experience_level: str = ""

class PDFJobExtractor:
    """Extracts job information from PDF job postings using AI"""

    def __init__(self, ai_client: Optional[AIClient] = None):
        """Initialize PDF job extractor"""
        self.ai_client = ai_client or AIClient()
        self.project_root = Path(__file__).parent.parent

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from PDF using multiple fallback methods

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")

        # Try multiple PDF extraction methods in order of preference
        methods = []

        if PDFPLUMBER_AVAILABLE:
            methods.append(self._extract_with_pdfplumber)
        if PYMUPDF_AVAILABLE:
            methods.append(self._extract_with_pymupdf)
        if PYPDF2_AVAILABLE:
            methods.append(self._extract_with_pypdf2)

        if not methods:
            raise ImportError(
                "No PDF processing library available. Install one of: pdfplumber, PyMuPDF, or PyPDF2\n"
                "pip install pdfplumber  # Recommended\n"
                "pip install PyMuPDF     # Alternative\n"
                "pip install PyPDF2      # Fallback"
            )

        # Try each method until one succeeds
        last_error = None
        for method in methods:
            try:
                text = method(pdf_path)
                if text.strip():  # Ensure we got meaningful content
                    logger.info(f"Successfully extracted {len(text)} characters using {method.__name__}")
                    return text
                else:
                    logger.warning(f"{method.__name__} returned empty text")
            except Exception as e:
                logger.warning(f"{method.__name__} failed: {e}")
                last_error = e
                continue

        # If all methods failed
        raise Exception(f"Failed to extract text from PDF. Last error: {last_error}")

    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber (most reliable)"""
        import pdfplumber

        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts)

    def _extract_with_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF (good for complex layouts)"""
        import fitz

        text_parts = []
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text_parts.append(page.get_text())
        doc.close()

        return "\n".join(text_parts)

    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2 (basic fallback)"""
        import PyPDF2

        text_parts = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

        return "\n".join(text_parts)

    def extract_job_info_with_ai(self, pdf_text: str) -> ExtractedJobInfo:
        """
        Use AI to extract structured job information from PDF text

        Args:
            pdf_text: Raw text extracted from PDF

        Returns:
            ExtractedJobInfo with structured data
        """
        logger.info("Extracting job information using AI...")

        # Create comprehensive extraction prompt
        prompt = self._create_extraction_prompt(pdf_text)

        # Get AI response
        response = self.ai_client.generate(prompt, max_tokens=2000, temperature=0.1)

        if not response.success:
            raise Exception(f"AI extraction failed: {response.error}")

        # Parse AI response into structured data
        job_info = self._parse_ai_extraction_response(response.content, pdf_text)

        logger.info(f"Successfully extracted job info for: {job_info.company} - {job_info.role}")
        return job_info

    def _create_extraction_prompt(self, pdf_text: str) -> str:
        """Create comprehensive prompt for job information extraction"""
        return f"""
Extract structured job information from this job posting PDF text. Parse all relevant details for resume customization.

JOB POSTING TEXT:
{pdf_text}

Please extract and structure the following information in a clear, parseable format:

## BASIC INFO
- Company Name: [exact company name]
- Job Title: [exact role title]
- Location: [work location/remote info]
- Job Type: [full-time, contract, etc.]
- Experience Level: [junior, mid, senior, executive]
- Salary Range: [if mentioned]

## JOB DESCRIPTION
[Clean, formatted version of the job description suitable for markdown]

## KEY REQUIREMENTS (must-have)
- [List each required skill/qualification]
- [Include years of experience if specified]
- [Technical skills, education, certifications]

## NICE TO HAVE (preferred)
- [List each preferred skill/qualification]
- [Bonus qualifications]
- [Preferred experience]

## COMPANY CULTURE & VALUES
[Description of company culture, work environment, values mentioned in posting]

## ADDITIONAL DETAILS
[Any other relevant information like benefits, growth opportunities, team structure]

Format your response clearly with headers and bullet points for easy parsing.
Focus on information that would be useful for tailoring a resume.
"""

    def _parse_ai_extraction_response(self, ai_response: str, original_text: str) -> ExtractedJobInfo:
        """Parse AI response into ExtractedJobInfo structure"""

        # Initialize with defaults
        company = "Unknown Company"
        role = "Unknown Role"
        location = "Unknown Location"
        job_type = "Full-time"
        key_requirements = []
        nice_to_have = []
        company_culture = ""
        salary_range = ""
        experience_level = ""

        # Parse sections using regex patterns
        import re

        # Extract basic info
        company_match = re.search(r'Company Name:\s*(.+)', ai_response, re.IGNORECASE)
        if company_match:
            company = company_match.group(1).strip()

        role_match = re.search(r'Job Title:\s*(.+)', ai_response, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).strip()

        location_match = re.search(r'Location:\s*(.+)', ai_response, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).strip()

        job_type_match = re.search(r'Job Type:\s*(.+)', ai_response, re.IGNORECASE)
        if job_type_match:
            job_type = job_type_match.group(1).strip()

        experience_match = re.search(r'Experience Level:\s*(.+)', ai_response, re.IGNORECASE)
        if experience_match:
            experience_level = experience_match.group(1).strip()

        salary_match = re.search(r'Salary Range:\s*(.+)', ai_response, re.IGNORECASE)
        if salary_match:
            salary_range = salary_match.group(1).strip()

        # Extract job description
        desc_pattern = r'## JOB DESCRIPTION\s*\n(.*?)(?=\n##|$)'
        desc_match = re.search(desc_pattern, ai_response, re.DOTALL | re.IGNORECASE)
        job_description = desc_match.group(1).strip() if desc_match else original_text[:2000]

        # Extract requirements
        req_pattern = r'## KEY REQUIREMENTS.*?\n(.*?)(?=\n##|$)'
        req_match = re.search(req_pattern, ai_response, re.DOTALL | re.IGNORECASE)
        if req_match:
            req_text = req_match.group(1)
            key_requirements = self._extract_list_items(req_text)

        # Extract nice-to-have
        nice_pattern = r'## NICE TO HAVE.*?\n(.*?)(?=\n##|$)'
        nice_match = re.search(nice_pattern, ai_response, re.DOTALL | re.IGNORECASE)
        if nice_match:
            nice_text = nice_match.group(1)
            nice_to_have = self._extract_list_items(nice_text)

        # Extract company culture
        culture_pattern = r'## COMPANY CULTURE.*?\n(.*?)(?=\n##|$)'
        culture_match = re.search(culture_pattern, ai_response, re.DOTALL | re.IGNORECASE)
        if culture_match:
            company_culture = culture_match.group(1).strip()

        return ExtractedJobInfo(
            company=company,
            role=role,
            location=location,
            job_type=job_type,
            raw_description=job_description,
            key_requirements=key_requirements,
            nice_to_have=nice_to_have,
            company_culture=company_culture,
            salary_range=salary_range,
            experience_level=experience_level
        )

    def _extract_list_items(self, text: str) -> list:
        """Extract list items from text"""
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Remove bullet points and clean up
                line = re.sub(r'^[-*•]\s*', '', line)
                line = re.sub(r'^\d+\.\s*', '', line)
                if line and len(line) > 3:  # Reasonable minimum length
                    items.append(line)
        return items[:15]  # Limit to reasonable number

    def create_job_folder(self, job_info: ExtractedJobInfo, job_name: Optional[str] = None) -> Path:
        """
        Create job folder structure with extracted information

        Args:
            job_info: Extracted job information
            job_name: Optional custom job name, otherwise auto-generated

        Returns:
            Path to created job folder
        """
        if not job_name:
            # Auto-generate job name: YYYY-MM-DD_company_role
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            company_clean = re.sub(r'[^\w\s-]', '', job_info.company).replace(' ', '_').lower()
            role_clean = re.sub(r'[^\w\s-]', '', job_info.role).replace(' ', '_').lower()
            job_name = f"{date_str}_{company_clean}_{role_clean}"

        job_dir = self.project_root / "jobs" / job_name
        job_dir.mkdir(parents=True, exist_ok=True)

        # Create generated directory
        (job_dir / "generated").mkdir(exist_ok=True)

        # Create job description markdown
        job_desc_content = self._create_job_description_md(job_info)
        with open(job_dir / "job_description.md", 'w') as f:
            f.write(job_desc_content)

        # Create prompt variables YAML
        prompt_vars_content = self._create_prompt_vars_yaml(job_info)
        with open(job_dir / "prompt_vars.yaml", 'w') as f:
            f.write(prompt_vars_content)

        logger.info(f"Created job folder: {job_dir}")
        return job_dir

    def _create_job_description_md(self, job_info: ExtractedJobInfo) -> str:
        """Create formatted job description markdown"""
        return f"""# Job Description

**Company:** {job_info.company}
**Role:** {job_info.role}
**Location:** {job_info.location}
**Type:** {job_info.job_type}
{f"**Experience Level:** {job_info.experience_level}" if job_info.experience_level else ""}
{f"**Salary Range:** {job_info.salary_range}" if job_info.salary_range else ""}

## Job Description

{job_info.raw_description}

## Key Requirements
{chr(10).join(f"- {req}" for req in job_info.key_requirements)}

## Nice to Have
{chr(10).join(f"- {nice}" for nice in job_info.nice_to_have)}

{f"## Company Culture Notes{chr(10)}{job_info.company_culture}" if job_info.company_culture else ""}

---
*Auto-generated from PDF job posting*
"""

    def _create_prompt_vars_yaml(self, job_info: ExtractedJobInfo) -> str:
        """Create prompt variables YAML with extracted information"""
        prompt_vars = {
            'target_role': job_info.role,
            'company_name': job_info.company,
            'company_culture': 'startup' if any(word in job_info.company_culture.lower()
                                              for word in ['startup', 'fast-paced', 'agile']) else 'enterprise',
            'key_requirements': job_info.key_requirements,
            'nice_to_have': job_info.nice_to_have,
            'emphasis_areas': job_info.key_requirements[:5],  # Top 5 requirements
            'content_preferences': {
                'max_achievements_per_role': 4 if job_info.experience_level.lower() in ['senior', 'executive'] else 3,
                'prioritize_quantified': True,
                'include_patents': True,
                'highlight_recent_roles': True
            },
            'ai_instructions': {
                'tone': 'professional',
                'focus': 'leadership' if any(word in job_info.role.lower()
                                           for word in ['manager', 'lead', 'director']) else 'technical',
                'industry_keywords': []
            }
        }

        return yaml.dump(prompt_vars, default_flow_style=False, sort_keys=False)

    def process_pdf_job_posting(self, pdf_path: Path, job_name: Optional[str] = None) -> Path:
        """
        Complete pipeline: PDF → extracted info → job folder

        Args:
            pdf_path: Path to PDF job posting
            job_name: Optional custom job name

        Returns:
            Path to created job folder
        """
        logger.info(f"Processing PDF job posting: {pdf_path}")

        # Extract text from PDF
        pdf_text = self.extract_text_from_pdf(pdf_path)

        # Use AI to extract structured information
        job_info = self.extract_job_info_with_ai(pdf_text)

        # Create job folder with extracted information
        job_folder = self.create_job_folder(job_info, job_name)

        logger.info(f"Successfully processed PDF job posting → {job_folder}")
        return job_folder

def main():
    """Command line interface for PDF job extraction"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract job information from PDF job postings')
    parser.add_argument('pdf_path', help='Path to PDF job posting')
    parser.add_argument('--job-name', help='Custom job name (auto-generated if not provided)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    try:
        extractor = PDFJobExtractor()

        pdf_path = Path(args.pdf_path)
        if not pdf_path.exists():
            print(f"Error: PDF file not found: {pdf_path}")
            return 1

        job_folder = extractor.process_pdf_job_posting(pdf_path, args.job_name)

        print(f"✅ Successfully processed PDF job posting")
        print(f"📁 Job folder created: {job_folder.name}")
        print(f"📝 Next step: make resume JOB={job_folder.name}")

        return 0

    except Exception as e:
        logger.error(f"PDF processing failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())