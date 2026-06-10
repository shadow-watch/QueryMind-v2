# Deployment and Release Guide

## Local stack with Docker Compose

Start services:

```powershell
docker compose up --build
```

Services:
- App: http://127.0.0.1:8000
- Elasticsearch: http://127.0.0.1:9200

Stop services:

```powershell
docker compose down
```

## Health and readiness endpoints

- `GET /health`: process is up.
- `GET /ready`: app can serve intended mode.
  - In `MOCK_MODE=true`: always `ready`.
  - In `MOCK_MODE=false`: requires `ELASTIC_API_KEY` and `GEMINI_API_KEY`.

## Secrets strategy

Do not commit real secrets.

Use environment variables from runtime/orchestration:
- `ELASTIC_API_KEY`
- `GEMINI_API_KEY`

For CI/CD:
- Store secrets in GitHub repository/environment secrets.
- Inject only at workflow runtime.
- Never print secret values in logs.

## Versioning and release process

Recommended: SemVer tags `vMAJOR.MINOR.PATCH`.

Release flow:
1. Ensure CI is green on main branch.
2. Create and push tag:
   ```powershell
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. `release.yml` runs quality checks, builds Docker image, and creates GitHub release notes.

## Suggested production next hardening

- Use managed secret store (Vault/AWS/GCP/Azure) instead of plain env files.
- Add OpenTelemetry traces with request ID correlation.
- Add rate limiting and authentication in front of `/query`.
