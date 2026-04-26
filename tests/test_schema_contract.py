"""Contract test: Pydantic schemas in ``api/schemas.py`` match the TypeScript
types in ``frontend/src/types/api.ts``.

This is the cheapest insurance against the Playwright mocks in
``frontend/e2e/*.spec.ts`` going stale when the backend adds, removes,
or renames a field. The Playwright mocks fabricate NwiSummaryResponse
payloads by hand, so neither `mypy`/TS nor Pydantic can catch a drift
between server and mock without an explicit cross-language check.

Strategy:

1. Walk every Pydantic model declared in ``api.schemas``.
2. Parse ``frontend/src/types/api.ts`` (regex-based, no TS tooling) to
   collect the field names declared on each exported interface, plus the
   literal values declared on exported string-literal unions.
3. For each Pydantic model whose name maps to a TS interface, assert that
   the field-name sets are equal. For each Pydantic ``Literal[...]`` field,
   assert the TS string-literal union has the same members.

We deliberately do NOT compare types in depth — TS `string | null` vs
Pydantic ``str | None`` differs by syntax, and a proper JSON-Schema-vs-TS
check is over-engineered for a single-digit number of interfaces.
Field-name drift is by far the most common mock-staleness bug in practice.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic import BaseModel

from api import schemas as api_schemas
from api.schemas import AmenityRichnessLabel, HollowNeighborhoodLabel, UpgradePotentialMode

TYPES_TS_PATH = Path(__file__).parent.parent / "frontend" / "src" / "types" / "api.ts"

# Models exported by api.schemas that do NOT have a matching TS interface.
# Keep this short and documented; prefer adding the TS type when practical.
_PYDANTIC_MODELS_WITHOUT_TS_COUNTERPART: set[str] = {
    # /health returns ``{"status": "ok"}`` and the frontend only inspects
    # ``response.ok``, so no dedicated TS interface is needed.
    "HealthResponse",
}

# Pydantic Literal -> TS string-literal-union pairs. Add both sides any
# time a new enum-like union is introduced in the API schemas.
_LITERAL_PAIRS: list[tuple[str, Any]] = [
    ("AmenityRichnessLabel", AmenityRichnessLabel),
    ("HollowNeighborhoodLabel", HollowNeighborhoodLabel),
    ("UpgradePotentialMode", UpgradePotentialMode),
]


def _extract_ts_interface_fields(source: str) -> dict[str, set[str]]:
    """Return ``{interface_name: {field_name, ...}}`` for every exported interface.

    Handles the conventional one-field-per-line format of ``api.ts``. Fields
    like ``foo?: Bar | null;`` and ``foo: Bar[];`` both yield ``"foo"``.
    """
    interfaces: dict[str, set[str]] = {}
    # Non-greedy match across lines for each interface body.
    for match in re.finditer(
        r"export\s+interface\s+(\w+)\s*\{([^}]*)\}",
        source,
        flags=re.DOTALL,
    ):
        name, body = match.group(1), match.group(2)
        fields: set[str] = set()
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
                continue
            # Match "fieldName?: ..." — strip everything from the colon onward.
            field_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\??\s*:", line)
            if field_match:
                fields.add(field_match.group(1))
        interfaces[name] = fields
    return interfaces


def _extract_ts_literal_union(source: str, name: str) -> set[str] | None:
    """Return the literal string values of ``export type Name = "a" | "b";``.

    Returns ``None`` when the union is not declared (caller decides how to
    fail). Uses a non-greedy match up to the trailing semicolon so
    multi-line unions are captured.
    """
    match = re.search(
        rf"export\s+type\s+{re.escape(name)}\s*=\s*([^;]+);",
        source,
        flags=re.DOTALL,
    )
    if not match:
        return None
    body = match.group(1)
    return set(re.findall(r'"([^"]+)"', body))


def _pydantic_models_in_module(module: Any) -> dict[str, type[BaseModel]]:
    """Return ``{ClassName: PydanticModel}`` for all BaseModel subclasses in a module."""
    models: dict[str, type[BaseModel]] = {}
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj is BaseModel:
            continue
        if not issubclass(obj, BaseModel):
            continue
        if obj.__module__ != module.__name__:
            # Imported but not defined here; skip.
            continue
        models[name] = obj
    return models


def test_pydantic_models_have_matching_ts_interfaces():
    """Every Pydantic model in api/schemas.py has a TS interface with matching fields."""
    source = TYPES_TS_PATH.read_text()
    ts_interfaces = _extract_ts_interface_fields(source)
    pydantic_models = _pydantic_models_in_module(api_schemas)

    assert pydantic_models, "api.schemas has no BaseModel classes — did the import break?"
    assert ts_interfaces, f"Could not parse any TS interfaces from {TYPES_TS_PATH}"

    errors: list[str] = []
    for py_name, model in pydantic_models.items():
        if py_name in _PYDANTIC_MODELS_WITHOUT_TS_COUNTERPART:
            continue
        if py_name not in ts_interfaces:
            errors.append(
                f"Pydantic model '{py_name}' has no matching TS interface "
                f"in {TYPES_TS_PATH.name}. Add it there or to "
                f"_PYDANTIC_MODELS_WITHOUT_TS_COUNTERPART with a comment."
            )
            continue

        py_fields = set(model.model_fields.keys())
        ts_fields = ts_interfaces[py_name]
        if py_fields != ts_fields:
            only_py = sorted(py_fields - ts_fields)
            only_ts = sorted(ts_fields - py_fields)
            parts = [f"{py_name}: field set mismatch."]
            if only_py:
                parts.append(f"Missing from TS: {only_py}.")
            if only_ts:
                parts.append(f"Missing from Python: {only_ts}.")
            errors.append(" ".join(parts))

    assert not errors, (
        "Backend Pydantic schemas have drifted from frontend TS types:\n  - "
        + "\n  - ".join(errors)
    )


def test_ts_interfaces_have_matching_pydantic_models():
    """Every exported TS interface should have a matching Pydantic model.

    Extra TS interfaces without a backend counterpart either indicate
    dead frontend code or a missing server-side model — both worth a
    human look.
    """
    source = TYPES_TS_PATH.read_text()
    ts_interfaces = _extract_ts_interface_fields(source)
    pydantic_models = _pydantic_models_in_module(api_schemas)

    extras = sorted(set(ts_interfaces.keys()) - set(pydantic_models.keys()))
    assert not extras, (
        f"TS interfaces without a matching Pydantic model in api.schemas: {extras}. "
        "Either add the Pydantic model, remove the TS interface, or document "
        "the intentional divergence."
    )


def test_literal_unions_agree():
    """``Literal[...]`` string members in Python match the TS string-literal union."""
    source = TYPES_TS_PATH.read_text()
    errors: list[str] = []
    for ts_name, py_literal in _LITERAL_PAIRS:
        ts_members = _extract_ts_literal_union(source, ts_name)
        if ts_members is None:
            errors.append(f"TS type '{ts_name}' not found in {TYPES_TS_PATH.name}.")
            continue
        # Literal[...] exposes its members via typing.get_args; fall back
        # to raw __args__ for older Python versions.
        args = get_args(py_literal)
        if not args and get_origin(py_literal) is None:
            errors.append(f"Pydantic '{ts_name}' is not a Literal/Union of str.")
            continue
        py_members = {a for a in args if isinstance(a, str)}
        if py_members != ts_members:
            only_py = sorted(py_members - ts_members)
            only_ts = sorted(ts_members - py_members)
            parts = [f"{ts_name}: literal values differ."]
            if only_py:
                parts.append(f"Missing from TS: {only_py}.")
            if only_ts:
                parts.append(f"Missing from Python: {only_ts}.")
            errors.append(" ".join(parts))

    assert not errors, "Literal unions have drifted:\n  - " + "\n  - ".join(errors)
