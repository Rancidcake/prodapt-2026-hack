# HLD — MyLesson.ai

## 1. Architecture Overview

MyLesson.ai uses a curriculum-grounded generation architecture.

```text
                    ┌─────────────────┐
                    │     Teacher     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ React Frontend  │
                    │ Teaching UI     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ FastAPI Backend │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌─────────────┐
       │ Ingestion  │ │ Retrieval  │ │ Generation  │
       │ Parser     │ │ / RAG      │ │ Orchestrator│
       └─────┬──────┘ └─────┬──────┘ └──────┬──────┘
             │              │               │
             └──────────────┼───────────────┘
                            ▼
                  ┌──────────────────┐
                  │ PostgreSQL +     │
                  │ pgvector         │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Draft Artifact   │
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │ Teacher Review   │
                  │ Edit / Regenerate│
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │ Approval Gate    │
                  └────────┬─────────┘
                           ▼
                         Export
```

## 2. Main Components

### 2.1 Frontend
**React + Vite + TypeScript + Tailwind CSS**

Responsibilities:
- Curriculum upload
- Teaching Context display/edit
- Lesson Studio
- Generation controls
- Artifact editor
- Objective coverage display
- Review and approval
- Export/library UI

### 2.2 API Backend
**FastAPI + Pydantic**

Responsibilities:
- Authentication/authorization
- API contracts
- Teaching Context management
- Generation orchestration
- Artifact lifecycle
- Review/approval
- Export requests

### 2.3 Ingestion Service
Responsibilities:
1. Accept document
2. Parse text
3. Preserve page/section metadata
4. Chunk content
5. Generate embeddings
6. Store chunks and embeddings

For MVP, PDF/DOCX parsing can use PyMuPDF and python-docx.

### 2.4 Retrieval Layer
Uses PostgreSQL + pgvector.

Flow:

```text
Teacher Request
      ↓
Generate query embedding
      ↓
Similarity search
      ↓
Top relevant chunks
      ↓
Citations + generation context
```

Retrieved content is treated as reference data, never as system instructions.

### 2.5 Generation Layer

All AI features use a common generation abstraction:

```text
Teaching Context
      +
Retrieved Context
      +
Task Type
      +
User Constraints
      ↓
Prompt Template
      ↓
LLM Provider
      ↓
Schema Validation
      ↓
Artifact
```

Task types:
- `lesson_plan`
- `simplify`
- `activity`
- `material`
- `quiz`
- `adapt`

### 2.6 Review & Approval Layer

```text
Generate
   ↓
DRAFT
   ↓
Teacher edits/regenerates
   ↓
APPROVED
   ↓
EXPORT
```

The backend must enforce approval; the frontend alone must not be trusted.

## 3. Data Model

```text
Tenant
 └── User
      ├── TeachingContext
      ├── SourceDocument
      │    └── DocumentChunk
      └── Artifact
           ├── ArtifactSection
           ├── LearningObjective
           ├── Question
           │    └── QuestionOption
           ├── ObjectiveAlignment
           ├── Citation
           └── ArtifactVersion

GenerationRun ──► PromptTemplate
AuditLog
```

Every tenant-owned record carries `tenant_id`.

## 4. Generation Flow

```text
1. Teacher selects topic/objective
2. Backend loads Teaching Context
3. Backend retrieves relevant source chunks
4. Prompt is assembled from:
      - Teaching Context
      - retrieved references
      - task type
      - constraints
5. LLM generates structured output
6. Pydantic/schema validation runs
7. Citations/objective mappings are stored
8. Artifact is saved as draft
9. Frontend streams/displays result
10. Teacher edits or regenerates sections
11. Teacher explicitly approves
12. Approved artifact can be exported
```

## 5. Lesson Studio Flow

```text
Topic + Objectives + Grade + Duration + Class Size
                         ↓
                 Teaching Context
                         ↓
                  Retrieve Sources
                         ↓
                 Lesson Generator
                         ↓
              Structured Lesson Plan
                         ↓
              Objective Coverage Check
                         ↓
                  Teacher Review
```

## 6. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript |
| Styling | Tailwind CSS |
| Backend | FastAPI + Python |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Parsing | PyMuPDF + python-docx |
| AI | Provider-abstracted LLM |
| Validation | Pydantic |
| Queue | PostgreSQL queue / optional RQ |
| Export | ReportLab + python-docx |
| Deployment | Vercel + backend/container hosting |

## 7. MVP Simplification

For the hackathon, prioritize:

1. Curriculum upload
2. Teaching Context extraction
3. Retrieval + grounding
4. Lesson Studio
5. Quiz + objective alignment
6. Review/edit/approve
7. Concept simplification
8. Activities/materials
9. Export

Advanced infrastructure such as full multi-tenant administration, extensive analytics, LMS integration and student-facing workflows can remain Phase 2.

## 8. Key Architectural Principle

> **One Teaching Context → one generation pipeline → multiple teacher-facing artifacts.**

This prevents the product from becoming a collection of unrelated AI prompt generators and keeps the curriculum-agnostic design central to the system.
