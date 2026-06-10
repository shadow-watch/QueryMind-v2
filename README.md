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
