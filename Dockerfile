FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md pytest.ini .env.example ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn httpx pydantic pydantic-settings python-dotenv pytest pytest-asyncio ruff mypy

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "querymind.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
