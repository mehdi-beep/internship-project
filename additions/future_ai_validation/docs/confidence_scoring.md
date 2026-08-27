# Confidence Scoring Strategy — Design Notes

Detailed design for the scoring approach summarized in `SPECIFICATION.md` Section 8.

## Why per-field, not just one overall number

A single overall confidence score (e.g. "78% confident") hides exactly the
information a human reviewer needs to act efficiently. Two very different situations
could both produce a 78% score:
- Nine fields match perfectly, one (the technical-report free text) doesn't parse
  cleanly from handwriting — genuinely low-stakes, easy to visually verify in seconds.
- The date matches, the client matches, but no signature is detected at all — a much
  more serious finding that a single blended score would understate.

The design therefore always produces **one result per compared field, plus one
overall summary** — never only the summary.

## Proposed field weights (illustrative starting point, to be tuned during Phase 7)

| Field | Relative weight | Reasoning |
|---|---|---|
| Signature presence (Vision) | Highest | The one check most directly tied to "is this a genuinely valid signed document at all" |
| Intervention date | High | A date mismatch is easy to OCR reliably (printed or clearly-formatted) and is a meaningful discrepancy if wrong |
| Client name | High | Easy to fuzzy-match, and a mismatch here could indicate a genuinely wrong attachment |
| Start/end time | Medium | Slightly harder to OCR reliably (handwritten times vary in format) than a date |
| Technician name | Medium | Similar reasoning to client name, slightly lower weight since it's cross-checked against the logged-in session at submission time already (Rule 5) |
| Technical report / free-text notes | Lowest | Hardest to OCR reliably from handwriting, and least likely to indicate an actual problem versus just noisy extraction |

## Proposed scoring formula (illustrative, not final)

```
overall_confidence = Σ (field_weight_i × field_match_score_i) / Σ field_weight_i
```

Where each `field_match_score` is itself a 0.0–1.0 value from the comparison engine
(exact match → close to 1.0; a fuzzy-matched but clearly-the-same value → a bit
lower; a clear mismatch → close to 0.0).

## The three possible states per field, not just "match / mismatch"

1. **Confident match** — extracted value and stored value agree above a threshold.
2. **Confident mismatch** — extracted value and stored value clearly disagree.
3. **Unable to assess** — OCR/Vision confidence for that specific field was itself too
   low to trust the extraction at all (e.g. the relevant region of the photo was
   blurry). This is deliberately a *distinct* state from "mismatch" — an unreadable
   field is not evidence of a discrepancy, and conflating the two would actively
   mislead a reviewer into treating a photo-quality problem as a data-accuracy
   problem.

## Suggested decision thresholds (illustrative, to be tuned)

| Overall confidence | Suggested decision shown to reviewer |
|---|---|
| ≥ 0.90, zero "unable to assess" fields | "Suggested: Approve" |
| 0.60 – 0.89, or any field unable to assess | "Suggested: Review carefully" (with the specific field-level explanations shown) |
| < 0.60 | "Suggested: Review carefully — multiple discrepancies detected" |

Note there is **no threshold that produces an automatic "Suggested: Reject"** — the
design deliberately treats "reject" as a decision only a human should actively reach,
even when the AI's confidence is very low; the system's role at the low end is to
raise attention and explain why, not to pre-judge the outcome.

## Calibration is a real, ongoing concern

These weights and thresholds are starting points, not values validated against real
data. Section 7 of `ROADMAP.md` ("Evaluation and tuning") is explicitly the phase
where these numbers would actually be checked against real reviewer decisions over
time and adjusted — presenting them here as fixed and correct without that real-world
validation would be overstating what a specification document alone can establish.
