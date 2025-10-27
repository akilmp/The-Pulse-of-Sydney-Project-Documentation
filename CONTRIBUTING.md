# Contributing to The Pulse of Sydney Documentation

Thanks for taking the time to improve this project! These guidelines summarise how to contribute responsibly and consistently.

## Coding Conventions

* **Python style:** follow the Ruff defaults configured in `pyproject.toml` (PEP 8 with import sorting). Use type hints for new functions.
* **Structure:** keep runnable helpers inside `src/pulse/` and prefer pure functions that consume fixtures or clearly documented inputs.
* **Docs:** update the README or narrative sections when the code behaviour or pipeline flow changes.

## Testing Requirements

* Run `make data` to stage cached fixtures before executing code that depends on external data.
* Execute `pytest` (or `make test`) to ensure ETL, feature engineering, and SCHI helpers continue to work with the fixtures.
* Optional static analysis: `make lint` (Ruff) is encouraged locally; the CI workflow runs it in non-blocking mode.

## Data Privacy & Ethics

* Do **not** commit personal commute logs or third-party data that is not redistributable. Use anonymised or synthetic fixtures when sharing examples.
* Keep secrets and API keys out of version control—reference `.env.example` or document configuration variables instead.
* When adding datasets or notebooks, document provenance and licence terms in the README or dedicated data registry files.

Following these expectations keeps the project reproducible, respectful of privacy, and easy for others to review. Thank you!
