---
created: 2026-01-23
updated: 2026-01-23
status: experimental
version: 0.2
origin: category-theoretic intuition (composition, identity, structure-preserving maps)
purpose: structural sanity check for system composition
scope: post-hoc validation; not a design or optimization tool
invocation: system check
related:
  - napkin-grammar
  - operational-hamming-layer
---

# Compositional Sanity Check

### A lightweight category-theoretic lens for validating system coherence

---

## Purpose

This framework provides a **minimal structural sanity check** for systems, prompts, and no‑code AI agents.

It is **not** a design method, optimization tool, or formal theory.
Its sole function is to answer one question:

> **Is this system composable without reinterpretation?**

If the answer is no, the system is considered *malformed*, regardless of how clever or effective it appears locally.

---

## When to Use

Invoke this check:

* **After** a system or prompt is drafted
* **Before** scaling, reuse, or delegation
* When something "works" but feels brittle or hard to transfer

Do **not** use during early ideation or creative exploration.

---

## What This Is (and Is Not)

**This is:**

* A negative test (linting, not construction)
* A guardrail against hidden coupling and meaning drift
* A way to keep human–AI systems legible under composition

**This is not:**

* Category theory education
* A correctness proof
* A replacement for Hamming, napkin math, or decision logic
* A formal requirement

---

## Core Principle

> **Structure must survive composition.**

If meaning must be re‑explained at every step, the system is not well‑formed.

---

## The Five Checks

### 1. Object Stability

**Question:**

> Can I name the *things* in this system without reference to their internal workings?

Objects may be:

* agents
* contexts
* modes
* documents
* projects

**Fail signal:**

* An object only makes sense once you explain how it works internally

---

### 2. Explicit Transformations

**Question:**

> When moving from A → B, can I state what is preserved and what is transformed?

Transformations may include:

* routing
* summarization
* constraint narrowing
* state changes

**Fail signal:**

* Transitions described as "and then" or "the system understands"

---

### 3. Compositional Integrity

**Question:**

> If I compose A → B → C, does the meaning of A survive without reinterpretation?

Composition should:

* preserve intent
* avoid silent scope changes
* not require re‑negotiating assumptions

**Fail signal:**

* Meaning has to be re‑explained or corrected at each step

---

### 4. Identity / No‑Op Validity

**Question:**

> Is there a valid state where *nothing changes* and meaning is preserved?

Examples:

* stabilization
* holding
* incubation
* pause / defer

**Fail signal:**

* Every step must transform or optimize something

---

### 5. Intent‑Preserving Mapping

**Question:**

> When I reuse this structure in a new context, does intent remain stable?

This check applies when:

* moving across domains
* reusing prompts
* delegating to another human or AI

**Fail signal:**

* The same structure produces qualitatively different intent without explicit modification

---

## Interpretation Rules

* Failing **one** check does not invalidate a system
* Failing **multiple** checks indicates structural fragility
* Passing all checks does **not** imply optimality

This framework flags *coherence*, not quality.

### Topological Failure Note (Interpretive)

Some compositional failures are *topological rather than categorical*. In these cases, objects and transformations may appear well-defined locally, yet composition fails because the underlying structure contains hidden boundaries, discontinuities, holes (forbidden regions), or disconnected components. When multiple checks fail together or failures recur across revisions, the issue is often structural shape rather than transformation precision. In such cases, repairing composition requires reshaping structure or clarifying boundaries, not refining individual transformations.

---

## Human–AI Readability & Modularity (Design Constraint)

This check assumes that system components are designed to be legible to **both humans and AI models**.

**Human–AI readability**

* Each object should be understandable when read in isolation
* Meaning should survive rereading without relying on author memory
* Ambiguity should be intentional and bounded, not accidental

**Modularity**

* Components should be movable without semantic breakage
* Context should narrow interpretation, not redefine it
* Local changes should not require global reinterpretation

Poor readability or weak modularity often appears downstream as failed composition.

---

## Relationship to Other Frameworks

* **Napkin Grammar** → surfaces structure
* **Hamming** → tests feasibility and failure
* **Algorithms** → guide decisions under uncertainty
* **This check** → validates compositional well‑formedness

Each operates independently.

---

## Usage Guidance

* Run in under 5 minutes
* One sentence per check is sufficient
* If something fails, **rewrite structure**, not content

Do not add structure solely to pass the check.

---
