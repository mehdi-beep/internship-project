# Isolation Confirmation

This file exists so the isolation claim made throughout this folder is **verifiable**,
not just asserted.

## What "isolated" means here, precisely

1. **Nothing in `backend/` or `frontend/` (the real application) imports anything from
   this folder.** You can confirm this yourself at any time:
   ```bash
   grep -r "future_ai_validation" backend/ frontend/
   ```
   This should return **zero results**. If it ever returns a result, something has
   been wired in that shouldn't be — that's the exact signal to look for.

2. **Nothing in this folder is imported anywhere else either.** Every Python-like
   file in `backend/` and every TypeScript-like file in `frontend/components/` here
   uses a non-executable extension (`.py.example`, `.tsx.example`) specifically so
   that:
   - Python's import system cannot import them (`import x` requires a real `.py`
     file).
   - The frontend's TypeScript compiler and bundler (Vite) cannot pick them up as
     real source files, even if this folder were accidentally left inside a
     directory the build tooling scans.

3. **No router from this folder is registered in `backend/main.py`.** The real
   application's router registration is a fixed, explicit list —
   `app.include_router(health.router, ...)`, `app.include_router(auth.router, ...)`,
   and so on, all the way through every real feature. You can confirm nothing from
   this folder appears in that list:
   ```bash
   grep -n "include_router" backend/main.py
   ```
   Every line in that output references a router from `backend/app/api/`, never from
   `future_ai_validation/`.

4. **No route from this folder appears anywhere in `frontend/src/App.tsx`'s route
   table.** The real application's routes are a fixed, explicit list, exactly as
   documented in `ARCHITECTURE.md`. Nothing here is added to it.

5. **Nothing in this folder was pushed to GitHub as part of this task**, per the
   explicit instruction not to push anything. It exists only in the local working
   copy at the time of writing.

## What would need to happen for this to ever become "live"

Per the Integration Plan in `SPECIFICATION.md` (Section 11), turning any of this from
a specification into working, integrated code would require a person to deliberately:
- Write real, executable code (rename or rewrite the `.example` files into real
  `.py`/`.tsx` files).
- Deploy it as its own separate service (per the architecture described).
- Explicitly add one new button to `InterventionReviewViewer.tsx` that calls that
  separate service.

None of those four things have been done. This folder, as it stands right now, is
documentation and illustrative placeholders only.
