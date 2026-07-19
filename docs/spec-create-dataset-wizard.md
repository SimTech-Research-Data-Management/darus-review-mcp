# Spec: DaRUS Create-Dataset Card Wizard (MCP)

## Objective

Let a scientist create a publishable **draft** dataset on DaRUS through an
MCP-driven, schema-aware **card wizard** — instead of hand-filling DaRUS's
90-field web form or authoring raw Dataverse native JSON.

- **User:** a researcher (e.g. depositing paper data) using an MCP client (Claude Desktop) connected to the `darus-mcp` server.
- **Success:** from a single card the user creates a valid DaRUS draft (title, description, subject, one author, one contact); additional metadata is added incrementally through later cards, each an idempotent upsert onto the same draft. The wizard never publishes.

Non-goals (v1): publishing, file upload, discipline metadata blocks (EngMeta/enzymeML/etc.), edit/delete of published datasets, multi-dataverse.

## Tech Stack

- **pyDataverse** (local editable, branch `dev`) — Dataverse API client + `pyDataverse.mcp` server. Python ≥3.12, pydantic v2, fastmcp `2.14.5`.
- **darus-review-mcp** (branch `dev`) — deployment wrapper + wizard/cards. fastmcp, `python-dotenv`.
- FastMCP **FormInput** app provider (needs fastmcp `≥3.2.0` — see Open Questions) for rendered cards; conversational fallback otherwise.
- Auth: `API_TOKEN` env → the connected `Dataverse` instance writes as the user.

## Commands

```
# darus-review-mcp
Test:   uv run python test_darus.py
Sync:   uv sync
Serve:  uv run fastmcp dev main.py        # MCP Inspector, click tools by hand

# pyDataverse
Test:   ./run-tests.sh          (or: uv run pytest tests/ -q)

# live loop: edit source → tests re-import (editable) → for Desktop, ⌘Q + relaunch
```

## Project Structure

```
pyDataverse/pyDataverse/
  dataverse/dataverse.py   → Dataverse facade: create_dataset(), (add) upsert_metadata()
  api/native.py            → create_dataset, edit_dataset_metadata (replace=)
  mcp/dataset.py           → MCP tool fns: get_dataset, list_files, create_dataset, (add) upsert_dataset_metadata
  mcp/server.py            → tool registration + MCPConfiguration (dataset=["read","create"])

darus-review-mcp/
  main.py                  → server assembly + opt-in config
  wizard/ (new)            → card models + sequencing (FormInput app / conversational)
  test_darus.py            → registration + schema + wizard tests
  docs/spec-create-dataset-wizard.md
```

## Code Style

Match existing pyDataverse MCP tools: flat, `Annotated` params with inline
descriptions, return `encode(...)` (TOON), pull the connection via
`ensure_dataverse(ctx)` (no `base_url` override on writes).

```python
def upsert_dataset_metadata(
    identifier: Annotated[str, "PID of the draft dataset to update."],
    fields: Annotated[Dict[str, Any], "Complete values for exactly the fields this card owns."],
    ctx: Context = CurrentContext(),
):
    """Replace this card's fields on a draft (idempotent). Draft only."""
    dv = ensure_dataverse(ctx)
    ds = dv.native_api.edit_dataset_metadata(identifier, fields, replace=True)
    return encode({"persistent_id": ds.dataset_persistent_id})
```

## Card Model

Cards own **disjoint** top-level citation fields, so each upsert replaces only its own.

| Card | Fields | Gate |
|---|---|---|
| **1. Basics** | title\*, description\*, subject\* (dropdown), author[0] {name\*, affiliation}, contact[0] {name, email\*} | required — creates the draft |
| 2. People | full author[] + contact[] list editor (add / edit-by-index / remove) | optional |
| 3. Keywords & Classification | keyword, topicClassification, language, kindOfData | optional |
| 4. Related work | publication, relatedMaterial, relatedDataset, otherReferences, dataSources | optional |
| 5. Funding & Project | project, grantNumber | optional |
| 6. Coverage & Provenance | timePeriodCovered, dateOfCollection, productionDate/Place, series, software, storage | optional |

Repeatable-entity editing (People) = reuse one entry model, addressable by
index; the card always resends the **complete** list with `replace=True`.

## Testing Strategy

- No-framework runnable tests in `test_darus.py` (existing convention).
- **Never create live datasets in automated tests.** Assert registration + input schema only.
- Live create/upsert = **manual**, against a sandbox collection, gated behind an explicit run.
- One live smoke (manual): create draft via Card 1 → upsert People → confirm field-scoped replace didn't clobber Card 1, and re-running a card is idempotent (no duplicate authors).

## Boundaries

- **Always:** draft-only writes; `replace=True` scoped to a card's own fields; resend complete field values; run `test_darus.py` before commit; keep both repos on `dev`, local only.
- **Ask first:** publishing, file upload, `delete_dataset` (discard), adding a dependency (e.g. bumping fastmcp to ≥3.2 for FormInput), touching production collections.
- **Never:** auto-publish; push to upstream; create datasets from within automated tests; commit `API_TOKEN`.

## Success Criteria

1. Card 1 alone creates a valid DaRUS draft and returns its PID + URL.
2. A later card (People) upserts via `edit_dataset_metadata(replace=True)` **without** clobbering or duplicating Card 1's fields.
3. Re-submitting any card is idempotent (verified: no duplicate authors after two submits).
4. Wizard never issues a publish call.
5. `test_darus.py` green (registration + schemas for both `Create_Dataset` and the upsert tool).
6. Verified manually against a sandbox collection.

## Resolved Decisions

1. **v1 is conversational-only.** FormInput needs fastmcp ≥3.2.0, but pyDataverse pins `<3.0.0`. Cards would require moving the whole library onto a new fastmcp major — out of v1 scope. v1: pyDataverse exposes `Create_Dataset` + `upsert_dataset_metadata`; the model sequences the cards in dialogue.
2. **All metadata logic lives in pyDataverse.** Schema is governed by the DaRUS *server* (fetched live); pyDataverse is the generic client that maps it to native JSON. darus-review-mcp stays a thin app (deployment, token, opt-in config) with zero metadata logic. Nothing is DaRUS-specific.

## Open Questions

1. **`edit_dataset_metadata(replace=True)` scope** — confirm field-scoped (not whole-record) against draft `doi:10.18419/DARUS-6325` (needs `API_TOKEN`). Blocks Success Criteria #2.
2. **Parent collection alias** for live create tests (DARUS-6325 is a dataset DOI, not a collection — still need the collection to create drafts into).
