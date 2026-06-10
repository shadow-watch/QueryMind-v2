import logging

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from querymind.core.logging import configure_logging
from querymind.core.middleware import attach_request_id_filter, request_context_middleware
from querymind.core.settings import settings
from querymind.domain.contracts import QueryRequest, QueryResponse
from querymind.services.pipeline import PipelineService

configure_logging()
attach_request_id_filter()
logger = logging.getLogger("querymind.app")

app = FastAPI(title=settings.app_name)
app.middleware("http")(request_context_middleware)
pipeline = PipelineService()


UI_HTML = """
<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
        <title>QueryMind v2 UI</title>
        <style>
            :root {
                --bg: #0f172a;
                --panel: #111827;
                --text: #e5e7eb;
                --muted: #9ca3af;
                --accent: #22c55e;
                --danger: #ef4444;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                font-family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif;
                background: radial-gradient(circle at top, #1f2937, var(--bg));
                color: var(--text);
            }
            .wrap {
                max-width: 980px;
                margin: 40px auto;
                padding: 0 16px;
            }
            .card {
                background: linear-gradient(180deg, #111827, #0b1220);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 18px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
            }
            h1 { margin: 0 0 8px 0; font-size: 28px; }
            p { color: var(--muted); margin: 0 0 16px 0; }
            label { display: block; margin-bottom: 8px; font-weight: 600; }
            textarea, input[type=number] {
                width: 100%;
                background: #0b1220;
                border: 1px solid #334155;
                color: var(--text);
                border-radius: 8px;
                padding: 10px;
            }
            textarea { min-height: 88px; resize: vertical; }
            .row {
                display: grid;
                grid-template-columns: 1fr 180px 160px;
                gap: 12px;
                margin-top: 12px;
            }
            .actions {
                margin-top: 14px;
                display: flex;
                gap: 10px;
                align-items: center;
            }
            button {
                background: var(--accent);
                color: #052e16;
                border: 0;
                border-radius: 8px;
                padding: 10px 14px;
                font-weight: 700;
                cursor: pointer;
            }
            .secondary {
                background: #334155;
                color: #e5e7eb;
            }
            .status { font-weight: 700; }
            .status.ok { color: var(--accent); }
            .status.err { color: var(--danger); }
            pre {
                background: #020617;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                white-space: pre-wrap;
                word-break: break-word;
                margin-top: 14px;
                max-height: 420px;
                overflow: auto;
            }
            @media (max-width: 760px) {
                .row { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class=\"wrap\">
            <div class=\"card\">
                <h1>QueryMind v2</h1>
                <p>Run natural language analytics queries and inspect the API response.</p>

                <label for=\"query\">Query</label>
                <textarea id=\"query\">Average order value by country</textarea>

                <div class=\"row\">
                    <div>
                        <label for=\"max\">Max results</label>
                        <input id=\"max\" type=\"number\" min=\"1\" max=\"100\" value=\"10\" />
                    </div>
                    <div>
                        <label for=\"raw\">Include raw</label>
                        <input id=\"raw\" type=\"checkbox\" checked />
                    </div>
                    <div class=\"actions\">
                        <button id=\"run\">Run Query</button>
                        <button id=\"clear\" class=\"secondary\">Clear</button>
                    </div>
                </div>

                <div class=\"actions\">
                    <span id=\"status\" class=\"status\"></span>
                </div>

                <pre id=\"out\">Response will appear here.</pre>
            </div>
        </div>

        <script>
            const runBtn = document.getElementById('run');
            const clearBtn = document.getElementById('clear');
            const queryEl = document.getElementById('query');
            const maxEl = document.getElementById('max');
            const rawEl = document.getElementById('raw');
            const outEl = document.getElementById('out');
            const statusEl = document.getElementById('status');

            function setStatus(text, ok) {
                statusEl.textContent = text;
                statusEl.className = 'status ' + (ok ? 'ok' : 'err');
            }

            runBtn.addEventListener('click', async () => {
                setStatus('Running...', true);
                outEl.textContent = 'Loading...';

                const payload = {
                    query: queryEl.value,
                    include_raw: rawEl.checked,
                    max_results: Number(maxEl.value || 10)
                };

                try {
                    const res = await fetch('/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const body = await res.json();
                    outEl.textContent = JSON.stringify(body, null, 2);
                    setStatus('HTTP ' + res.status + (res.ok ? ' OK' : ' Error'), res.ok);
                } catch (err) {
                    outEl.textContent = String(err);
                    setStatus('Request failed', false);
                }
            });

            clearBtn.addEventListener('click', () => {
                outEl.textContent = 'Response will appear here.';
                setStatus('', true);
            });
        </script>
    </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def ui() -> str:
        return UI_HTML


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env, "mock_mode": str(settings.mock_mode).lower()}


@app.get("/ready")
async def ready() -> dict[str, object]:
    checks = {
        "mock_mode": settings.mock_mode,
        "elastic_key_configured": bool(settings.elastic_api_key),
        "gemini_key_configured": bool(settings.gemini_api_key),
    }

    if settings.mock_mode:
        return {"status": "ready", "checks": checks}

    live_ready = checks["elastic_key_configured"] and checks["gemini_key_configured"]
    if live_ready:
        return {"status": "ready", "checks": checks}
    return {"status": "not_ready", "checks": checks}


@app.get("/diagnostics")
async def diagnostics() -> dict[str, object]:
    return {
        "app_name": settings.app_name,
        "env": settings.app_env,
        "mock_mode": settings.mock_mode,
        "gemini_model": settings.gemini_model,
        "query_timeout_ms": settings.query_timeout_ms,
        "max_results_limit": settings.max_results_limit,
        "elastic_configured": bool(settings.elastic_api_key),
        "gemini_configured": bool(settings.gemini_api_key),
    }


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    response = pipeline.run(request)
    logger.info(
        "query_processed status=%s query_type=%s",
        response.status.value,
        response.query_type.value,
        extra={"request_id": "-"},
    )
    return response