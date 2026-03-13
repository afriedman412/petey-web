VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

BASE_IMAGE = us-east1-docker.pkg.dev/petey-dev/petey/base:latest
VM_INSTANCE = petey-gpu-test
VM_ZONE = us-central1-a

.PHONY: venv install run deploy build-base setup-vm deploy-vm clean

venv:
	python3 -m venv $(VENV)
	$(PIP) install -e .

install: venv

run: venv
	export FIREBASE_AUTH_DISABLED=1 && $(VENV)/bin/uvicorn server.app:app --reload

build-base:
	gcloud config set project petey-dev
	gcloud artifacts repositories create petey --repository-format=docker --location=us-east1 || true
	docker buildx build --platform linux/amd64 -f Dockerfile.base -t $(BASE_IMAGE) --push .

docker-build:
	docker buildx build --platform linux/amd64 -f Dockerfile.base -t $(BASE_IMAGE) --load .
	docker buildx build --platform linux/amd64 -t petey-web --load .

docker-build-local:
	docker build -f Dockerfile.base -t $(BASE_IMAGE) .
	docker build -t petey-web .

docker-run:
	docker run --rm -p 8080:8080 \
		-e FIREBASE_AUTH_DISABLED=1 \
		petey-web

deploy:
	gcloud config set project petey-dev
	gcloud run deploy petey --source . --region=us-central1 --allow-unauthenticated --memory=16Gi --gpu=1 --gpu-type=nvidia-l4 --no-cpu-throttling

setup-vm:
	gcloud compute ssh $(VM_INSTANCE) --zone=$(VM_ZONE) -- \
		'sudo apt-get update && sudo apt-get install -y tesseract-ocr ghostscript python3-pip python3-venv && \
		git clone https://github.com/afriedman412/petey-web.git ~/petey-web 2>/dev/null || true && \
		python3 -m venv ~/petey-web/venv && \
		~/petey-web/venv/bin/pip install torch marker-pdf && \
		cd ~/petey-web && ~/petey-web/venv/bin/pip install -e .'

deploy-vm:
	gcloud compute ssh $(VM_INSTANCE) --zone=$(VM_ZONE) -- \
		'cd ~/petey-web && git pull && \
		venv/bin/pip install -e . && \
		pkill -f "uvicorn server.app" || true && \
		nohup bash -c "set -a && source ~/.env && venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8080" > ~/petey.log 2>&1 &'

clean:
	rm -rf $(VENV)
