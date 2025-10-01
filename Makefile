.DEFAULT_GOAL := help

SOURCE ?= Rocky_Gray_Resume.tex
BASE = $(basename $(SOURCE))
OUTPUT_DIR = docs

LATEXMK_OPTS=-pdf -output-directory=$(OUTPUT_DIR)

serve: ## serve page locally
	go run server.go &

watch-serve: ## watch files and reload on changes
	ls docs/* | entr reload-browser "Google Chrome"

build: $(OUTPUT_DIR)/$(BASE).pdf $(OUTPUT_DIR)/$(BASE)_Compressed.pdf ## Compile the PDF

cover: $(OUTPUT_DIR)/Rocky_Gray_Cover.pdf ## Compile the cover letter

$(OUTPUT_DIR)/Rocky_Gray_Cover.pdf: Rocky_Gray_Cover.tex classes/cover-letter/cover.cls
	TEXINPUTS=./classes//: latexmk -lualatex -output-directory=$(OUTPUT_DIR) -f $(notdir $<) || true

$(OUTPUT_DIR)/$(BASE)_Compressed.pdf: $(OUTPUT_DIR)/$(BASE).pdf
	UNIDOC_LICENSE_API_KEY=$$(find_password UNIDOC_LICENSE_API_KEY) go run compression/main.go $< $@

$(OUTPUT_DIR)/%.pdf: $(SOURCE)
	latexmk $(LATEXMK_OPTS) -f $^ || true

.PHONY: watch
watch: $(SOURCE) ## compile and reload
	latexmk $(LATEXMK_OPTS) -pvc $^

.PHONY: clean
clean : ## remove all TeX-generated files in your local directory
	latexmk -output-directory=$(OUTPUT_DIR) -c
	cd $(OUTPUT_DIR) && $(RM) -f $(BASE).bbl $(BASE).run.xml pdfa.xmpi

infra-init: ## Initialize infrastructure
	cd infrastructure; terraform init

infra-plan: ## See terraform plan
	cd infrastructure; terraform plan

infra-apply: ## Apply terraform
	cd infrastructure; terraform apply

GREEN  := $(shell tput -Txterm setaf 2)
RESET  := $(shell tput -Txterm sgr0)

help: ## print this help message
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "${GREEN}%-20s${RESET}%s\n", $$1, $$NF }' $(MAKEFILE_LIST)
