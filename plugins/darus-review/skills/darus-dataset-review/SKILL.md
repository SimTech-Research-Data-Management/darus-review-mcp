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

Turn a DaRUS dataset into grounded review feedback by pulling its actual
metadata, files, and tabular schemas through the `darus-mcp` tools and checking
them against a rubric distilled from DaRUS/FoKUS curation guidance, EngMeta, and
FAIR. The value is that findings are **evidence-based** — every issue points at a
specific metadata field, file, or column, not a vibe.

The single most important thing a reviewer catches that automated validators
miss is **internal inconsistency**: the description promises variables the tables
don't contain, EngMeta lists a parameter no file records, a column is typed
numeric but holds text. Keep that cross-checking front of mind.

## Prerequisites

- The `darus-mcp` MCP server must be connected (tools appear as
  `Search_Dataverse`, `Get_Dataset_Metadata`, `List_Files_in_Dataset`,
  `Get_Tabular_File_Schema`, `Read_Tabular_File`, `Read_File_Content`, …).
- Restricted or draft datasets need a valid `API_TOKEN` on the server. If a call
  returns nothing for a dataset the user says exists, suspect an access/token
  issue rather than an empty dataset, and say so.

## Workflow

Work in this order — cheap, broad evidence first, then drill into files only
where the metadata gives you something to check against.

1. **Locate the dataset.** If the user gave a DOI/PID (e.g.
   `doi:10.18419/darus-XXXX`), use it directly. Otherwise `Search_Dataverse`
   to find it and confirm the match with the user before reviewing.

2. **Pull the full metadata.** `Get_Dataset_Metadata` for the complete record
   (citation block + any discipline blocks like EngMeta, process, enzymeML). This
   is the backbone — most criteria are checked here. Read the description text
   carefully; you'll cross-reference it against files and schemas later.

3. **List the files.** `List_Files_in_Dataset`. Note file roles/tags,
   per-file descriptions, directory structure, formats, and whether a README or
   documentation file exists.

4. **Inspect tabular data where it matters.** For each tabular file relevant to
   the review, `Get_Tabular_File_Schema` for columns/types, and
   `Read_Tabular_File` for a small **sample** (not the whole file — reads can be
   large) to check that values actually match their declared types and that
   documented missing-data codes appear as described.

5. **Read the documentation.** If a README/codebook exists,
   `Read_File_Content` on it, so you can check column definitions, units, and
   missing-data codes against the real schema.

6. **If the dataset contains code/software, check it can actually be run.** Data
   without runnable analysis code is only half-reproducible. When you see scripts
   or source files (`.py`, `.R`, `.jl`, `.m`, `.ipynb`, `.sh`, `.cpp`, …),
   `Read_File_Content` on the dependency and instruction files and verify the
   record answers "what do I install, and how do I run this?". See rubric
   section 7 for the full checklist; the essentials are a **dependency manifest**
   (Python: `pyproject.toml` / `uv.lock` / `requirements.txt` / `environment.yml`;
   and the equivalents for other languages) and **execution instructions** (a
   README saying how to run it, with the entry point named).

7. **Cross-check and score** against `references/rubric.md`. Load that file now —
   it is the authoritative criteria list, each tied to the evidence that confirms
   or violates it, with source citations and confidence caveats.

Only pull as much file/table detail as the review needs. A completeness check of
citation metadata doesn't require reading every CSV; a "do the tables match the
description" check does.

## The consistency checks that matter most

These are the cross-tool checks a rubric-by-itself won't make for you. Always run
the ones whose inputs exist:

- **Description ↔ files**: every file/table named in the description exists in
  the file list, and no substantive file is left undocumented.
- **Description ↔ tabular schema**: variables/quantities named in the prose
  appear as real columns (and vice versa).
- **EngMeta ↔ data**: discipline metadata (measured/controlled variables, system
  parameters, resolution) is reflected in the actual files/columns.
- **Schema ↔ values**: column types match sampled values; declared units and
  missing-data codes are consistent with what's in the README and the data.
- **Code ↔ dependencies ↔ instructions**: if scripts are present, their imports
  are covered by a declared dependency manifest, and a reader is told how to
  install and run them (see rubric section 7).

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
The cross-checks above that failed, each with the two pieces of evidence that
disagree.

## Recommended fixes
Ordered, concrete, and actionable — what to add/change and where.
```

Grounding rules that keep the review trustworthy:

- **Cite the evidence.** Every finding names the metadata field, file, or column
  it's based on. "Description is vague" is useless; "Description (3 sentences)
  states no method or software; violates rubric 2.1" is a finding.
- **Distinguish blocking from cosmetic.** A missing Contact email or DOI is a
  hard gate; a missing per-file description is a polish item. Say which.
- **Don't invent requirements.** The rubric flags a few lower-confidence and one
  refuted criterion (see the caveats in `references/rubric.md`) — respect those
  labels and don't present encouraged practices as mandates.
- **Applicability first.** EngMeta discipline/process criteria apply to
  computational-science/engineering datasets. For a pure tabular-survey dataset,
  note them as not-applicable rather than failing them.
