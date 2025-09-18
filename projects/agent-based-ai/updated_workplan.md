# Agent-Based Dynamic Resume Framework - Updated Work Plan

## Project Overview
Create an intelligent system that automatically generates job-specific resumes by analyzing job descriptions and tailoring Rocky Gray's professional background using AI-assisted content rewriting. The system will use the existing AltaCV-based template as the foundation while making it modular and data-driven.

## Quick Start for AI Agent
This work plan is designed for systematic implementation, building incrementally from data extraction to full AI-powered resume customization. Each phase includes specific deliverables and validation criteria.

## Phase 1: Data Extraction & Repository Setup (Days 1-3)

### 1.1 Repository Structure Enhancement
Extend the existing structure with new directories:
```
resume-agent/
├── data/
│   ├── personal.yaml         # Basic info, contact details
│   ├── background.yaml       # Role summaries, company info
│   ├── achievements.yaml     # Quantified accomplishments by company
│   ├── skills.yaml          # Technical and soft skills
│   └── templates/           # Template variants
├── jobs/                    # Job-specific configurations
│   └── YYYY-MM-DD_company_role/
│       ├── job_description.md
│       ├── prompt_vars.yaml
│       └── generated/
├── tools/
│   ├── extract.py          # Data extraction from existing resume
│   ├── generate.py         # Resume generation engine
│   └── ai_client.py        # External AI API integration
├── templates/
│   ├── base_resume.tex     # Modular version of Rocky_Gray_Resume.tex
│   └── sections/           # Individual section templates
└── config/
    ├── api_keys.yaml       # API configuration (gitignored)
    └── settings.yaml       # Global settings
```

### 1.2 Data Extraction Tool
Build `tools/extract.py` to parse existing `Rocky_Gray_Resume.tex`:
- Extract personal information (name, contact, tagline)
- Parse experience sections into structured data
- Identify skills/tags from each role
- Export to YAML format with proper categorization
- Handle the second document you'll provide

### 1.3 Enhanced Makefile Integration
Add new targets to existing Makefile:
```makefile
# New resume generation targets
resume: ## Generate job-specific resume (usage: make resume JOB=2024-01-15_reddit_engineer)
job-init: ## Initialize new job folder structure
ai-generate: ## Generate AI-tailored content for job
extract-data: ## Extract data from existing resume files
```

## Phase 2: Template Modularization (Days 4-6)

### 2.1 AltaCV Template Breakdown
Convert `Rocky_Gray_Resume.tex` into modular components:
- `templates/base_resume.tex` - Main document structure with Jinja2 placeholders
- `templates/sections/header.tex` - Personal info and photo
- `templates/sections/experience.tex` - Job entries with dynamic bullet points
- `templates/sections/sidebar.tex` - Skills, education, certifications, patents
- Preserve existing color scheme and styling

### 2.2 YAML Schema Design
Define structured schemas for:
```yaml
# personal.yaml
name: "Rocky Gray"
tagline: "Software Engineering Leader"
contact:
  location: "Washington D.C Metro Area"
  email: "rocky.grayjr@gmail.com"
  # ... etc

# background.yaml
roles:
  - company: "Reddit"
    title: "Engineering Manager"
    duration: "Dec 2024 --- Oct 2025"
    location: "Remote --- San Francisco, CA"
    summary: "Led the Ads API Platform and Business Engineering teams"
    key_themes: ["Leadership", "API Platform", "Data Engineering"]

# achievements.yaml
by_company:
  Reddit:
    - achievement: "Led the Ads API Platform and Business Engineering teams"
      impact: "driving partner integrations, platform reliability"
      quantified: true
      keywords: ["leadership", "api", "platform"]
```

### 2.3 Jinja2 Template Engine
Implement template rendering with:
- Dynamic content selection based on job requirements
- Conditional section inclusion
- Bullet point prioritization and ordering
- Tag/skill filtering and highlighting

## Phase 3: Basic Generation Pipeline (Days 7-10)

### 3.1 Core Generation Engine (`tools/generate.py`)
- YAML data loading and validation
- Jinja2-based template rendering
- Basic content filtering (skills, achievements)
- LaTeX compilation integration
- Error handling and logging

### 3.2 Job Configuration System
For each job in `jobs/YYYY-MM-DD_company_role/`:
- `job_description.md` - Raw job posting
- `prompt_vars.yaml` - Job-specific customization parameters
```yaml
target_role: "Senior Software Engineer"
key_requirements: ["Python", "API design", "Leadership"]
company_culture: "startup"
emphasis_areas: ["technical leadership", "scalability"]
```

### 3.3 Enhanced Makefile Targets
```makefile
resume: $(jobs_dir)/$(JOB)/generated/resume.pdf

$(jobs_dir)/$(JOB)/generated/resume.pdf: $(data_files)
	python tools/generate.py --job=$(JOB) --output=$@

job-init:
	mkdir -p jobs/$(JOB)/generated
	touch jobs/$(JOB)/job_description.md
	cp templates/prompt_vars_template.yaml jobs/$(JOB)/prompt_vars.yaml
```

## Phase 4: AI Integration Layer (Days 11-15)

### 4.1 AI Client Implementation (`tools/ai_client.py`)
- Support for OpenAI, Anthropic, and other APIs
- Configurable API key management
- Rate limiting and error handling
- Prompt template management
- Response parsing and validation

### 4.2 Job Description Analysis
AI-powered analysis to:
- Extract key requirements and nice-to-haves
- Identify industry-specific keywords
- Categorize requirements (technical, leadership, domain)
- Generate relevance scores for existing achievements
- Suggest content emphasis areas

### 4.3 Content Rewriting Engine
AI-assisted content generation:
- Rewrite achievement bullets to match job language
- Optimize for ATS keyword matching
- Maintain authenticity while enhancing relevance
- Generate job-specific summary/tagline variations
- Suggest skill prioritization and grouping

### 4.4 Meta-Prompt System
Design comprehensive prompts for:
```
Job Analysis Prompt:
"Analyze this job description and extract..."

Achievement Rewriting Prompt:
"Given this achievement and job requirements, rewrite to emphasize..."

Skill Prioritization Prompt:
"From this skill list, prioritize and group for this role..."
```

## Phase 5: Advanced Generation Features (Days 16-18)

### 5.1 Multi-Pass Generation
1. **Analysis Pass**: Job description → requirements extraction
2. **Selection Pass**: Achievement filtering and prioritization
3. **Rewriting Pass**: AI-enhanced content generation
4. **Compilation Pass**: LaTeX generation and PDF build
5. **Validation Pass**: Quality checks and formatting verification

### 5.2 Dynamic Content Selection
- Achievement relevance scoring
- Automatic bullet point prioritization
- Skill section reordering based on job requirements
- Section emphasis adjustment (technical vs leadership)
- Length optimization for single-page constraint

### 5.3 Quality Assurance Tools
- Content authenticity validation
- ATS-friendly formatting checks
- LaTeX compilation error handling
- Generated content review prompts
- Consistency checks across versions

## Phase 6: Workflow Automation (Days 19-21)

### 6.1 Complete Make Integration
```makefile
.PHONY: resume job-init extract-data ai-generate

resume: ai-generate $(OUTPUT_DIR)/$(JOB)_resume.pdf

$(OUTPUT_DIR)/$(JOB)_resume.pdf: jobs/$(JOB)/generated/resume.tex
	latexmk $(LATEXMK_OPTS) -jobname=$(JOB)_resume $<

ai-generate: jobs/$(JOB)/generated/resume.tex

jobs/$(JOB)/generated/resume.tex: $(data_files) jobs/$(JOB)/job_description.md
	python tools/generate.py --job=$(JOB) --ai-enhance --output=$@

job-init:
	@echo "Creating job folder: jobs/$(JOB)"
	mkdir -p jobs/$(JOB)/generated
	cp templates/job_description_template.md jobs/$(JOB)/job_description.md
	cp templates/prompt_vars_template.yaml jobs/$(JOB)/prompt_vars.yaml
	@echo "Job folder created. Edit jobs/$(JOB)/job_description.md and run 'make resume JOB=$(JOB)'"

extract-data:
	python tools/extract.py --source=Rocky_Gray_Resume.tex --output=data/
```

### 6.2 Configuration Management
- API key configuration with environment variable fallback
- Global settings for AI model preferences
- Template variant selection
- Output format options (PDF, LaTeX source)

### 6.3 Error Handling & Logging
- Comprehensive error reporting
- AI API failure fallbacks
- LaTeX compilation debugging
- Generation progress tracking

## Phase 7: Advanced Features & Polish (Days 22-25)

### 7.1 Multi-Format Output
- PDF generation (primary)
- HTML version for online portfolios
- Plain text for ATS systems
- JSON structured data export

### 7.2 Template Variations
- Industry-specific formatting adjustments
- Company culture adaptations (conservative vs startup)
- Role-specific emphasis (technical vs management)
- Color scheme variations

### 7.3 Analytics & Optimization
- Track which achievements work best for different roles
- A/B test content variations
- Success metrics integration (if available)
- Performance optimization recommendations

### 7.4 Documentation & Examples
- Complete usage documentation
- Example job configurations
- Troubleshooting guide
- Best practices for data maintenance

## Success Metrics

- **Generation Speed**: <60 seconds from job description to tailored PDF
- **Relevance Score**: >90% keyword alignment with job requirements
- **Quality Consistency**: Zero LaTeX compilation errors
- **Content Authenticity**: AI-generated content maintains professional accuracy
- **Customization Depth**: 5-8 tailored achievements per role with job-specific language

## Technology Stack

- **Core**: Python 3.8+, LaTeX (AltaCV), YAML, Jinja2
- **AI Integration**: OpenAI API, Anthropic API (configurable)
- **Build System**: Enhanced Makefile with new targets
- **Template Engine**: Jinja2 with custom filters
- **Validation**: PyYAML, LaTeX syntax checking

## Risk Mitigation

- **API Costs**: Implement request caching and content reuse
- **AI Hallucination**: Strict validation against original data
- **LaTeX Dependencies**: Maintain existing compilation pipeline
- **Data Privacy**: Local processing, encrypted API key storage
- **Template Maintenance**: Version control for template evolution

## Implementation Validation

After each phase:
1. Test with sample job description
2. Validate generated LaTeX compiles successfully
3. Verify output maintains professional quality
4. Check ATS-friendly formatting
5. Review AI-generated content for accuracy

## Deliverables

1. Complete data extraction from existing resume
2. Modular AltaCV template system
3. AI-powered content generation pipeline
4. Enhanced Makefile with `make resume JOB=company-role-date`
5. Comprehensive documentation and examples
6. Quality assurance and validation tools

This plan builds incrementally from your existing professional setup while adding intelligent customization capabilities that will make each resume highly targeted to specific opportunities.