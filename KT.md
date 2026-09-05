# KT — MyLesson.ai (Engineering Handoff)

Written for anyone picking this up cold. Covers what's actually built and running today (not what the design docs describe), how it fits together, and concrete next steps for what's still missing.

Read this alongside `README.md` (product framing + design decisions), `BRD.md`/`SRS.md`/`HLD.md` (target design). **This doc is the "as-built" reality check** — where it diverges from those, that's called out explicitly rather than silently.

---

## 1. What's actually working right now

A real, end-to-end system: authenticated multi-user access, PDF ingestion into a real vector store, and grounded generation with citations. **Verified live, not just claimed** — see §8 and §9 for the actual test transcripts.

```
Browser
   │
   ▼
Streamlit (frontend/app.py)  ── login/register gate, HTTP Basic on every call
   │  HTTP + Basic Auth
   ▼
FastAPI (backend/app/main.py)
   │
   ├─ auth.py ── get_current_user() verifies against users table (bcrypt)
   │
   ├─ POST /documents ──► parser.py → chunker.py → embeddings.py (Gemini) ──► Postgres
   │                                                                          (source_documents,
   │                                                                           document_chunks
   │                                                                           vector(768))
   │
   └─ POST /generate/* ──► retriever.py (pgvector cosine similarity,
                            tenant_id enforced in the query itself)
                                  │
                                  ▼
                          Orchestrator (services/generation/orchestrator.py)
                                  │
                                  ▼
                          Prompt module (llm/prompts/*.py)
                                  │
                                  ▼
                          client.py ── provider dispatch (LLM_PROVIDER env var)
                                  │
                                  ├──► providers/anthropic_provider.py
                                  └──► providers/gemini_provider.py
                                  │
                                  ▼
                          Real model, real structured JSON, grounded + cited
```

**What's still missing from this loop:** generated artifacts don't persist. A lesson plan or quiz comes back to the screen and is gone when you refresh — there's no `artifacts` table yet, no library, no draft→approved workflow. Source documents and chunks *do* persist (real Postgres rows); generation output does not. See §10 and §11.

---

## 2. Repository map

```
.
├── .env                          # secrets + provider config (gitignored)
├── run_everything.py             # one-click dev runner — see §3
├── README.md / BRD.md / SRS.md / HLD.md   # design docs (target state, not fully as-built)
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI app — auth, documents, and generation endpoints
│       ├── db.py                 # SQLAlchemy engine/session, init_db() (no Alembic yet)
│       ├── auth.py               # HTTP Basic auth, bcrypt, get_current_user() dependency
│       ├── models/
│       │   ├── user.py           # User (username, password_hash)
│       │   └── document.py       # SourceDocument, DocumentChunk (tenant_id, vector(768))
│       ├── schemas/
│       │   ├── auth.py           # RegisterRequest, UserResponse
│       │   ├── document.py       # DocumentResponse
│       │   └── generation.py     # request/response Pydantic models
│       ├── services/
│       │   ├── generation/orchestrator.py   # task_type → prompt module dispatch
│       │   ├── ingestion/
│       │   │   ├── parser.py     # PyMuPDF, page-numbered text extraction
│       │   │   └── chunker.py    # fixed-size + overlap, never crosses a page boundary
│       │   └── retrieval/retriever.py   # pgvector cosine-similarity top-k, tenant-scoped
│       └── llm/
│           ├── client.py         # provider dispatch (reads LLM_PROVIDER)
│           ├── errors.py         # shared exception types, all providers raise these
│           ├── embeddings.py     # Gemini embeddings — always, regardless of LLM_PROVIDER
│           ├── pii_guard.py      # regex PII scrub, runs before every prompt
│           ├── providers/
│           │   ├── anthropic_provider.py
│           │   └── gemini_provider.py
│           └── prompts/          # one file per task_type — see §5
│               ├── shared.py
│               ├── lesson_plan.py
│               ├── quiz.py
│               ├── material.py
│               ├── explanation.py
│               ├── activity.py
│               └── section_regenerate.py
└── frontend/
    ├── requirements.txt
    ├── api_client.py             # thin HTTP wrapper — every call takes an `auth` tuple
    └── app.py                    # login/register gate + single-page UI
```

**Not present yet:** no `alembic/`, no `artifacts`/`learning_objectives`/`questions`/`generation_runs` tables, no `services/export/`, no tests. All named in HLD/README as target structure — none built.

---

## 3. How to run it

### First-time local setup (one-time, per machine)

```bash
brew install postgresql@18 pgvector    # or whatever Postgres major version you're on
brew services start postgresql@18
createdb mylesson
psql -d mylesson -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Every time

```bash
# fill in .env first: ANTHROPIC_API_KEY and/or GEMINI_API_KEY, LLM_PROVIDER, DATABASE_URL
python run_everything.py
```

This creates a **single shared** `.venv` at repo root (not per-component, unlike what the README's manual setup describes — a dev-convenience shortcut), installs both `backend/requirements.txt` and `frontend/requirements.txt` into it, starts FastAPI with `--reload` on `:8000`, waits for `/health`, then starts Streamlit on `:8501`. Tables are created automatically on backend startup via `init_db()`. Ctrl+C stops both.

**First thing in the browser:** the app now gates on login. Use the "Create account" tab to register — there's no seed user, no admin bootstrap, just self-serve signup.

Env vars that matter (`.env`):

| Var | Purpose |
|---|---|
| `LLM_PROVIDER` | `anthropic` or `gemini` — selects which `providers/*.py` backend `client.py` loads |
| `ANTHROPIC_API_KEY` | Required if `LLM_PROVIDER=anthropic` |
| `GEMINI_API_KEY` | Required if `LLM_PROVIDER=gemini` **or always**, since embeddings use Gemini regardless of provider (§8) |
| `LLM_MODEL_PRIMARY` | Model ID — see §4 for per-provider gotchas |
| `DATABASE_URL` | e.g. `postgresql+psycopg://<you>@localhost:5432/mylesson` |
| `API_BASE_URL` | Read by the frontend to find the backend; defaults to `localhost:8000` |

---

## 4. The provider abstraction (Decision 9, made real)

`client.py` is a **dispatcher, not an implementation** — it re-exports the shared exception types from `errors.py` and imports exactly one of the two provider backends based on `LLM_PROVIDER`. Prompts and the orchestrator never import a provider directly.

| | Anthropic | Gemini |
|---|---|---|
| Transport | Official `anthropic` SDK | Raw REST (`requests`) to `generateContent` — no SDK |
| Structured output | `output_config.format` (json_schema) | `generationConfig.responseSchema` |
| **Gotcha** | `thinking: adaptive` + `effort` only work on the 4.6+ tier — Haiku 4.5 400s if you send them. `_supports_adaptive_thinking()` in `anthropic_provider.py` gates this by model prefix. | `responseSchema` **rejects `additionalProperties`** outright (400) — stripped recursively in `gemini_provider.py`'s `_strip_unsupported_keys()`. Separately, the **`-lite` model variants reject `thinkingConfig` entirely** (400) and don't do hidden reasoning anyway — `generate()` only sends it for non-lite models. |
| Cost lever | Model choice only | `thinkingConfig: {thinkingBudget: 0}` on non-lite models — the full flash line does hidden reasoning by default and bills it as tokens even for trivial output (measured: 131 total tokens to say "Hello", 120 of them invisible thinking). |

**Default model is now `gemini-flash-lite-latest`**, not `gemini-flash-latest`. The non-lite alias was hitting persistent free-tier "high demand" overload errors during testing (likely a very new model release getting hammered); `gemini-2.5-flash` is fully deprecated for new users (404, pointing at `gemini-3.6-flash`/"the Interactions API" instead). Lite is also cheaper, which was the point of switching providers in the first place.

If demo-day reliability is a concern, **the fastest mitigation is flipping `LLM_PROVIDER=anthropic` in `.env`** (assuming that account has credits) rather than fighting model-alias contention — the whole point of this abstraction is that the swap is one env var, not a code change.

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

All of them (except `activity`) route retrieved chunks through `shared.wrap_reference_material()`, which delimits them as `<reference_material>` and explicitly frames anything inside as data, never instructions (prompt-injection defense). This is no longer theoretical — real chunks flow through here now (§8).

---

## 6. PII handling

`pii_guard.py` runs on every free-text field before it reaches any provider. It regex-masks email addresses, phone numbers, and roll-number patterns. It **deliberately does not** try to catch names or addresses — the real PII boundary is architectural (README Decision 2: no student accounts, no student data collected at all). This module is a second-layer safety net for the case where a teacher pastes a paragraph that happens to contain a stray contact detail, not the primary defense.

---

## 7. Error handling contract

| Exception | Raised by | HTTP status | Meaning |
|---|---|---|---|
| `MissingCredentialsError` (`llm/errors.py`) | any LLM provider | 500 | The relevant API key env var isn't set |
| `LLMProviderError` (`llm/errors.py`) | any LLM provider | 502 | Provider rejected the request or was unreachable (billing, quota, overload, network) — message is the real provider error text |
| `GenerationTruncatedError` (`llm/errors.py`) | any LLM provider | 502 | Hit the output token cap before finishing — raise `max_tokens` |
| `GenerationRefusedError` (`llm/errors.py`) | any LLM provider | 502 | Blocked by the provider's safety filters |
| `EmbeddingError` (`llm/embeddings.py`) | ingestion, retrieval | 502 | Gemini's embedding endpoint failed — no API key, quota, or network |
| 401 (no custom exception) | `auth.py`'s `get_current_user` | 401 | Bad username/password, or no credentials sent |

All of the above are caught in `main.py` and returned as clean JSON `{"detail": "..."}` — nothing should ever surface as a raw Python traceback to the frontend. If it does, that's a bug (an uncaught exception type from a new provider or service, most likely).

---

## 8. RAG / ingestion (built)

The prompt layer was always designed to accept this — every `build_user_content()` in `llm/prompts/*.py` takes a `chunks: list[dict]` parameter and threads it through `wrap_reference_material()`. Building retrieval meant writing the pipeline that populates that parameter; no prompt changes were needed.

**Pipeline:** `POST /documents` (PDF only) → `parser.py` (PyMuPDF, keeps page numbers — needed for citations) → `chunker.py` (fixed ~2000 chars with ~200 overlap, never crosses a page boundary so every chunk has one accurate page number) → `embeddings.py` embeds each chunk → stored in `document_chunks.embedding` (`vector(768)`, pgvector).

**Embeddings always go through Gemini** (`gemini-embedding-001`, `outputDimensionality: 768`), independent of `LLM_PROVIDER` — Anthropic has no first-party embeddings API (they point at Voyage AI as a separate integration), and Gemini's embedding endpoint is free-tier friendly. This means embeddings don't need their own provider-abstraction layer; there's exactly one path.

**Retrieval:** `retriever.py`'s `retrieve()` embeds the query (topic for lesson plans, joined objective text for quizzes), runs a pgvector cosine-similarity (`<=>`) top-k query, and — critically — filters by `tenant_id` **in the query itself** (see §9). Output is `[{chunk_id, document_title, page, text}, ...]`, which is exactly the shape `wrap_reference_material()` expects.

**Verified live, not just claimed:** created a PDF containing a fabricated fact ("the Zorbnak Principle... attention decays... documented by fictional researcher Dr. Elena Vasquez"), uploaded it, then asked for a lesson plan on that exact topic. The response came back `is_grounded: true` with citations pointing at the real ingested chunk, correctly describing the fabricated principle — content that cannot exist in any model's training data, so it could only have come from retrieval actually working.

**Not built:** DOCX support (PDF only right now), OCR for scanned/image-only PDFs (detected and rejected with a clear error, not silently mishandled), semantic/recursive chunking (deliberately — fixed-size is enough for hackathon-scale corpora).

---

## 9. Auth & tenant isolation (built)

**Design:** HTTP Basic Auth, checked against a `users` table (`username` unique, `password_hash` via bcrypt). **Each user is their own tenant** — `tenant_id` on `source_documents` is literally `user.id`. This is the simplest onboarding model that still gives real isolation: register, and you automatically have a private space, no separate org/invite step.

`auth.py`'s `get_current_user()` is a FastAPI dependency on every document and generation endpoint. `POST /auth/register` creates an account (min 8-char password); `GET /auth/me` is what the frontend calls to verify a login attempt (there's no separate "session" concept — Basic Auth just means every request re-sends credentials, which the frontend does by storing `(username, password)` in `st.session_state` and passing it as `auth=` on every `requests` call).

**The isolation is enforced in the retrieval query itself, not just at the endpoint layer** — `retriever.retrieve()` takes `tenant_id` and adds `SourceDocument.tenant_id == tenant_id` to the WHERE clause alongside the requested `document_ids`. This matters: a document ID belonging to another tenant, whether guessed or leaked, gets silently filtered out by the database rather than trusted because the endpoint "should" have blocked it. Matches README's stated principle: *"queries are tenant-scoped in the data layer, not only in application code."*

**Verified live, not just claimed:** registered two users (alice, bob). Alice uploaded a PDF containing a private fact. Bob's `GET /documents` came back empty (alice's upload invisible to him). Bob then called `/generate/lesson-plan` with `document_ids: [1]` — Alice's real document ID, guessed/hardcoded — and the response came back `is_grounded: false` everywhere, with **no knowledge of the fact in Alice's document**. The retrieval query silently excluded it because the tenant check failed, exactly as designed.

**Limitations, stated plainly:**
- No rate limiting on login attempts, no password reset flow, no email verification, no MFA. Fine for a hackathon demo where the bar is "can't see another teacher's data," not a hardened identity system.
- HTTP Basic sends credentials (base64-encoded, not encrypted) on every single request. Acceptable over `localhost` in dev; **would need HTTPS before any real deployment** — Basic Auth without TLS is credentials-in-the-clear.
- No `/auth/logout` endpoint needed (there's no server-side session to invalidate) — the frontend's "Log out" button just clears `st.session_state`.

**Operational lesson learned, worth repeating for whoever touches the schema next:** adding the `users` table and the `tenant_id` column on `source_documents` required dropping and recreating those tables, because `Base.metadata.create_all()` (no Alembic yet — see §11) only creates missing tables, it doesn't alter existing ones. Before doing that, **always check row counts first** — a document had actually been uploaded through the running UI between sessions, and it got dropped along with the schema change because the row count wasn't checked before running `DROP TABLE ... CASCADE`. No real harm done here (it was test data), but the next schema change should check `SELECT count(*)` on every affected table before touching it, or better, finally add Alembic so schema changes don't require destructive rebuilds at all.

---

## 10. Known gaps (explicit, so nobody assumes otherwise)

- **No artifact persistence.** Generated lesson plans and quizzes are never saved — no `artifacts`, `learning_objectives`, `questions`, or `generation_runs` tables exist yet. Refreshing the browser loses everything generated. This is the main remaining gap; see §11.
- **No review/approve/export workflow.** Generation returns straight to the screen; there's no draft→approved gate despite that being a hard design requirement (README Decision 4) — there's nothing to gate yet, since nothing persists.
- **DOCX ingestion not implemented** — PDF only.
- **No Alembic.** Schema changes currently mean dropping tables (see the incident in §9). Real risk now that real user accounts and documents exist in the DB, unlike before.
- **No tests.**
- **Frontend mismatch:** `HLD.md` still documents a React frontend; the team pivoted to Streamlit for speed (README's tech-stack table + rejected-alternative note reflect this, `HLD.md` doesn't — worth reconciling before anyone reads it cold).
- **README's tech-stack table still says "Auth: JWT with tenant claim"** — what's actually built is HTTP Basic + bcrypt, which satisfies the tenant-isolation requirement but not the JWT specifics. Worth reconciling or explicitly marking JWT as a Phase 2 upgrade.

---

## 11. Next steps: persisting generated artifacts

The ingestion side of the database is done (§8, §9) — this section is what's left to make *generation output* durable, which is the difference between "a chat window" and "a personal library" (the README's stated goal).

1. **Add tables to `models/`** following the pattern in `models/document.py`: `Artifact` (type discriminator per README Decision 6, `tenant_id`, status: draft/approved, JSON payload column is fine for now), `LearningObjective`, `Question` + `ObjectiveAlignment` (the pair that makes quiz coverage queryable — README Decision 5), `GenerationRun`.
2. **`GenerationRun` is nearly free to add right now** — `GenerationResult` (in `llm/errors.py`) already carries `model`, `input_tokens`, `output_tokens`, `pii_detected`. It's just an INSERT after each `client.generate()` call inside the orchestrator or the endpoint.
3. **Persist on generate, don't just return.** After `orchestrator.generate(...)` succeeds in `main.py`, write the `Artifact` + `LearningObjective` (+ `Question`/`ObjectiveAlignment` for quiz) rows scoped to `current_user.id`, then return the artifact's ID alongside the payload.
4. **Add list/retrieve endpoints** (`GET /artifacts`, `GET /artifacts/{id}`), tenant-scoped the same way `/documents` already is — copy that pattern directly.
5. **Only after that:** the draft→approved status column and the approval gate (README Decision 4) — it needs artifacts to exist as rows before "approve" means anything.
6. **Add Alembic** before this schema grows further — see the incident note in §9. `alembic init`, then a migration per table added above, instead of continuing to drop-and-recreate.

---

## 12. Quick reference — what to touch for common changes

| Want to... | Touch |
|---|---|
| Add a new generation task type | New file in `llm/prompts/`, one `elif` in `orchestrator.py`'s `_REGISTRY`, one endpoint in `main.py` |
| Add a new LLM provider | New file in `llm/providers/`, one `elif` in `client.py` |
| Change what counts as PII | `llm/pii_guard.py`'s `_PATTERNS` |
| Change a prompt's output shape | Edit that task's `OUTPUT_SCHEMA` — remember Gemini strips `additionalProperties` automatically, no need to maintain two schema versions |
| Add a new tenant-scoped table | Follow `models/document.py` + `retriever.py`'s pattern: `tenant_id` FK to `users.id`, filter by it in every query, never trust a client-supplied ID alone |
| Persist generated artifacts | §11 above |
| Support DOCX upload | Add a `parse_docx()` alongside `parser.py`'s `parse_pdf()`, branch on file extension in `main.py`'s upload endpoint |
