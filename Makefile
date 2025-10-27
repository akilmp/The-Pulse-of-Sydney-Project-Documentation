PYTHON ?= python

.PHONY: data clean test

data:
	$(PYTHON) -m src.etl.fetch_transport
	$(PYTHON) -m src.etl.fetch_weather
	$(PYTHON) -m src.etl.fetch_housing
	$(PYTHON) -m src.etl.fetch_abs

clean:
	$(PYTHON) -m src.cleaning.clean_transport
	$(PYTHON) -m src.cleaning.clean_weather
	$(PYTHON) -m src.cleaning.clean_housing
	$(PYTHON) -m src.cleaning.clean_abs

test:
	pytest -q
