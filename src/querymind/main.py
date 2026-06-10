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
                --warn: #f59e0b;
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
                flex-wrap: wrap;
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
            .ghost {
                background: #1f2937;
                color: #e5e7eb;
                border: 1px solid #334155;
            }
            .status { font-weight: 700; }
            .status.ok { color: var(--accent); }
            .status.err { color: var(--danger); }
            .status.warn { color: var(--warn); }
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
            .panel {
                background: #020617;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                margin-top: 12px;
            }
            .mini {
                font-size: 13px;
                color: var(--muted);
            }
            .samples {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            .tabbar {
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }
            .tabbar button.active {
                background: #16a34a;
                color: #052e16;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                border: 1px solid #334155;
                padding: 8px;
                text-align: left;
                font-size: 14px;
            }
            th {
                background: #111827;
                position: sticky;
                top: 0;
            }
            .hidden { display: none; }
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

                <div class=\"panel\">
                    <div><strong>Dataset Mode:</strong> <span id=\"mode\">Loading...</span></div>
                    <div class=\"mini\" id=\"modeDetail\"></div>
                </div>

                <div class=\"panel\">
                    <div><strong>Sample Queries</strong></div>
                    <div class=\"samples\">
                        <button class=\"ghost sample\" data-q=\"Average order value by country\">AOV by country</button>
                        <button class=\"ghost sample\" data-q=\"Top products by revenue\">Top revenue products</button>
                        <button class=\"ghost sample\" data-q=\"Which products have declining reviews over time?\">
                            Declining reviews trend
                        </button>
                        <button class=\"ghost sample\" data-q=\"Most reviewed products\">Most reviewed products</button>
                    </div>
                </div>

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
                        <button id=\"download\" class=\"ghost\">Download CSV</button>
                    </div>
                </div>

                <div class=\"actions\">
                    <span id=\"status\" class=\"status\"></span>
                </div>

                <div class=\"tabbar\">
                    <button id=\"tabTable\" class=\"ghost active\">Table</button>
                    <button id=\"tabJson\" class=\"ghost\">JSON</button>
                </div>

                <div id=\"tablePanel\" class=\"panel\">
                    <div id=\"tableInfo\" class=\"mini\">Run a query to render table.</div>
                    <div style=\"max-height: 420px; overflow: auto;\">
                        <table id=\"resultTable\" class=\"hidden\">
                            <thead id=\"resultHead\"></thead>
                            <tbody id=\"resultBody\"></tbody>
                        </table>
                    </div>
                </div>

                <pre id=\"out\" class=\"hidden\">Response will appear here.</pre>

                <div class=\"panel\">
                    <div><strong>To run on real Elasticsearch dataset</strong></div>
                    <ol class=\"mini\">
                        <li>Set <code>MOCK_MODE=false</code> in your .env.</li>
                        <li>Set <code>ELASTIC_ENDPOINT</code>, <code>ELASTIC_API_KEY</code>, and <code>GEMINI_API_KEY</code>.</li>
                        <li>Restart server and check <code>/ready</code> returns <code>status=ready</code>.</li>
                    </ol>
                </div>
            </div>
        </div>

        <script>
            const runBtn = document.getElementById('run');
            const clearBtn = document.getElementById('clear');
            const downloadBtn = document.getElementById('download');
            const queryEl = document.getElementById('query');
            const maxEl = document.getElementById('max');
            const rawEl = document.getElementById('raw');
            const outEl = document.getElementById('out');
            const statusEl = document.getElementById('status');
            const tableEl = document.getElementById('resultTable');
            const headEl = document.getElementById('resultHead');
            const bodyEl = document.getElementById('resultBody');
            const tableInfoEl = document.getElementById('tableInfo');
            const tabTable = document.getElementById('tabTable');
            const tabJson = document.getElementById('tabJson');
            const tablePanel = document.getElementById('tablePanel');
            const modeEl = document.getElementById('mode');
            const modeDetailEl = document.getElementById('modeDetail');
            const sampleBtns = Array.from(document.querySelectorAll('.sample'));

            let lastRows = [];
            let lastResponse = null;

            function setStatus(text, kind) {
                statusEl.textContent = text;
                statusEl.className = 'status ' + kind;
            }

            function setTab(tab) {
                if (tab === 'table') {
                    tablePanel.classList.remove('hidden');
                    outEl.classList.add('hidden');
                    tabTable.classList.add('active');
                    tabJson.classList.remove('active');
                } else {
                    tablePanel.classList.add('hidden');
                    outEl.classList.remove('hidden');
                    tabJson.classList.add('active');
                    tabTable.classList.remove('active');
                }
            }

            function renderTable(rows) {
                if (!Array.isArray(rows) || rows.length === 0) {
                    tableEl.classList.add('hidden');
                    tableInfoEl.textContent = 'No row data to render as table.';
                    headEl.innerHTML = '';
                    bodyEl.innerHTML = '';
                    return;
                }

                const columns = Array.from(rows.reduce((acc, row) => {
                    Object.keys(row || {}).forEach(k => acc.add(k));
                    return acc;
                }, new Set()));

                headEl.innerHTML = '<tr>' + columns.map(c => `<th>${c}</th>`).join('') + '</tr>';
                bodyEl.innerHTML = rows.map((row) => {
                    const tds = columns.map((c) => `<td>${row[c] ?? ''}</td>`).join('');
                    return `<tr>${tds}</tr>`;
                }).join('');

                tableInfoEl.textContent = `Showing ${rows.length} row(s).`;
                tableEl.classList.remove('hidden');
            }

            function toCsv(rows) {
                if (!Array.isArray(rows) || rows.length === 0) {
                    return '';
                }
                const cols = Array.from(rows.reduce((acc, row) => {
                    Object.keys(row || {}).forEach(k => acc.add(k));
                    return acc;
                }, new Set()));

                const esc = (val) => {
                    const s = String(val ?? '');
                    return '"' + s.replaceAll('"', '""') + '"';
                };

                const lines = [cols.map(esc).join(',')];
                for (const row of rows) {
                    lines.push(cols.map((c) => esc(row[c])).join(','));
                }
                return lines.join('\\n');
            }

            async function loadMode() {
                try {
                    const [diagRes, readyRes] = await Promise.all([
                        fetch('/diagnostics'),
                        fetch('/ready')
                    ]);
                    const d = await diagRes.json();
                    const r = await readyRes.json();

                    if (d.mock_mode) {
                        modeEl.textContent = 'Mock dataset (built-in sample rows)';
                        modeEl.style.color = '#22c55e';
                    } else {
                        modeEl.textContent = 'Live Elasticsearch dataset';
                        modeEl.style.color = '#f59e0b';
                    }

                    modeDetailEl.textContent =
                        `Ready status: ${r.status}. ` +
                        `Elastic key configured: ${d.elastic_configured}. ` +
                        `Gemini key configured: ${d.gemini_configured}.`;
                } catch (err) {
                    modeEl.textContent = 'Unable to load diagnostics';
                    modeEl.style.color = '#ef4444';
                    modeDetailEl.textContent = String(err);
                }
            }

            tabTable.addEventListener('click', () => setTab('table'));
            tabJson.addEventListener('click', () => setTab('json'));

            sampleBtns.forEach((btn) => {
                btn.addEventListener('click', () => {
                    queryEl.value = btn.dataset.q || '';
                });
            });

            runBtn.addEventListener('click', async () => {
                setStatus('Running...', 'ok');
                outEl.textContent = 'Loading...';
                tableInfoEl.textContent = 'Loading...';

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
                    lastResponse = body;
                    lastRows = body.raw_results || [];
                    outEl.textContent = JSON.stringify(body, null, 2);
                    renderTable(lastRows);

                    const kind = res.ok ? (body.status === 'error' ? 'err' : 'ok') : 'err';
                    setStatus('HTTP ' + res.status + (res.ok ? ' OK' : ' Error'), kind);
                } catch (err) {
                    outEl.textContent = String(err);
                    renderTable([]);
                    setStatus('Request failed', 'err');
                }
            });

            clearBtn.addEventListener('click', () => {
                outEl.textContent = 'Response will appear here.';
                renderTable([]);
                lastRows = [];
                lastResponse = null;
                setStatus('', 'ok');
            });

            downloadBtn.addEventListener('click', () => {
                const csv = toCsv(lastRows);
                if (!csv) {
                    setStatus('No rows to export.', 'warn');
                    return;
                }
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'querymind-results.csv';
                a.click();
                URL.revokeObjectURL(url);
                setStatus('CSV downloaded.', 'ok');
            });

            setTab('table');
            loadMode();
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