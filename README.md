# QueryMind v2

Deterministic, testable rebuild of QueryMind with clear pipeline contracts.

## Run API

```powershell
python -m uvicorn querymind.main:app --app-dir src --reload --port 8000
```

## Run Local Stack (Docker Compose)

```powershell
docker compose up --build
```

App endpoint: `http://127.0.0.1:8000`

## Health and Readiness

- `GET /health` -> process-level liveness
- `GET /ready` -> mode-aware readiness
- `GET /diagnostics` -> non-secret runtime diagnostics

## Run With Real Elasticsearch Dataset

1. Copy `.env.example` to `.env`.
2. Set these values in `.env`:
	- `MOCK_MODE=false`
	- `ELASTIC_ENDPOINT=https://<your-elasticsearch-host>:9200`
	- `ELASTIC_API_KEY=<your-elastic-api-key>`
	- `GEMINI_API_KEY=<your-gemini-api-key>`
3. Start the app:
	```powershell
	python -m uvicorn querymind.main:app --app-dir src --reload --port 8000
	```
4. Confirm readiness:
	- Open `http://127.0.0.1:8000/ready`
	- Expect `status=ready`
5. Open UI at `http://127.0.0.1:8000/` and run queries.

Note: In live mode, QueryMind translates natural language to ES|QL via Gemini and runs it against your Elasticsearch dataset.

## Run Tests

```powershell
python -m pytest
```

## Run Full Quality Checks

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

This runs:
- Ruff lint checks
- MyPy type checks
- Pytest suite

## Release

Tag a release to trigger `.github/workflows/release.yml`:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

See deployment and secrets details in `docs/DEPLOYMENT.md`.
