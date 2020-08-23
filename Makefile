.DEFAULT_GOAL := help

SOURCE = Rocky_Gray_Resume.tex
BASE = "$(basename $(SOURCE))"
PUBLIC_DIR = public

LATEXMK_OPTS=-pdf -output-directory=$(PUBLIC_DIR)

build: $(PUBLIC_DIR)/$(BASE).pdf ## Compile the PDF

$(PUBLIC_DIR)/%.pdf: $(SOURCE)
	latexmk $(LATEXMK_OPTS) $^

.PHONY: watch
watch: $(SOURCE) ## compile and reload
	latexmk $(LATEXMK_OPTS) -pvc $^

.PHONY: clean
clean : ## remove all TeX-generated files in your local directory
	latexmk -output-directory=$(PUBLIC_DIR) -c
	$(RM) -f public/$(BASE).bbl public/$(BASE).run.xml public/pdfa.xmpi

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
