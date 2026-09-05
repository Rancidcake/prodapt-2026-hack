# SRS — MyLesson.ai

## 1. Purpose
Define the functional and non-functional requirements for MyLesson.ai.

## 2. System Users
**Teacher:** uploads curriculum, creates teaching contexts, generates artifacts, edits outputs and approves exports.

## 3. Functional Requirements

### FR-01 — Source Upload
The system shall allow teachers to upload supported syllabus, curriculum, chapter or teaching documents.

### FR-02 — Curriculum Understanding
The system shall extract:
- Subject
- Grade/level
- Units and topics
- Learning objectives
- Prerequisites
- Key concepts

### FR-03 — Teaching Context
The system shall maintain a reusable Teaching Context containing curriculum information and teacher-selected constraints.

### FR-04 — Lesson Plan Generation
The system shall generate a lesson plan containing:
- Learning objectives
- Prerequisites
- Duration and timings
- Introduction/hook
- Teacher activities
- Student activities
- Guided/independent practice
- Checks for understanding
- Assessment
- Differentiation
- Homework/extension

### FR-05 — Concept Simplification
The system shall generate explanations, analogies, examples, misconceptions and quick checks at the requested level.

### FR-06 — Activity Generation
The system shall generate classroom activities based on topic, objective, duration, class size and available resources.

### FR-07 — Learning Material Generation
The system shall generate handouts, worksheets, revision summaries and slide/board outlines.

### FR-08 — Quiz Generation
The system shall generate MCQs, short-answer, long-answer and numerical questions with configurable difficulty and answer keys.

### FR-09 — Objective Alignment
The system shall associate generated lesson content and quiz questions with Learning Objectives and report objective coverage.

### FR-10 — Grounded Generation
When source documents are selected, the system shall retrieve relevant document chunks and attach citations to generated content where applicable.

### FR-11 — Ungrounded Warning
When no source material is selected, generated artifacts shall be visibly marked as requiring teacher verification.

### FR-12 — Adaptation
The system shall allow teachers to adapt an artifact for learner level, teaching time, class size or other classroom constraints.

### FR-13 — Review
Teachers shall be able to edit artifact sections and regenerate individual sections using a free-text instruction.

### FR-14 — Approval Gate
New artifacts shall begin in `draft` status. Only an explicit teacher action shall move an artifact to `approved`.

### FR-15 — Export
Only approved artifacts shall be exportable without a draft/unreviewed indication.

### FR-16 — Versioning
The system shall maintain artifact versions and generation metadata.

## 4. Non-Functional Requirements

- **Usability:** A teacher should be able to create an artifact with minimal configuration.
- **Performance:** Common generation requests should target approximately ≤25 seconds at p95.
- **Reliability:** LLM outputs shall be schema-validated before presentation where practical.
- **Security:** Tenant-owned data must remain isolated.
- **Privacy:** Teacher-uploaded content must not be exposed to other tenants.
- **Traceability:** Generation, editing, approval and export actions should be auditable.
- **Extensibility:** New curricula, subjects and generation modes should not require curriculum-specific code branches.

## 5. Core Data Entities
- Tenant
- User
- TeachingContext
- SourceDocument
- DocumentChunk
- LearningObjective
- Artifact
- ArtifactSection
- ArtifactVersion
- Question
- QuestionOption
- ObjectiveAlignment
- Citation
- GenerationRun
- PromptTemplate
- AuditLog

## 6. Artifact States

```text
draft → edited/regenerated → approved → exported
  ↑             │
  └─────────────┘
```

There shall be no automatic approval path.

## 7. Quality Requirements

### Structural
- Required lesson sections are present.
- Quiz questions contain valid answers.
- Questions map to objectives where alignment is requested.

### Grounding
- Citations resolve to actual source chunks.
- Citations belong to the teacher's source documents.

### Human Review
- Sampled outputs are reviewed for factual accuracy, curriculum alignment, level appropriateness and usability.

## 8. Security Requirements
- Server-side authorization
- Tenant-scoped queries
- Secrets stored server-side
- Retrieved documents treated as untrusted reference data
- Audit logging for important actions
- Configurable data retention/deletion

## 9. MVP Acceptance Criteria
A teacher can:
1. Upload a curriculum/source document.
2. See an extracted Teaching Context.
3. Select a topic/objective.
4. Generate a lesson plan.
5. Generate at least one supporting artifact.
6. Generate a quiz linked to objectives.
7. Adapt or regenerate content.
8. Review and edit the result.
9. Explicitly approve it.
10. Export the approved artifact.
