# Local Setup

## Required Software

- Python 3.11 or newer
- Node.js and npm
- PostgreSQL
- Apache Kafka
- Git

## Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example .env
uvicorn backend.app.main:app --reload
```

## Database

Create the configured database:

```bash
createdb tech_intel
```

The FastAPI app creates tables at startup through SQLAlchemy metadata.

## Kafka

Start Kafka locally and keep `KAFKA_BOOTSTRAP_SERVERS=localhost:9092` unless your broker uses another address.

Run consumers:

```bash
python -m scripts.run_consumers
```

Run ingestors:

```bash
python -m scripts.run_ingestors --limit 25
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://127.0.0.1:8000`.
