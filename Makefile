.DEFAULT_GOAL := help

PDFLATEX = pdflatex -interaction=batchmode -synctex=1
SH = /bin/bash
ASCRIPT = /usr/bin/osascript

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
	#$(RM) -f -- *.out *.bcf *.run.xml *.fls *.aux *.bak *.bbl *.blg *.log *.out *.toc *.tdo _region.* *.fdb_latexmk

GREEN  := $(shell tput -Txterm setaf 2)
RESET  := $(shell tput -Txterm sgr0)

help: ## print this help message
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "${GREEN}%-20s${RESET}%s\n", $$1, $$NF }' $(MAKEFILE_LIST)
