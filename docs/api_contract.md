# API Contract (Shipping Mode)

This document defines **minimal contract guardrails** while the project is iterating quickly.

## Intent

- Protect critical frontend/backend integration points.
- Avoid over-constraining active product iteration.
- Keep changes easy for both humans and coding agents.

## Stable (Do Not Break Without Coordination)

### Error envelope shape
All non-2xx API responses should use:

```json
{
  "code": "string",
  "message": "string",
  "details": {}
}
```

`details` may be `null`, object, or list depending on context.

### Core endpoints
- `GET /health`
- `GET /nwi/summary`
- `GET /nwi/summary/by-query`

### Core summary invariants
For `NwiSummaryResponse`:
- `search_radius_miles >= selected_radius_miles`
- `counts.selected_block_groups <= counts.context_block_groups`
- If `nwi.mean`, `nwi.min`, and `nwi.max` are all present, then:
  - `nwi.min <= nwi.mean <= nwi.max`

## Evolving (Safe To Iterate)

- Additional response fields may be added.
- Label text and human-readable messages may be refined.
- Non-core endpoints may be added/removed during internal development.
- Internal implementation details are free to change if stable items above hold.

### Upgrade Potential semantics

`upgrade_potential` is evolving while WAS analytics are internal. Current semantics:
- `mode="nwi_and_was"` means candidates cleared the NWI delta threshold and improved `was_2019` by at least `min_delta_was` points.
- `mode="nwi_only"` means WAS could not be evaluated for the comparison, so candidates use the legacy NWI-only rule and clients should label that fallback explicitly.

## Change Policy (Shipping Mode)

- Small additive changes: proceed directly.
- Breaking stable items: coordinate in PR notes and update tests in the same change.
- No formal versioning gate yet; introduce stricter versioning when external clients depend on the API.
