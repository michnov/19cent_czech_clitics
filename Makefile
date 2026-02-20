SHELL=/bin/bash

INPUT_DIR=input_data
OUTPUT_DIR=output_data
TMP_DIR=tmp
VENV_DIR=.venv
LIB_DIR=lib

DATA_NAME=Sušil_prosodie-List1-export-20260220

###################### INSTALL AND SETUP TARGETS ######################

# Python virtual environment targets
.PHONY: venv install-deps clone-udapi clean-venv

# Set up everything: clone udapi + venv + dependencies
setup: clone-udapi venv install-deps

# Clone udapi repository if not present
clone-udapi:
	@echo "Checking for udapi-python..."
	@if [ ! -d "$(LIB_DIR)/udapi-python" ]; then \
		echo "Cloning udapi-python repository..."; \
		mkdir -p $(LIB_DIR); \
		git clone https://github.com/udapi/udapi-python.git $(LIB_DIR)/udapi-python; \
	else \
		echo "udapi-python already exists at $(LIB_DIR)/udapi-python"; \
	fi

# Create virtual environment
venv: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip setuptools wheel

# Install dependencies (requires venv and udapi clone)
install-deps: venv clone-udapi
	@echo "Installing dependencies..."
	$(VENV_DIR)/bin/pip install -r requirements.txt

# Clean virtual environment
clean-venv:
	rm -rf $(VENV_DIR)

########################### DATA PROCESSING TARGETS ###########################

# Data processing targets
sentences : $(TMP_DIR)/01.sentences/$(DATA_NAME).uniq.txt
$(TMP_DIR)/01.sentences/$(DATA_NAME).uniq.txt: $(TMP_DIR)/01.sentences/$(DATA_NAME).txt
	mkdir -p $(TMP_DIR)/01.sentences
	uniq $< > $@
$(TMP_DIR)/01.sentences/%.txt: $(INPUT_DIR)/%.tsv
	mkdir -p $(TMP_DIR)/01.sentences
	cat $< | cut -f2 | tail -n+2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$$//' > $@
	patch $@ < patch/$*.patch

parse: $(TMP_DIR)/02.parsed/$(DATA_NAME).conllu
$(TMP_DIR)/02.parsed/%.conllu: $(TMP_DIR)/01.sentences/%.uniq.txt
	mkdir -p $(TMP_DIR)/02.parsed
	udapy \
		read.Sentences \
		udpipe.Base model=cs online=1 \
		write.Conllu \
		< $< > $@

clean:
	rm -rf $(TMP_DIR)/*

# Clean everything (data + venv)
clean-all: clean clean-venv