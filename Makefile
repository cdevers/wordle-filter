WORDLIST    = wordle/wordle-words.txt
FREQ_FULL   = wordle/wordle-freq-full.txt
ANNOTATOR   = wordle/wordle_freq_annotator.py
SCRIPT      = wordle/wdl-filter
INSTALL_DIR = $(HOME)/bin

.PHONY: help setup install uninstall check clean

help:
	@echo "wordle-filter"
	@echo ""
	@echo "Targets:"
	@echo "  make setup      Download Norvig corpus and build frequency file"
	@echo "  make install    Copy wdl-filter to $(INSTALL_DIR)/"
	@echo "  make uninstall  Remove wdl-filter from $(INSTALL_DIR)/"
	@echo "  make check      Verify Python 3 is available and data files exist"
	@echo "  make clean      Remove generated frequency file"
	@echo ""
	@echo "First time:"
	@echo "  make setup && make install"
	@echo ""
	@echo "Then add to your shell config:"
	@echo "  export WORDLE_WORDLIST=$(WORDLIST)"
	@echo "  export FREQ_FILE=$(FREQ_FULL)"

setup: $(FREQ_FULL)

$(FREQ_FULL): $(WORDLIST) $(ANNOTATOR)
	@echo "Building frequency file (downloads ~30 MB from norvig.com)..."
	python3 $(ANNOTATOR) $(WORDLIST) $(FREQ_FULL)
	@echo "Done: $(FREQ_FULL)"

install: $(SCRIPT)
	@mkdir -p $(INSTALL_DIR)
	cp $(SCRIPT) $(INSTALL_DIR)/wdl-filter
	chmod +x $(INSTALL_DIR)/wdl-filter
	@echo "Installed to $(INSTALL_DIR)/wdl-filter"
	@echo "Make sure $(INSTALL_DIR) is on your PATH."

uninstall:
	rm -f $(INSTALL_DIR)/wdl-filter
	@echo "Removed $(INSTALL_DIR)/wdl-filter"

check:
	@python3 --version || (echo "Error: python3 not found" && exit 1)
	@test -f $(WORDLIST)  || echo "Warning: word list not found at $(WORDLIST)"
	@test -f $(FREQ_FULL) || echo "Warning: frequency file not found — run 'make setup'"
	@test -f $(FREQ_FULL) && echo "OK: $(FREQ_FULL) exists"
	@echo "Check complete."

clean:
	rm -f $(FREQ_FULL)
	@echo "Removed $(FREQ_FULL) — run 'make setup' to regenerate"
