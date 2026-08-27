# Estimated Implementation Roadmap

Rough, planning-level effort estimates for turning the specification in
`SPECIFICATION.md` into a real, working (but still separate, still optional) service.
These are estimates for a single developer working incrementally, phased so that each
phase produces something demonstrable on its own rather than requiring the whole
thing to be built before anything can be shown.

## Phase 0 — Groundwork (~1 week)
- Set up the separate service's own repository/deployment (independent of BIMS's own
  repo and deployment pipeline).
- Collect a small labeled dataset of real (or realistic mock) paper-BI photographs
  paired with their correct digital-form values, for evaluating OCR/Vision accuracy
  before building anything else on top of unreliable extraction.
- Decide, concretely, between the open-source (Tesseract) and cloud-API OCR options
  based on accuracy against that labeled set — this decision meaningfully affects
  every later phase's cost and complexity, so it belongs first.

## Phase 1 — OCR pipeline, structured fields only (~2 weeks)
- Image preprocessing (deskew/denoise/quality-check).
- Layout/template detection for the paper BI's known structured fields.
- Field-level text extraction with a per-field confidence value.
- **Demonstrable output at the end of this phase:** given a photo, produce a
  `{field_name: extracted_text}` mapping — no comparison against BIMS yet.

## Phase 2 — Comparison engine against real BIMS data (~1–2 weeks)
- Read-only integration against the real BIMS API (`GET /api/interventions/{id}`).
- Field alignment and fuzzy-matching logic between OCR output and stored values.
- **Demonstrable output at the end of this phase:** given a real intervention ID,
  produce a per-field match/mismatch result — still no scoring or UI yet.

## Phase 3 — Vision AI pipeline (~2–3 weeks)
- Signature-presence detection.
- Image-quality gating (reject/flag unusable photos before they reach OCR/comparison
  at all).
- This phase is scoped separately from Phase 1 because it's a genuinely different
  kind of model (detection/classification vs. text extraction) and can be developed
  and evaluated in parallel with Phases 1–2 by a second contributor if the team has
  one available, rather than strictly sequentially.

## Phase 4 — Confidence scoring + explanation generation (~1 week)
- Implement the weighted per-field/overall scoring strategy from
  `docs/confidence_scoring.md`.
- Implement the plain-language explanation generator.
- **Demonstrable output at the end of this phase:** the full
  `{confidence_score, field_results[], suggested_decision, explanation}` structure,
  for a real intervention, end to end — this is the first point where the module is
  functionally "complete" as a standalone service, even with no UI yet.

## Phase 5 — API layer + async job handling (~1 week)
- Wrap the pipeline behind the three proposed endpoints
  (`/ai-review/analyze`, `/ai-review/result/{job_id}`, `.../explanation`).
- Add a task queue (Celery + Redis, or equivalent) so analysis runs asynchronously
  rather than blocking an HTTP request for what could be several seconds of
  OCR/Vision inference.

## Phase 6 — Frontend integration (~3–5 days)
- Build the "Get AI Suggestion" panel (see
  `frontend/components/AISuggestionPanel.tsx.example` for an illustrative starting
  shape).
- Add the one new, optional button to `InterventionReviewViewer.tsx` (the only touch
  point on the real, existing application — everything else in this roadmap happens
  entirely inside the separate service).

## Phase 7 — Evaluation and tuning (ongoing)
- Compare the model's suggested decisions against real human decisions over time to
  measure and improve accuracy before treating the suggestions as trustworthy enough
  to actively promote to reviewers as a default-on feature.
- This phase is deliberately open-ended and ongoing rather than a fixed deliverable —
  a decision-support AI feature's real value only becomes measurable once it's used
  against real cases over real time, not something that can be fully validated before
  first deployment.

## Total rough estimate

Roughly **8–11 weeks** of focused development to reach a working, demonstrable
end-to-end prototype (through Phase 6), for a single developer — with Phase 7 as
ongoing refinement rather than a hard endpoint. This is a rough planning estimate, not
a commitment, and does not include the model-training/fine-tuning effort that Phase 3
specifically might require if a suitable pretrained signature-detection model isn't
readily available and needs to be trained from a custom dataset instead.
