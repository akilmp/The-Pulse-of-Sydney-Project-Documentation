.PHONY: help data clean features app test report ensure_data_dirs

PYTHON ?= python

help:
@echo "Available targets:"
@echo "  make data     # Fetch raw datasets"
@echo "  make clean    # Run data cleaning tasks"
@echo "  make features # Build feature datasets"
@echo "  make app      # Start the Streamlit dashboard"
@echo "  make test     # Execute automated tests"
@echo "  make report   # Generate project report"

APP_SCRIPT ?= app/streamlit_app.py
REPORT_NOTEBOOK ?= notebooks/05_visual_story.ipynb
REPORT_OUTPUT ?= report/Sydney_Pulse_DataStory.pdf

DATA_FETCH_MODULES = \
src.etl.fetch_transport \
src.etl.fetch_weather \
src.etl.fetch_housing \
src.etl.fetch_abs

CLEANING_MODULES = \
src.cleaning.clean_transport \
src.cleaning.clean_weather \
src.cleaning.clean_housing \
src.cleaning.clean_abs

FEATURE_MODULES = \
src.features.make_geometries \
src.features.engineer_commute_features \
src.features.engineer_weather_features \
src.features.composite_index


data: ensure_data_dirs
	@set -e; \
	for module in $(DATA_FETCH_MODULES); do \
		$(PYTHON) -m $$module; \
	done

clean: ensure_data_dirs
	@set -e; \
	for module in $(CLEANING_MODULES); do \
		$(PYTHON) -m $$module; \
	done

features: ensure_data_dirs
	@set -e; \
	for module in $(FEATURE_MODULES); do \
		$(PYTHON) -m $$module; \
	done

app:
$(PYTHON) -m streamlit run $(APP_SCRIPT)

test:
$(PYTHON) -m pytest

report:
jupyter nbconvert --to pdf $(REPORT_NOTEBOOK) --output $(REPORT_OUTPUT)

ensure_data_dirs:
$(PYTHON) -c "from src.config import Settings; Settings().ensure_directories()"
