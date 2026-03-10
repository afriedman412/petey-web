VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: venv install run deploy clean

venv:
	python3 -m venv $(VENV)
	$(PIP) install -e .

install: venv

run: venv
	export FIREBASE_AUTH_DISABLED=1 && $(VENV)/bin/uvicorn server.app:app --reload

deploy:
	gcloud run deploy petey --source . --region=us-east1 --allow-unauthenticated

clean:
	rm -rf $(VENV)
