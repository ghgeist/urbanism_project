---
created: 2026-01-24
updated: 2026-01-24
status: experimental
version: 0.1
origin: topological intuition (shape, boundaries, invariants)
purpose: early structural diagnosis of brittleness
scope: pre-categorical; pre-composition
invocation: optional upstream pass
related:
* napkin-grammar
* compositional-sanity-check
---

# Structural Topology Read

### A lightweight, topology-inspired lens for early structural diagnosis

---

## Purpose

This framework provides a **minimal structural read** for systems, prompts, and frameworks that *feel brittle* or unstable before formal validation or reuse.

It exists to answer one question:

> **What is the shape of the space this system defines?**

### Machine Summary

* Input: a draft system, prompt, or framework
* Output: at most **one** structural shape insight (or none)
* Success condition: a topological issue explains observed brittleness
* Failure condition: no decisive shape insight appears quickly → stop

### Human Summary

Use this read when something feels structurally off but you cannot yet explain why. If nothing important appears within a few minutes, do not continue.

---

## When to Use

Invoke this read:

* **Before** running a compositional or reuse check
* When something works locally but feels fragile or hard to transfer
* When repeated rewrites improve clarity but not stability
* When failures recur despite careful wording

Do **not** use during execution, optimization, or implementation.

---

## What This Is (and Is Not)

**This is:**

* An early, exploratory diagnostic
* A shape-oriented read, not a correctness test
* A way to explain *why* brittleness appears
* A complement to categorical validation

**This is not:**

* A design or construction method
* A checklist for completeness
* A theory of topology
* A replacement for Napkin Grammar or compositional checks
* A gate or approval step

If it becomes procedural, it has failed.

---

## Core Intuition

Any system, prompt, or framework defines a **space of allowed transformations**.

Structural brittleness arises when that space contains:

* hidden boundaries
* forbidden regions
* discontinuities
* disconnected components
* irreducible loops

This read surfaces those features early, before they manifest as downstream failures.

---

## The Read (Five Questions)

Ask these questions informally, while looking at the structure as a whole.
Do not force answers. Stop as soon as a decisive structural insight appears.

### Machine Rule

* Evaluate questions sequentially
* Stop after the first decisive structural finding
* Do not attempt coverage or completeness

---

### 1. Connectedness

**Question:**

> Does this define a single coherent space of intent, or multiple loosely connected ones?

**Signals (Machine / Human):**

* parallel goals that do not constrain each other
* instructions that can be satisfied independently
* outputs that are reasonable but misaligned

**Interpretation:**

Multiple connected components often appear as ambiguity disguised as flexibility.

---

### 2. Boundaries

**Question:**

> Where does behavior qualitatively change?

**Signals (Machine / Human):**

* exploration → execution bleed
* description → judgment bleed
* reflection → solutioning bleed

**Interpretation:**

Unmarked boundaries cause leakage rather than explicit errors.

---

### 3. Holes (Forbidden Regions)

**Question:**

> What paths are implicitly not allowed, even if never stated?

**Signals (Machine / Human):**

* "obviously it shouldn't…"
* reliance on taste, norms, or shared context
* safety or scope assumptions held only by the author

**Interpretation:**

Unmarked holes warp all valid paths through the system.

---

### 4. Discontinuities

**Question:**

> What jumps are treated as smooth transitions?

**Signals (Machine / Human):**

* "and then it understands…"
* silent scope narrowing
* undeclared authority or context shifts

**Interpretation:**

Discontinuities tear meaning under reuse or composition.

---

### 5. Non-Contractible Loops

**Question:**

> What failure pattern keeps reappearing across revisions?

**Signals (Machine / Human):**

* repeated hedging
* analysis spirals
* premature summarization
* re-asking the same clarification

**Interpretation:**

If it survives rewrites, the issue is structural, not linguistic.

---

## Output Rule

If a topological issue is identified:

> **Do not refine wording.**
> Change structure, clarify boundaries, or stop.

If no structural issue appears quickly, end the read.

---

## Relationship to Other Frameworks

* **Napkin Grammar** → surfaces elements and relations
* **Structural Topology Read** → interprets structural shape
* **Compositional Sanity Check** → validates composability

Each answers a different question.
None replace the others.

---

## Usage Guidance

* Run in under 5 minutes
* One insight is sufficient
* Stop early when structure appears
* Preserve artifacts as evidence, not deliverables

This read is successful when it prevents unnecessary refinement or explains recurring brittleness.

---
