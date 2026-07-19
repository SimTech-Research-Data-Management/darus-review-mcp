# Implementation Plan: DaRUS Create-Dataset Card Wizard (v1, conversational)

Spec: [spec-create-dataset-wizard.md](./spec-create-dataset-wizard.md)

## Overview

v1 delivers the create-early + per-card-upsert flow as **conversational** MCP
tools (no FormInput — barred by pyDataverse's `fastmcp<3.0.0` cap). Card 1
(create) already ships as `Create_Dataset`. The new work is the **upsert tool**
for later cards, gated behind live confirmation that `replace=True` is
field-scoped. All metadata logic stays in pyDataverse; darus only opts in.

## Architecture Decisions

- **Reuse `Create_Dataset` for Card 1.** Single inline author/contact = one-element lists the model passes. No new create code.
- **One generic `upsert_dataset_metadata` tool** for all later cards, wrapping `edit_dataset_metadata(replace=True)`. Cards own disjoint fields → replace is safe + idempotent. Full-value resend, no deltas.
- **Conversational sequencing.** No wizard state machine; card order lives in a guidance prompt + tool descriptions. The model drives create → upsert.
- **Logic in pyDataverse `mcp/`; darus stays thin.**

## Dependency Graph

```
Task 1 (spike: verify replace scope)  ← gates everything
        │
        ▼
Task 2 (upsert tool in pyDataverse) ──┬── Task 3 (darus opt-in)
        │                             └── Task 4 (card-order guidance)  [parallel]
        ▼
Task 5 (tests) ──▶ Task 6 (live end-to-end smoke)
```

## Task List

### Phase 1: De-risk + Foundation

## Task 1: Verify `replace=True` is field-scoped (spike)

**Description:** Before building on it, confirm on a live draft that `edit_dataset_metadata(replace=True)` replaces only the fields sent — not the whole record — and is idempotent. This is the load-bearing assumption of the whole upsert design; fail fast.

**Acceptance criteria:**
- [ ] Editing field A on draft `doi:10.18419/DARUS-6325` leaves an untouched field B intact.
- [ ] Editing a multi-value field (e.g. `keyword`) with a full list twice yields no duplicates.

**Verification:**
- [ ] Manual script (scratchpad, not committed) using `API_TOKEN`; before/after `Get_Dataset_Metadata` diff shows only the targeted field changed.

**Dependencies:** None (needs `API_TOKEN` + the draft DOI).
**Files likely touched:** scratchpad only.
**Scope:** S

## Task 2: `upsert_dataset_metadata` MCP tool (pyDataverse)

**Description:** Add a facade method + MCP tool that takes a draft PID and a card's field values and applies them via `edit_dataset_metadata(replace=True)`. Generic over citation fields; native-format passthrough for anything the friendly layer doesn't cover. Gate on a new `"edit"` config value.

**Acceptance criteria:**
- [ ] `dataset` config Literal gains `"edit"`; tool registered `enabled="edit" in config.dataset`.
- [ ] Tool takes `identifier` + card field values, returns updated PID; uses `ensure_dataverse(ctx)` (no `base_url`).
- [ ] Does not publish; draft-only.

**Verification:**
- [ ] `uv run pytest tests/ -q` (pyDataverse) green.
- [ ] In-process: tool registers when `dataset=["read","create","edit"]`.

**Dependencies:** Task 1.
**Files likely touched:** `dataverse/dataverse.py`, `mcp/dataset.py`, `mcp/server.py`.
**Scope:** M

### Checkpoint: Foundation
- [ ] Task 1 confirms replace scope (or design revised). Task 2 tests green.

### Phase 2: Wire + Guide

## Task 3: darus opt-in for edit

**Description:** Flip darus `main.py` to `MCPConfiguration(dataset=["read","create","edit"])`.

**Acceptance criteria:**
- [ ] `upsert_dataset_metadata` served by the darus app (14 tools).

**Verification:**
- [ ] `uv run python test_darus.py` green with updated count + name assertion.

**Dependencies:** Task 2.
**Files likely touched:** `main.py`, `test_darus.py`.
**Scope:** S

## Task 4: Card-order guidance

**Description:** Encode the card sequence (Basics → People → Keywords → Related → Funding → Coverage) and the create-early/upsert rules so the model sequences correctly. Via an MCP prompt/resource or enriched tool descriptions — minimal, no state machine.

**Acceptance criteria:**
- [ ] The model, told "help me deposit a dataset," creates via Card 1 then offers later cards in order, upserting each.

**Verification:**
- [ ] Manual dialogue in `fastmcp dev` / Desktop: create → add People → add Keywords, drafts reflect each.

**Dependencies:** Task 2 (can draft text in parallel).
**Files likely touched:** `mcp/server.py` (prompt/descriptions) or a small guidance resource.
**Scope:** S

### Phase 3: Verify

## Task 5: Tests

**Description:** Registration + input-schema tests for `upsert_dataset_metadata`; update served-tool count.

**Acceptance criteria:**
- [ ] Test asserts upsert tool served + required params (`identifier` + fields).
- [ ] No test creates a live dataset.

**Verification:** `uv run python test_darus.py` green.
**Dependencies:** Task 3.
**Files likely touched:** `test_darus.py`.
**Scope:** S

## Task 6: Live end-to-end smoke (manual)

**Description:** Against a **sandbox collection** (alias TBD — open question): Card 1 create → People upsert → Keywords upsert; confirm Success Criteria #2/#3 (no clobber, no dup, no publish).

**Acceptance criteria:**
- [ ] Draft created from Card 1 returns PID + URL.
- [ ] People upsert doesn't clobber Basics; re-run adds no duplicate authors.
- [ ] No publish call issued.

**Verification:** Manual, `Get_Dataset_Metadata` diffs between steps.
**Dependencies:** Tasks 3–5 + collection alias.
**Files likely touched:** scratchpad only.
**Scope:** S

### Checkpoint: Complete
- [ ] All success criteria met; both repos green on `dev`; ready for review.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `replace=True` is whole-record, not field-scoped | High | Task 1 spike first; if so, switch to fetch-merge-replace-full-block |
| No parent collection alias for create tests | Med | Open question; upsert path testable on DARUS-6325 meanwhile |
| Friendly→native mapping for later-card fields balloons | Med | v1 keeps upsert generic/native-passthrough; friendly per-card wrappers deferred |
| Conversational sequencing drifts | Low | Task 4 guidance; acceptable for v1, FormInput cards are the eventual fix |

## Open Questions

- Parent **collection alias** for live create tests (Task 6)?
- Confirm `API_TOKEN` in env has write rights on DARUS-6325 (Task 1)?
