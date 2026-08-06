FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Working defaults so the container boots with zero platform-side configuration
# (e.g. a fresh Railway deploy before any service variables are set) — dev.db is
# already copied into the image above, pre-migrated and pre-seeded with synthetic
# demo data, so no boot-time migration/seed step is needed for this default path.
# Real platform env vars always override these; see README "Running on Railway"
# for what to change before sharing a deployment publicly (SECRET_KEY especially —
# this default is visible to anyone who reads this file).
ENV DATABASE_URL=sqlite:///./dev.db \
    SECRET_KEY=dev-secret-key-not-for-production \
    CORS_ORIGINS=*

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
