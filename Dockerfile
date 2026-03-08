FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ server/
COPY templates/ templates/
COPY schemas/ schemas/

# Firebase config is passed via env vars at deploy time:
#   FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID
# GCP credentials are auto-detected on Cloud Run (no key file needed).

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080"]
