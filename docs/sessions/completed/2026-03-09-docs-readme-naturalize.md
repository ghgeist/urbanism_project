---
created: 2026-03-09
---
# README tone and accuracy pass

## Objective
Review `README.md` for templated or over-produced language, then rewrite the high-friction sections so it reads like a maintained project document rather than generated marketing copy.

## Success Criteria
- Remove obvious "AI-smell" from intros, highlights, contributing, and testing copy.
- Tighten setup and usage sections so they are more direct and easier to skim.
- Correct any factual mismatches discovered during the review.

## Progress Log
- Checked active sessions and confirmed no existing README-focused session was in progress.
- Reviewed `README.md` and flagged tone issues, repeated emphasis, and a few claims to verify against the codebase.
- Verified current routes in `frontend/src/App.tsx` and geocoding behavior in `services/walkability.py`.
- Verified database configuration supports both `PG*` variables and `DATABASE_URL` in `services/db.py`.
- Rewrote the README introduction, overview, quickstart, testing, deployment, and contributing sections to use plainer language and less template-like structure.
- Removed the unused table of contents, which also eliminated a stale `Roadmap` entry that no longer had a matching section.
- Added the `service_unavailable` API error to the documented error list so the README matches the current backend behavior.

## Outcome
- `README.md` now reads more like project documentation and less like generated portfolio copy.
- No lint diagnostics were reported for the edited files.
