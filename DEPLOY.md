# Deploying the Capacity-Planning Copilot

This app is a single FastAPI service: it serves the `/ask` API **and** the chat UI
(`static/index.html`) from one process, so you only need to deploy one thing.

## What's included
- `Dockerfile` — builds and runs the app anywhere that supports containers
- `Procfile` — for buildpack-based hosts (Railway/Render/Heroku-style, no Docker needed)
- `railway.json` — explicit Railway config (optional, Railway also auto-detects the Dockerfile)

## Local test run
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
PYTHONPATH=src uvicorn capacity_copilot.api.main:app --reload
```
Visit http://localhost:8000 — chat UI is there. `/health` and `/metrics` are also live.

## Option A — Railway (fastest, recommended)
1. Push this repo to GitHub.
2. https://railway.app → New Project → Deploy from GitHub repo.
3. Railway detects the `Dockerfile` automatically and builds it.
4. In the project's **Variables** tab, add `ANTHROPIC_API_KEY`.
5. Railway gives you a public `*.up.railway.app` URL as soon as the build finishes — that's live.
6. (Optional) Settings → Networking → add a custom domain.

## Option B — Render
1. https://render.com → New → Web Service → connect your GitHub repo.
2. Render auto-detects the Dockerfile (or use the Procfile with the Python native runtime).
3. Add environment variable `ANTHROPIC_API_KEY` in the dashboard.
4. Deploy — Render gives you a `*.onrender.com` URL.

## Option C — Fly.io
```bash
fly launch          # detects the Dockerfile, asks a few questions
fly secrets set ANTHROPIC_API_KEY=sk-ant-...
fly deploy
```

## Production hardening (added after audit)

This app went through a bug/security pass. What changed and why:

| Issue found | Fix |
|---|---|
| A single `/ask` with 50k tests took **151 seconds** — would be killed by any host's request timeout | Input bounds (`parser.py`): test_count/rack_count/license_seats/deadline are clamped to safe ranges; response tells the user what was clamped via a `notes` field. Confirmed: same "huge input" case now returns in ~8s. |
| `rack_count=0` or `license_seats=0` crashed SimPy immediately (`ValueError: capacity must be > 0`) | Same clamping — minimums enforced at parse time, before any simulation runs. |
| Any Anthropic API error (timeout, rate limit, outage) crashed the request with a raw stack trace | `reasoner.py` now catches SDK exceptions and raises a clean `ReasonerError`; `/ask` catches that and still returns the grounded simulation numbers with a plain-English note, instead of a 500. |
| Missing `ANTHROPIC_API_KEY` raised `KeyError` on first call | Checked explicitly with a clear message; also exposed via `GET /ready`. |
| Any unhandled exception would leak a Python stack trace to the client | Global exception handler returns a generic `{"detail": "Internal server error."}` and logs the real error server-side. |
| No request size limit on `query` | `AskRequest.query` capped to 1000 chars (422 on violation). |
| Nondeterministic rack-type selection (Python set iteration order isn't guaranteed stable) | Sorted before selection — matters once multi-rack-type scenarios reach the live API. |
| Anyone could call `/ask` and spend your Anthropic budget | Optional `COPILOT_API_KEY` env var — if set, requests need header `X-API-Key: <value>`. Unset by default so the public demo still works. |
| Container ran as root | Dockerfile now creates and runs as a non-root `appuser`. |
| No container healthcheck | Added `HEALTHCHECK` hitting `/health`. |
| Loose `>=` dependency versions | Pinned to exact tested versions in `requirements.txt`. |

**New environment variables (both optional):**
- `COPILOT_API_KEY` — if set, `/ask` requires header `X-API-Key: <value>`
- `CORS_ALLOW_ORIGINS` — comma-separated origins; defaults to `*` (fine for the bundled same-origin chat UI; tighten if you build a separate frontend)

**New endpoints:**
- `GET /ready` — readiness probe, also reports whether `ANTHROPIC_API_KEY` is configured

**Still worth knowing before going fully public:**
- No rate limiting yet beyond the platform's own defaults — if you expect real public traffic, add a rate limiter (e.g. `slowapi`) or front it with your host's rate-limiting feature.
- `test_count` is capped at 10,000 for the live synchronous API (keeps `/ask` under ~10s). Larger campaigns should go through `scripts/run_validation.py`-style batch scenarios, not the chat UI.
- See `LIMITATIONS.md` for scope limitations (single-suite queries only, no backlog modeling, etc.) — these are unchanged by this hardening pass.


## Other notes

- **Never commit your real `.env`** — only `.env.example` is checked in. Set the key via
  the host's dashboard/CLI secrets, as shown above.
- **Metrics:** Prometheus metrics are exposed at `/metrics` on the same service — point a
  Grafana Cloud or self-hosted Prometheus scraper at `<your-url>/metrics` for dashboards.
- The live API runs the full domain-model simulation (`engine_v2`/`sensitivity_v2`), the
  same pipeline validated in `VALIDATION_REPORT.md` (13/13 known-answer scenarios) — not a
  simplified stand-in. See `LIMITATIONS.md` for what's still out of scope (multi-suite
  queries via chat, priority-preemption as a distinct diagnosis, backlog modeling).

