# AI-Assisted Approval Module — Technical Specification (Prototype / Future Work)

> **Status: PROTOTYPE SPECIFICATION ONLY. NOT INTEGRATED. NOT FUNCTIONAL.**
>
> Nothing in this folder is imported by, called from, or wired into the BIMS
> application in any way. Every file here is either documentation or an illustrative,
> non-functional placeholder. The current application continues to work exactly as it
> does today — see [`ISOLATION.md`](./ISOLATION.md) for an explicit, verifiable
> confirmation of that.

---

## 1. Objective

Assist the Chef des Techniciens and the Administration Supervisor during the
two-level approval workflow by automatically:

1. Comparing the uploaded photograph of the signed paper BI against the digital
   intervention form the technician filled in.
2. Detecting inconsistencies between the two (a different date, a different client
   name, a missing signature, a duration that doesn't match, etc.).
3. Generating a numerical confidence score reflecting how well the two agree.
4. Explaining, in plain language, exactly which fields disagree and why.
5. Suggesting — never automatically deciding — an Approve or Reject recommendation,
   which the human reviewer remains free to accept or override.

This is explicitly framed as **decision support, not decision automation**. The
specification's own long-term roadmap (Chapter 2.3) names "Artificial Intelligence"
as an out-of-first-version-scope future direction — this document is the concrete
design for that direction, prepared without touching the current, working
implementation.

## 2. Why this fits the existing application without changing it

The current review workflow already does the human half of this job manually: the
`InterventionReviewViewer.tsx` component already presents the digital form and the
attached photograph side by side for exactly this comparison, and the backend's
existing `approval_service.py` already has a single, well-defined point where a
decision is recorded (`decide_technical_approval()` /
`decide_administrative_approval()`). This AI module is designed to slot in as an
**advisory input to that same human decision point** — not to replace it, and not to
require any change to the transition rules, the audit trail, or the permission model
already in place (all documented in the main application's `ARCHITECTURE.md`).

## 3. Proposed architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Existing BIMS Application (UNCHANGED)                 │
│                                                                              │
│  InterventionReviewViewer.tsx                                                │
│         │ (future, optional) "Get AI Suggestion" button                       │
│         ▼                                                                     │
└─────────┼──────────────────────────────────────────────────────────────┘
          │  (future) HTTPS call to a SEPARATE service, never a direct import
          ▼
┌──────────────────────────────────────────────────────────────────────┐
│              AI Validation Service (future, standalone deployment)        │
│                                                                              │
│   1. OCR Pipeline           — extracts raw text from the paper-BI photo      │
│           │                                                                   │
│           ▼                                                                   │
│   2. Vision AI Pipeline     — detects structural elements (signature          │
│           │                     present? stamp present? handwriting          │
│           │                     legible regions?)                            │
│           ▼                                                                   │
│   3. Comparison Engine      — aligns OCR'd/detected fields against the        │
│           │                     digital form's actual stored values           │
│           │                     (fetched from BIMS's own API, read-only)      │
│           ▼                                                                   │
│   4. Confidence Scoring      — produces one overall score + one score per      │
│           │                     compared field                                │
│           ▼                                                                   │
│   5. Explanation Generator   — turns the raw comparison result into a          │
│                                human-readable list of what matches/differs     │
│                                                                              │
│   Output: { confidence_score, field_results[], suggested_decision,            │
│             explanation }                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

**Key architectural decision:** this is designed as a **separate service**, not as
new code inside `backend/app/services/`. Reasons:
- It has a fundamentally different runtime profile (potentially GPU-bound, slower,
  with external model dependencies) than the rest of the FastAPI application, which is
  a lightweight, fast, purely relational-database-backed API today.
- It can be developed, versioned, and deployed entirely independently, without ever
  touching the main application's release cycle.
- It keeps the "do not modify existing behavior" constraint trivially true — the main
  application would only ever need one small, optional, additive change (a button
  that calls out to this separate service) to eventually integrate it, and even that
  is explicitly **not implemented now**.

## 4. Folder structure (this repository, illustrative only)

```
future_ai_validation/
├── SPECIFICATION.md         This document.
├── ISOLATION.md              Explicit confirmation this folder is not wired in.
├── ROADMAP.md                 Phased implementation plan with time estimates.
├── backend/
│   ├── ocr/                    OCR pipeline design + a placeholder module.
│   │   └── ocr_pipeline.py.example
│   ├── vision/                  Vision AI pipeline design + a placeholder module.
│   │   └── vision_pipeline.py.example
│   ├── comparison/                The comparison engine design + a placeholder module.
│   │   └── comparison_engine.py.example
│   ├── schemas/                    Proposed request/response data shapes.
│   │   └── ai_review_schemas.py.example
│   └── api/                          Proposed API endpoint definitions (not mounted
│       └── ai_review_router.py.example   anywhere — see ISOLATION.md).
├── frontend/
│   └── components/
│       └── AISuggestionPanel.tsx.example   A proposed UI panel, not rendered anywhere.
└── docs/
    └── confidence_scoring.md      Detailed scoring-strategy design notes.
```

Every `.py.example`/`.tsx.example` file uses a non-executable extension
deliberately, so it cannot be accidentally imported by Python or picked up by the
TypeScript compiler even if someone later moves this folder somewhere the build
tooling can see it. See [`ISOLATION.md`](./ISOLATION.md) for the full reasoning.

## 5. Future OCR pipeline

**Purpose:** extract raw text from the photographed paper BI — dates, the client
name as handwritten, the technician's name, and any handwritten notes — so it can be
compared against the same fields on the digital form.

**Proposed approach:**
1. **Image preprocessing** — deskew, denoise, and binarize the uploaded photo (paper
   documents photographed in the field are rarely perfectly flat or evenly lit).
2. **Layout detection** — locate the BI's structured regions (a form template with
   known field positions would make this far more reliable than free-form OCR across
   the whole image — the paper BI's layout is fixed, so a template-matching approach
   is likely more accurate than general-purpose OCR for the structured fields, with
   general OCR reserved for the handwritten free-text areas).
3. **Text extraction** per detected region.
4. **Field-level output** — not just "here is all the text on the page," but a
   structured `{field_name: extracted_text, confidence}` mapping per known field,
   directly comparable against the digital form's stored values.

**Suggested tooling** (to be evaluated at implementation time, not decided here):
Tesseract (open-source, no external API dependency, well-suited to a structured-form
use case once layout detection narrows down each field's region) as a first,
lower-cost option; a cloud OCR API (e.g. a managed vision/OCR service) as a
higher-accuracy but higher-cost and higher-dependency alternative, particularly for
handwriting recognition, which template-based Tesseract alone handles poorly.

## 6. Future Vision AI pipeline

**Purpose:** go beyond text extraction to detect the *structural* elements a
reviewer currently checks visually — is there a signature present in the signature
area? Is there a company/client stamp? Is the handwriting legible at all, or is the
photo too blurry/dark to trust any extracted text from it?

**Proposed approach:**
1. **Signature-region detection** — a lightweight object-detection or region-classification
   model trained (or fine-tuned) specifically to answer "is there ink/a mark in this
   specific expected region of the form," since the paper BI's signature location is
   fixed by the form template.
2. **Image-quality assessment** — a simple, fast check (blur detection, brightness/
   contrast checks) run *before* OCR, so a genuinely unusable photo is flagged
   immediately ("image quality too low for reliable comparison") rather than silently
   producing a low-confidence-but-unexplained OCR result.
3. **(Optional, later phase) Stamp/logo detection** — if the company's paper BIs
   include an official stamp, a similar region-presence check could confirm it's
   present.

**Suggested tooling:** a general-purpose vision model (e.g. a small fine-tuned
classifier, or an existing pretrained document-analysis model) rather than training a
large model from scratch — the specific detection tasks here (signature present/absent,
image quality) are narrow and well-suited to lightweight, fast, cheaply-fine-tuned
models rather than a large general vision-language model, which would be needlessly
expensive to run at request time for what is fundamentally a binary/simple
classification task per region.

## 7. Comparison workflow

Once the OCR and Vision pipelines have both produced their output for a given
attachment, the comparison engine:

1. **Fetches the digital form's actual stored values** for that intervention from the
   real BIMS API (read-only — `GET /api/interventions/{id}`, the exact same endpoint
   the frontend already uses to display the review screen), so the AI service never
   needs its own copy of the intervention data and can never drift out of sync with
   what the application actually has stored.
2. **Aligns each OCR'd field against its digital counterpart** — e.g. the
   OCR-extracted date is string/date-parsed and compared against
   `intervention.intervention_date`; the OCR-extracted client name is fuzzy-matched
   (not exact-string-matched, since handwriting-to-text extraction is inherently
   imperfect) against `client.client_name`.
3. **Incorporates the Vision pipeline's structural findings** — e.g. "no signature
   detected" is treated as a distinct, high-severity finding, separate from and not
   conflatable with a low-confidence text-field mismatch.
4. **Produces one structured result per compared field**, plus one overall result —
   this per-field granularity is what lets the Explanation Generator (Section 9)
   produce a genuinely useful, specific explanation rather than a single opaque score.

## 8. Confidence scoring strategy

See [`docs/confidence_scoring.md`](./docs/confidence_scoring.md) for the detailed
design; summarized here:

- **Per-field confidence**, not just one overall number — a date mismatch and a
  missing signature are very different kinds of problems, and collapsing them into
  one score would hide exactly the information a reviewer needs.
- **Weighted overall score** — not every field matters equally; a mismatched
  technical-report free-text field (inherently the hardest to OCR reliably, and the
  least likely to actually indicate fraud or error) should weigh less than a
  mismatched date or a missing signature.
- **Explicit "cannot assess" state**, distinct from "low confidence" — if the Vision
  pipeline's image-quality check fails, the correct output is "unable to reliably
  compare this attachment," never a fabricated low score that looks like a real
  finding.
- **The suggested decision is a recommendation only** — e.g. "Suggested: Approve
  (confidence 0.91)" or "Suggested: Review carefully — 2 fields disagree
  (confidence 0.42)," never a binary auto-decision, and never something the system
  acts on without the human reviewer explicitly clicking Approve/Reject themselves
  through the existing, unchanged workflow.

## 9. Explanation generation

For every field where the comparison result falls below a configurable
"confident-match" threshold, the system generates one specific, human-readable
sentence — e.g. *"The date on the attached document appears to read '12/03/2026', but
the digital form has '13/03/2026' — please verify."* rather than a bare numeric score
with no context. This is the piece most directly aimed at trust: a reviewer is far
more likely to appropriately trust (or appropriately override) a suggestion they can
see the specific reasoning for, versus an opaque number.

## 10. Suggested API endpoints (proposed, not implemented, not mounted anywhere)

All hypothetical, all namespaced separately from the real application's `/api` prefix
specifically so there is never any possibility of an accidental route collision:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/ai-review/analyze/{intervention_id}` | Trigger analysis for a given intervention's attachment(s); returns a job ID (analysis is likely too slow to be synchronous). |
| `GET` | `/ai-review/result/{job_id}` | Poll for the analysis result once ready. |
| `GET` | `/ai-review/result/{job_id}/explanation` | Fetch just the human-readable explanation text, separately from the raw structured result (useful for a lightweight UI panel that doesn't need every raw field). |

See [`backend/api/ai_review_router.py.example`](./backend/api/ai_review_router.py.example)
for an illustrative FastAPI router sketch using these exact paths — deliberately
**not** using the real application's router-registration pattern (`app.include_router`
in `main.py`), since this file is never meant to be mounted onto the real app.

## 11. Integration plan (future, when actually implemented)

If and when this is actually built and the team decides to integrate it, the
integration surface with the *existing, unchanged* application would be intentionally
minimal:

1. **One new, optional button** in `InterventionReviewViewer.tsx` — "Get AI
   Suggestion" — visible only to `chef_technicien`/`admin_supervisor` reviewers,
   calling the new, separate AI service's API directly (not through the main BIMS
   backend at all, avoiding any change to `backend/app/api/`).
2. **The AI service reads from BIMS's existing API** (`GET /api/interventions/{id}`
   and the existing attachment-download endpoint) — it never writes to the BIMS
   database, and never needs its own copy of application data.
3. **No change to the approval decision path itself** — `decide_technical_approval()`/
   `decide_administrative_approval()` in the real `approval_service.py` remain
   exactly as they are today; a human still explicitly clicks Approve or Reject, the
   AI suggestion is purely informational context shown alongside that decision.
4. **No change to the database schema** — the AI service's own analysis results, if
   persisted at all, would live in its own separate storage, not in any BIMS table.

This plan is deliberately structured so that steps 1–4 could each be reviewed,
approved, and rolled back independently — the actual current application's behavior
is never at risk from this future work, even once it moves from specification to
real implementation.

## 12. Required libraries (proposed, not installed, not added to any requirements file)

| Library | Purpose |
|---|---|
| `pytesseract` / Tesseract OCR engine | OCR text extraction (open-source option) |
| A cloud OCR/Vision API SDK (provider TBD) | Higher-accuracy OCR/handwriting alternative |
| `opencv-python` | Image preprocessing (deskew, denoise, quality checks) |
| `Pillow` | General image loading/manipulation |
| A small ML framework (e.g. `torch` or `onnxruntime` for inference only) | Running the signature-detection / image-quality classifier |
| `rapidfuzz` (or similar) | Fuzzy string matching for comparing OCR'd text against stored field values |
| `celery` or a similar task queue (+ Redis) | Running analysis asynchronously, given OCR/Vision inference is unlikely to be fast enough for a synchronous HTTP request |

None of these are installed anywhere in this repository — this is a proposed list
for a future, separate service's own dependency file, not an addition to
`backend/requirements.txt`.

## 13. Estimated implementation roadmap

See [`ROADMAP.md`](./ROADMAP.md) for the full phased breakdown with effort estimates.
