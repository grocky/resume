.DEFAULT_GOAL := help

SOURCE ?= Rocky_Gray_Resume.tex
BASE = "$(basename $(SOURCE))"
OUTPUT_DIR = docs

# Job-specific variables
JOB ?=
JOBS_DIR = jobs

LATEXMK_OPTS=-pdf -output-directory=$(OUTPUT_DIR)

serve: ## 🌐 serve page locally
	go run server.go &

watch-serve: ## 👀 watch files and reload on changes
	ls docs/* | entr reload-browser "Google Chrome"

build: $(OUTPUT_DIR)/$(BASE).pdf ## 📄 compile the PDF

$(OUTPUT_DIR)/%.pdf: $(SOURCE)
	latexmk $(LATEXMK_OPTS) $^

.PHONY: watch
watch: $(SOURCE) ## 🔄 compile and reload
	latexmk $(LATEXMK_OPTS) -pvc $^

.PHONY: clean
clean : ## 🧹 remove all TeX-generated files in your local directory
	latexmk -output-directory=$(OUTPUT_DIR) -c
	cd $(OUTPUT_DIR) && $(RM) -f $(BASE).bbl $(BASE).run.xml pdfa.xmpi

infra-init: ## ☁️ initialize infrastructure
	cd infrastructure; terraform init

infra-plan: ## 📋 see terraform plan
	cd infrastructure; terraform plan

infra-apply: ## 🚀 apply terraform
	cd infrastructure; terraform apply

# Resume generation targets
.PHONY: resume job-init extract-data job-from-pdf resume-from-pdf

resume: ## 📝 generate job-specific resume (example: make resume JOB=2024-01-15_reddit_engineer)
	@if [ -z "$(JOB)" ]; then \
		echo "Error: JOB parameter required. Usage: make resume JOB=YYYY-MM-DD_company_role"; \
		exit 1; \
	fi
	@if [ ! -d "$(JOBS_DIR)/$(JOB)" ]; then \
		echo "Error: Job directory $(JOBS_DIR)/$(JOB) does not exist."; \
		echo "Run 'make job-init JOB=$(JOB)' first."; \
		exit 1; \
	fi
	@echo "Generating resume for job: $(JOB)"
	@echo "Using structured data and modular templates..."
	@if [ ! -d "venv" ]; then \
		echo "Setting up Python virtual environment..."; \
		python3 -m venv venv; \
		venv/bin/pip install -r requirements.txt; \
	fi
	venv/bin/python tools/generate.py --job=$(JOB)
	@if [ -f "$(JOBS_DIR)/$(JOB)/generated/resume.tex" ]; then \
		echo "Compiling LaTeX to PDF..."; \
		latexmk $(LATEXMK_OPTS) -jobname=$(JOB)_resume $(JOBS_DIR)/$(JOB)/generated/resume.tex; \
		echo "Resume generated successfully: docs/$(JOB)_resume.pdf"; \
	else \
		echo "Error: LaTeX file not generated"; \
		exit 1; \
	fi

job-init: ## 📁 initialize new job folder structure manually (example: make job-init JOB=2024-01-15_reddit_engineer)
	@if [ -z "$(JOB)" ]; then \
		echo "Error: JOB parameter required. Usage: make job-init JOB=YYYY-MM-DD_company_role"; \
		exit 1; \
	fi
	@if [ -d "$(JOBS_DIR)/$(JOB)" ]; then \
		echo "Warning: Job directory $(JOBS_DIR)/$(JOB) already exists."; \
	else \
		echo "Creating job folder: $(JOBS_DIR)/$(JOB)"; \
		mkdir -p $(JOBS_DIR)/$(JOB)/generated; \
		cp templates/job_description_template.md $(JOBS_DIR)/$(JOB)/job_description.md; \
		cp templates/prompt_vars_template.yaml $(JOBS_DIR)/$(JOB)/prompt_vars.yaml; \
		echo "Job folder created successfully!"; \
	fi
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit $(JOBS_DIR)/$(JOB)/job_description.md with the job posting"
	@echo "2. Customize $(JOBS_DIR)/$(JOB)/prompt_vars.yaml for this role"
	@echo "3. Run 'make resume JOB=$(JOB)' to generate the resume"

extract-data: ## 📊 extract data from existing resume files (already completed)
	@echo "Data extraction already completed. YAML files are in data/ directory."
	@echo "Files created:"
	@ls -la data/*.yaml | awk '{print "  " $$9}'

job-from-pdf: ## Extract job info from PDF posting (usage: make job-from-pdf PDF=path/to/job.pdf [JOB=custom-name])
	@if [ -z "$(PDF)" ]; then \
		echo "Error: PDF parameter required. Usage: make job-from-pdf PDF=path/to/job.pdf"; \
		exit 1; \
	fi
	@if [ ! -f "$(PDF)" ]; then \
		echo "Error: PDF file not found: $(PDF)"; \
		exit 1; \
	fi
	@echo "🔍 Processing PDF job posting: $(PDF)"
	@if [ ! -d "venv" ]; then \
		echo "Setting up Python virtual environment..."; \
		python3 -m venv venv; \
		venv/bin/pip install -r requirements.txt; \
	fi
	@echo "📄 Extracting job information from PDF using AI..."
	@if [ -n "$(JOB)" ]; then \
		venv/bin/python tools/pdf_job_extractor.py "$(PDF)" --job-name="$(JOB)"; \
	else \
		venv/bin/python tools/pdf_job_extractor.py "$(PDF)"; \
	fi

resume-from-pdf: ## RECOMMENDED: Complete PDF to tailored resume workflow (usage: make resume-from-pdf PDF=path/to/job.pdf)
	@if [ -z "$(PDF)" ]; then \
		echo "Error: PDF parameter required. Usage: make resume-from-pdf PDF=path/to/job.pdf"; \
		exit 1; \
	fi
	@echo "🔄 Complete PDF to Resume Workflow"
	@echo "Step 1: Extracting job information from PDF..."
	@EXTRACTED_JOB=$$(make job-from-pdf PDF="$(PDF)" $(if $(JOB),JOB="$(JOB)",) | grep "Job folder created:" | awk '{print $$5}' | xargs basename); \
	if [ -z "$$EXTRACTED_JOB" ]; then \
		echo "❌ Failed to extract job from PDF"; \
		exit 1; \
	fi; \
	echo "✅ Job extracted: $$EXTRACTED_JOB"; \
	echo "Step 2: Generating tailored resume..."; \
	make resume JOB="$$EXTRACTED_JOB"; \
	echo "🎉 Complete! Resume generated from PDF job posting."

GREEN  := $(shell tput -Txterm setaf 2)
RESET  := $(shell tput -Txterm sgr0)

help: ## 📋 print this help message
	@echo "${GREEN}📄 Agent-Based Resume Framework${RESET}"
	@echo "🚀 Quick Start: ${GREEN}make resume-from-pdf PDF=path/to/job-posting.pdf${RESET}"
	@echo ""
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "${GREEN}%-25s${RESET}%s\n", $$1, $$NF }' $(MAKEFILE_LIST)
