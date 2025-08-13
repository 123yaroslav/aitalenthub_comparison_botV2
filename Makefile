.PHONY: setup scrape index bot api test

VENV?=.venv
PY?=$(VENV)/bin/python
PIP?=$(VENV)/bin/pip

setup:
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

scrape:
	$(PY) -m scraper.main

index:
	$(PY) -m rag.indexer

bot:
	$(PY) -m bot.main

api:
	$(PY) -m api.main

test:
	$(PY) -m pytest -q
