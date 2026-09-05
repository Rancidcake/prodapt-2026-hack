# KT — MyLesson.ai (Engineering Handoff)

Written for anyone picking this up cold. Covers what's actually built and running today (not what the design docs describe), how it fits together, and concrete next steps for the two biggest missing pieces: the database and RAG/ingestion.

Read this alongside `README.md` (product framing + design decisions), `BRD.md`/`SRS.md`/`HLD.md` (target design). **This doc is the "as-built" reality check** — where it diverges from those, that's called out explicitly rather than silently.

---

## 1. What's actually working right now

A real, end-to-end vertical slice with **no database and no RAG yet**:

```
Streamlit (frontend/app.py)
      │  HTTP
      ▼
FastAPI (backend/app/main.py)
      │
      ▼
Orchestrator (services/generation/orchestrator.py)  ── dispatches by task_type
      │
      ▼
Prompt module (llm/prompts/*.py)  ── builds system + user text + JSON schema
      │
      ▼
client.py (llm/client.py)  ── provider dispatch, reads LLM_PROVIDER env var
      │
      ├──► providers/anthropic_provider.py  (Anthropic SDK)
      └──► providers/gemini_provider.py     (raw REST to generateContent)
      │
      ▼
Real model, real structured JSON back
```

Verified live (not just claimed): lesson-plan generation returns real, correctly-shaped content with objectives properly tagged into sections. Quiz generation's schema was also validated against the real API.

**What's missing from this loop:** nothing persists. Every `/generate/*` call is stateless — `chunks=[]` is hardcoded (no retrieval happens), there's no database, and closing the browser tab loses everything. That's next (§5, §6).

---

## 2. Repository map

```
.
├── .env                          # secrets + provider config (gitignored)
├── run_everything.py             # one-click dev runner — see §3
├── README.md / BRD.md / SRS.md / HLD.md   # design docs (target state, not as-built)
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI app, 2 endpoints: /generate/lesson-plan, /generate/quiz
│       ├── schemas/generation.py # request/response Pydantic models
│       ├── services/generation/orchestrator.py   # task_type → prompt module dispatch
│       └── llm/
│           ├── client.py         # provider dispatch (reads LLM_PROVIDER)
│           ├── errors.py         # shared exception types, all providers raise these
│           ├── pii_guard.py       # regex PII scrub, runs before every prompt
│           ├── providers/
│           │   ├── anthropic_provider.py
│           │   └── gemini_provider.py
│           └── prompts/          # one file per task_type — see §4
│               ├── shared.py             # grounding wrapper, teaching-context formatter
│               ├── lesson_plan.py
│               ├── quiz.py
│               ├── material.py
│               ├── explanation.py
│               ├── activity.py
│               └── section_regenerate.py
└── frontend/
    ├── requirements.txt
    ├── api_client.py             # thin HTTP wrapper over the backend
    └── app.py                    # single-page Streamlit UI
```

**Not present yet:** no `alembic/`, no `models/` (DB), no `services/ingestion/`, no `services/retrieval/`, no `services/export/`, no auth, no tests. All named in HLD/README as target structure — none built.

---

## 3. How to run it

```bash
# fill in .env first: ANTHROPIC_API_KEY and/or GEMINI_API_KEY, LLM_PROVIDER
python run_everything.py
```

This creates a **single shared** `.venv` at repo root (not per-component, unlike what the README's manual setup describes — this is a dev-convenience shortcut), installs both `backend/requirements.txt` and `frontend/requirements.txt` into it, starts FastAPI with `--reload` on `:8000`, waits for `/health`, then starts Streamlit on `:8501`. Ctrl+C stops both.

Env vars that matter (`.env`):

| Var | Purpose |
|---|---|
| `LLM_PROVIDER` | `anthropic` or `gemini` — selects which `providers/*.py` backend `client.py` loads |
| `ANTHROPIC_API_KEY` | Required if `LLM_PROVIDER=anthropic` |
| `GEMINI_API_KEY` | Required if `LLM_PROVIDER=gemini` |
| `LLM_MODEL_PRIMARY` | Model ID — see §4 for per-provider gotchas |
| `API_BASE_URL` | Read by the frontend to find the backend; defaults to `localhost:8000` |

---

## 4. The provider abstraction (Decision 9, made real)

`client.py` is a **dispatcher, not an implementation** — it re-exports the shared exception types from `errors.py` and imports exactly one of the two provider backends based on `LLM_PROVIDER`. Prompts and the orchestrator never import a provider directly.

| | Anthropic | Gemini |
|---|---|---|
| Transport | Official `anthropic` SDK | Raw REST (`requests`) to `generateContent` — no SDK |
| Structured output | `output_config.format` (json_schema) | `generationConfig.responseSchema` |
| **Gotcha** | `thinking: adaptive` + `effort` only work on the 4.6+ tier — Haiku 4.5 400s if you send them. `_supports_adaptive_thinking()` in `anthropic_provider.py` gates this by model prefix. | `responseSchema` **rejects `additionalProperties`** outright (400) — stripped recursively in `gemini_provider.py`'s `_strip_unsupported_keys()` before every request, since our schemas set it everywhere for Anthropic's benefit. |
| Cost lever | Model choice only | `thinkingConfig: {thinkingBudget: 0}` — this model line does hidden reasoning by default and bills it as tokens even for trivial output (measured: 131 total tokens to say "Hello", 120 of them invisible thinking). Set to 0 unconditionally in the Gemini backend. |

**Known live issue as of this KT:** `gemini-flash-latest` (currently resolving to `gemini-3.8-flash`) is intermittently returning "high demand" 503-style errors under the free tier — likely a brand-new model getting hammered. `gemini-2.5-flash` is fully deprecated for new users (404, Google's error message points at `gemini-3.6-flash` and "the Interactions API" instead). If demo-day reliability is a concern, **the fastest mitigation is flipping `LLM_PROVIDER=anthropic` in `.env`** (assuming that account has credits) rather than fighting model-alias contention — the whole point of this abstraction is that the swap is one env var, not a code change.

To add a third provider: create `providers/<name>.py` exposing the same `generate(*, system, user_content, output_schema, task_type, prompt_version, effort, max_tokens) -> GenerationResult` signature, raising only the exception types from `errors.py`, then add one `elif` branch in `client.py`.

---

## 5. Prompt catalog

| `task_type` | Module | Critical constraint |
|---|---|---|
| `lesson_plan` | `lesson_plan.py` | Every section must list which `objective_ids` it covers |
| `quiz` | `quiz.py` | **The important one** — every question must carry an `objective_id` from the input list (never invented), and uncovered objectives go in `uncovered_objective_ids` rather than forcing a weak question. This is what makes objective-coverage reporting real. |
| `material` | `material.py` | Handout/summary/slide-outline/worksheet, matched to reading level |
| `explanation` | `explanation.py` | Must include analogies + explicit common misconceptions, not just the correct explanation |
| `activity` | `activity.py` | Scaled to class size + available resources; no grounding (no source material involved) |
| `section_regenerate` | `section_regenerate.py` | Edit-in-place; must not contradict neighboring sections given as context |

All of them (except `activity`) route retrieved chunks through `shared.wrap_reference_material()`, which delimits them as `<reference_material>` and explicitly frames anything inside as data, never instructions (prompt-injection defense). Right now every call site passes `chunks=[]`, so every artifact comes back `is_grounded: false` — that flips automatically once retrieval is wired in (§7), no prompt changes needed.

---

## 6. PII handling

`pii_guard.py` runs on every free-text field before it reaches any provider. It regex-masks email addresses, phone numbers, and roll-number patterns. It **deliberately does not** try to catch names or addresses — the real PII boundary is architectural (README Decision 2: no student accounts, no student data collected at all). This module is a second-layer safety net for the case where a teacher pastes a paragraph that happens to contain a stray contact detail, not the primary defense.

---

## 7. Error handling contract

| Exception (`llm/errors.py`) | HTTP status | Meaning |
|---|---|---|
| `MissingCredentialsError` | 500 | The relevant API key env var isn't set |
| `LLMProviderError` | 502 | Provider rejected the request or was unreachable (billing, quota, overload, network) — message is the real provider error text |
| `GenerationTruncatedError` | 502 | Hit the output token cap before finishing — raise `max_tokens` |
| `GenerationRefusedError` | 502 | Blocked by the provider's safety filters |

All four are caught in `main.py` and returned as clean JSON `{"detail": "..."}` — nothing should ever surface as a raw Python traceback to the frontend. If it does, that's a bug (an uncaught exception type from a new provider, most likely).

---

## 8. Known gaps (explicit, so nobody assumes otherwise)

- **No database.** Nothing persists. No artifact library, no versioning, no audit log.
- **No RAG/ingestion.** `chunks=[]` everywhere; grounding is always off; no document upload exists.
- **No auth or tenancy.** Single-user, no `tenant_id` scoping anywhere.
- **No review/approve/export workflow.** Generation returns straight to the screen; there's no draft→approved gate despite that being a hard design requirement (README Decision 4).
- **No tests.**
- **Frontend mismatch:** `HLD.md` still documents a React frontend; the team pivoted to Streamlit for speed (README's tech-stack table + rejected-alternative note reflect this, `HLD.md` doesn't — worth reconciling before anyone reads it cold).
- **Gemini model contention** — see §4.

---

## 9. Next steps: Database integration

Target schema is already specified in `HLD.md` §3 and `README.md`'s data-model section — this is the build sequence to get there without over-building on day one.

1. **Add deps.** `sqlalchemy`, `alembic`, and a driver (`psycopg[binary]` for sync, or `asyncpg` if the routes go async) into `backend/requirements.txt`.
2. **Local Postgres with pgvector.** Easiest path for a hackathon: `docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg16`. Add `DATABASE_URL` to `.env`.
3. **Start minimal, not full HLD scope.** Don't build all 15 tables on day one. Minimum viable slice to make the current generation flow persistent:
   - `teaching_contexts` (grade, subject, board, language)
   - `artifacts` (type discriminator per README Decision 6, status: draft/approved, payload as JSON for now)
   - `learning_objectives` (id, artifact_id, text)
   - `questions` + `objective_alignments` (this is the pair that makes quiz coverage queryable — the whole point of README Decision 5)
   - `generation_runs` (model, prompt_version, input_tokens, output_tokens, pii_detected) — **this one is nearly free to add right now**, since `GenerationResult` already carries every field it needs; it's just an INSERT after each `client.generate()` call.
   Everything else in the HLD data model (`source_documents`, `document_chunks`, `citations`, `artifact_versions`, `audit_logs`, `vaults`-equivalent) can wait until RAG (§10) or the review/approve workflow actually need them.
4. **`alembic init`, first migration** for the tables above.
5. **A `db.py` session dependency** in FastAPI (`Depends(get_session)`), threaded into the two existing endpoints.
6. **Persist on generate, don't just return.** After `orchestrator.generate(...)` succeeds, write the `artifacts` + `learning_objectives` (+ `questions`/`objective_alignments` for quiz) rows, then return the artifact's ID alongside the payload.
7. **Add list/retrieve endpoints** (`GET /artifacts`, `GET /artifacts/{id}`) — this is what turns the current "generate and it's gone" flow into the "personal library" the README promises.
8. **Only after that:** the draft→approved status column and the approval gate (README Decision 4) — it needs artifacts to exist as rows before "approve" means anything.

---

## 10. Next steps: RAG / ingestion integration

The prompt layer already expects this — every `build_user_content()` in `llm/prompts/*.py` takes a `chunks: list[dict]` parameter and threads it through `wrap_reference_material()`. Nothing in the prompt layer needs to change; only the caller needs to stop passing `[]`.

1. **Enable pgvector** in a migration (`CREATE EXTENSION IF NOT EXISTS vector;`), add `document_chunks` (chunk text, page/section ref, embedding vector, `document_id`, `tenant_id`).
2. **Upload endpoint.** `POST /documents` accepting PDF/DOCX multipart, storing the raw file (local disk is fine for a hackathon; S3/blob storage later) and creating a `source_documents` row.
3. **Parsing.** `PyMuPDF` for PDF (gives page numbers — needed for citations), `python-docx` for DOCX. Write one `parse_document(path) -> list[{text, page}]` function; keep it synchronous and simple.
4. **Chunking.** Fixed-size with overlap (e.g. ~500 tokens, ~50 overlap) is enough to start. Don't build semantic/recursive chunking for a hackathon demo — it's not what anyone will be judged on.
5. **Embeddings — pick one path regardless of `LLM_PROVIDER`.** Anthropic has no first-party embeddings API (they recommend Voyage AI as a separate integration). The pragmatic hackathon move: **always use Gemini's embedding endpoint for chunks and queries, independent of which provider is generating text** — it's free-tier friendly and means embeddings don't need their own provider-abstraction layer. Store the resulting vector in `document_chunks.embedding`.
6. **Retrieval.** Given a topic + teaching context, embed the query the same way, run a pgvector cosine-similarity top-k query scoped to `tenant_id` and the teacher's selected documents.
7. **Wire it in.** Replace the hardcoded `chunks=[]` in `main.py`'s two endpoints with the retrieval call's output, passed straight into `orchestrator.generate(...)`. Grounding, citations, and the `is_grounded` flag all start working immediately — that logic already exists in `shared.py`, it's just never had real chunks to work with.
8. **Frontend citation display.** The Streamlit UI already shows the grounded/ungrounded badge per section; it does not yet render the citation list (`chunk_id`/document/page) that the schema already carries. Small addition once real citations start flowing.

---

## 11. Quick reference — what to touch for common changes

| Want to... | Touch |
|---|---|
| Add a new generation task type | New file in `llm/prompts/`, one `elif` in `orchestrator.py`'s `_REGISTRY`, one endpoint in `main.py` |
| Add a new LLM provider | New file in `llm/providers/`, one `elif` in `client.py` |
| Change what counts as PII | `llm/pii_guard.py`'s `_PATTERNS` |
| Change a prompt's output shape | Edit that task's `OUTPUT_SCHEMA` — remember Gemini strips `additionalProperties` automatically, no need to maintain two schema versions |
| Add persistence | §9 above |
| Add grounding/citations | §10 above |
