---
name: darus-dataset-review
description: >-
  Review a DaRUS (or any Dataverse) research dataset for quality, FAIR
  compliance, and internal consistency between its metadata, human-readable
  description, and data files/tables. Use this whenever the user wants to
  review, audit, quality-check, curate, or assess a DaRUS/Dataverse dataset;
  check whether a dataset's metadata is complete; verify that a description
  matches its files or tabular columns; evaluate EngMeta / discipline metadata
  for computational-science and engineering data; check whether a dataset that
  ships code is reproducible (dependencies declared, run instructions given); or
  judge whether a dataset meets University of Stuttgart / SimTech / FoKUS RDM and
  FAIR best practices — even if they don't say the word "review". Requires the
  darus-mcp MCP server.
---

# DaRUS Dataset Review

## What this does

Review a DaRUS dataset by pulling its real metadata, files, and tabular schemas
via `darus-mcp` and checking them against `references/rubric.md`. Every finding
must point at a specific field, file, or column.

Prioritise **internal inconsistency** — what automated validators miss: the
description promises variables the tables lack, EngMeta names a parameter no file
records, a column typed numeric holds text.

## Prerequisites

The `darus-mcp` MCP server must be connected (tools appear as `Search_Dataverse`, `Get_Dataset_Metadata`, `List_Files_in_Dataset`, `Get_Tabular_File_Schema`, `Read_Tabular_File`, `Read_File_Content`, ...).

## Workflow

Work in this order — cheap, broad evidence first, then drill into files only
where the metadata gives you something to check against.

1. **Load `references/rubric.md`.** It is the authoritative criteria list and
   defines what each later step needs to collect and when a section applies.

2. **Locate the dataset.** If the user gave a DOI/PID (e.g.
   `doi:10.18419/darus-XXXX`), use it directly. Otherwise `Search_Dataverse`
   to find it and confirm the match with the user before reviewing.

3. **Pull the full metadata.** `Get_Dataset_Metadata` for the complete record
   (citation block + any discipline blocks like EngMeta, process, enzymeML). This
   is the backbone — most criteria are checked here. Read the description text
   carefully; you'll cross-reference it against files and schemas later.

4. **List the files.** `List_Files_in_Dataset`. Note file roles/tags,
   per-file descriptions, directory structure, formats, and whether a README or
   documentation file exists.

5. **Inspect tabular data where it matters.** For each tabular file relevant to
   the review, `Get_Tabular_File_Schema` for columns/types, and
   `Read_Tabular_File` for a small **sample** (not the whole file — reads can be
   large).

6. **Read the documentation** — the description, any README/codebook
   (`Read_File_Content`), and per-file descriptions. Read every surface that
   exists.

7. **If the dataset ships code, read it.** `Read_File_Content` on the dependency
   and instruction files so section 7 can be scored.

8. **Cross-check and score.** Run every criterion whose inputs exist. The rows
   whose Evidence column contains `↔` are cross-tool checks; they are what
   automated validators miss, so they usually carry the highest-value findings.

Only pull as much file/table detail as the review needs. A completeness check of
citation metadata doesn't require reading every CSV; a "do the tables match the
description" check does.

## Reporting the review

Lead with a verdict, then per-dimension findings, then concrete fixes. Use this
structure:

```
# Review: <dataset title> (<DOI>)

**Overall:** <one-line verdict — e.g. "Publishable; 2 blocking, 3 minor issues">

## Findings by dimension
For each rubric dimension, a short status line and only the notable items:
- ✅ Pass / ⚠️ Weak / ❌ Fail — <criterion> — <evidence: field/file/column> — <what's wrong>

## Consistency issues
Failed `↔` criteria, each with the two pieces of evidence that disagree.

## Recommended fixes
Ordered, concrete, and actionable — what to add/change and where.
```

Grounding rules that keep the review trustworthy:

- **Cite the evidence.** Every finding names the metadata field, file, or column
  it's based on. "Description is vague" is useless; "Description (3 sentences)
  states no method or software; violates rubric 2.1" is a finding.
- **Distinguish blocking from cosmetic.** Say which, per the rubric's section 1
  hard gate.
- **Obey the rubric's own limits** — its applicability and confidence-caveat
  rules (sections 3, 7, 9) decide what to mark N/A and what not to enforce. Don't
  restate or override them here.
