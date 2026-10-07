.PHONY: setup generate-data generate-sample validate init-db ingest dbt-deps dbt-build anomaly-detection reconcile test pipeline pipeline-local clean docker-up docker-down insights

PYTHON ?= python
export PYTHONPATH := .

setup:
	$(PYTHON) -m pip install -r requirements.txt
	@if not exist .env copy /Y .env.example .env

generate-sample:
	$(PYTHON) -m src.data_generation.generate --sample

generate-data:
	$(PYTHON) -m src.data_generation.generate

validate:
	$(PYTHON) -m src.validation.run_validation

init-db:
	$(PYTHON) -m src.ingestion.init_db

ingest:
	$(PYTHON) -m src.ingestion.load_raw --mode full

ingest-incremental:
	$(PYTHON) -m src.ingestion.load_raw --mode incremental

dbt-deps:
	cd dbt && dbt deps || echo "No packages required"

dbt-build:
	cd dbt && dbt run --profiles-dir .

anomaly-detection:
	$(PYTHON) -m src.anomaly_detection.detect

reconcile:
	$(PYTHON) -m src.transformation.reconcile

insights:
	$(PYTHON) scripts/generate_insights.py

dashboard:
	$(PYTHON) scripts/export_dashboard_data.py
	$(PYTHON) scripts/open_dashboard.py

test:
	$(PYTHON) -m pytest tests -v --tb=short

docker-up:
	docker compose up -d postgres
	$(PYTHON) -c "import time; time.sleep(8)"
	$(PYTHON) -m src.ingestion.init_db

docker-down:
	docker compose down

# Preferred when Docker is available
pipeline: generate-sample validate docker-up ingest dbt-build anomaly-detection reconcile insights
	@echo End-to-end Docker pipeline finished.

# Works without Docker (embedded PostgreSQL via pgserver)
pipeline-local:
	$(PYTHON) scripts/run_local_postgres_pipeline.py

clean:
	$(PYTHON) -c "import shutil,pathlib; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('data/source'), pathlib.Path('data/processed'), pathlib.Path('dbt/target'), pathlib.Path('dbt/logs'), pathlib.Path('.pgdata')]]; print('cleaned')"
