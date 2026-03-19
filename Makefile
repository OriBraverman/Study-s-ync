.PHONY: install ingest test run-api run-ui run-all process-outcasts

install:
	pip install -r requirements.txt

ingest:
	python src/retrieval/ingest.py

process-outcasts:
	python src/scraper/outcast_processor.py

test:
	pytest tests/ -v

run-api:
	uvicorn src.api.main:app --reload --port 8000

run-ui:
	streamlit run src/ui/app.py --server.port 8501

run-all:
	uvicorn src.api.main:app --port 8000 &
	streamlit run src/ui/app.py --server.port 8501
