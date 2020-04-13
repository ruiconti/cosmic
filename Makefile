.PHONY: run

test:
	pytest tests/ --color=yes --showlocals --tb=short

run:
	export FLASK_APP=src/allocation/entrypoints/app.py
	flask run --host 0.0.0.0 --port 5000