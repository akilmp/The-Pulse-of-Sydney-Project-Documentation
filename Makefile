.PHONY: data clean features test lint

DATA_FIXTURE=data/fixtures/transport_sample.csv
RAW_COPY=data/raw/transport_sample.csv
PROCESSED_MANIFEST=data/processed/features_manifest.json

## make data: populate cached raw data from fixtures
data:
	@echo "Copying cached fixtures into data/raw"
	@mkdir -p data/raw
	@cp $(DATA_FIXTURE) $(RAW_COPY)

## make clean: remove processed artefacts but keep fixtures
clean:
	@echo "Cleaning processed artefacts"
	@rm -f data/raw/transport_sample.csv
	@find data/interim -type f ! -name '.gitkeep' -delete
	@find data/processed -type f ! -name '.gitkeep' -delete

## make features: derive processed artefacts using cached raw data
features: data
	@echo "Generating processed features manifest"
	@mkdir -p data/processed
	@printf '{\n  "source": "data/raw/transport_sample.csv",\n  "records": 3,\n  "description": "Synthetic features for CI"\n}\n' > $(PROCESSED_MANIFEST)

## make test: run pytest suite
test:
	pytest

## make lint: run optional Ruff checks
lint:
	ruff check src tests
