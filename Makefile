.PHONY: help data clean features app test report

PYTHON ?= python

help:
	@echo "Available targets:"
	@echo "  make data     # Fetch raw datasets"
	@echo "  make clean    # Run data cleaning tasks"
	@echo "  make features # Build feature datasets"
	@echo "  make app      # Start the Streamlit dashboard"
	@echo "  make test     # Execute automated tests"
	@echo "  make report   # Generate project report"

DATA_SCRIPT ?= src/etl
CLEANING_SCRIPT ?= src/cleaning
FEATURE_SCRIPT ?= src/features
APP_SCRIPT ?= app/streamlit_app.py


data:
	@echo "TODO: Implement data fetching pipelines in $${DATA_SCRIPT}"

clean:
	@echo "TODO: Implement cleaning steps in $${CLEANING_SCRIPT}"

features:
	$(PYTHON) -m src.features.make_geometries
	$(PYTHON) -m src.features.engineer_commute_features
	$(PYTHON) -m src.features.engineer_weather_features
	$(PYTHON) -m src.features.composite_index

app:
	$(PYTHON) -m streamlit run $(APP_SCRIPT)

test:
	$(PYTHON) -m pytest

report:
	@echo "TODO: Generate analytical report"
