.DEFAULT_GOAL := help

SOURCE = Rocky_Gray_Resume.tex
BASE = "$(basename $(SOURCE))"

build: $(BASE).pdf ## Compile the PDF

%.pdf: $(SOURCE)
	latexmk -pdf $^

.PHONY: watch
watch: ## compile and reload
	latexmk -pdf -pvc $(SOURCE)

.PHONY: clean
clean : ## remove all TeX-generated files in your local directory
	latexmk -c
	$(RM) -f $(BASE)*.jpg $(BASE).bbl $(BASE).run.xml pdfa.xmpi

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
