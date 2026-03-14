# Integration Notes

## Purpose

This document describes the minimum real integration points between Jigsaw and the existing Garbage Collector and Arbiter systems.

It also records how the shared `kernel.v1` contract maps into Jigsaw's native `MessageEnvelope`.

## Shared Kernel Contract Mapping

Jigsaw now accepts `kernel.v1` as a first-class ingest surface for shared engine results.

Native Jigsaw runtime remains:

- `MessageEnvelope`

Shared `kernel.v1` ingest path:

- validate payload against `schemas/kernel_v1.schema.json`
- parse typed result fields
- map the result into `MessageEnvelope`
- preserve the original payload in `metadata["kernel_v1"]`

### `kernel.v1` -> `MessageEnvelope`

| `kernel.v1` field | Jigsaw target | Notes |
| --- | --- | --- |
| `subject.subject_id` | `candidate.candidate_id` | preserved directly |
| `subject.subject_type` | `candidate.kind` | preserved directly |
| `summary` | `candidate.summary`, `explanation.summary` | used for top-line explanation |
| `classification` | `candidate.attributes.classification` | preserved as metadata |
| `outputs.recommended_action` | `candidate.attributes.recommended_action` | preserved as metadata |
| `outputs.tags` | `candidate.attributes.tags` | preserved as metadata |
| `score` | `scores["kernel_score"]` | explicit shared-contract score |
| `confidence` | `scores["kernel_confidence"]`, `scores["confidence"]` | confidence remains separate from score |
| `signals.relevance` | `scores["fit"]` | used as Jigsaw fit-compatible signal |
| `evidence[*]` | `evidence[*]` | mapped into `EvidenceRecord` with provenance |
| `rationale` | `explanation.why_now` | preserved as rationale |
| `outputs.matched_targets` | `explanation.supporting_points` | labels become supporting points |
| full payload | `metadata["kernel_v1"]` | original validated result retained for audit |

This mapping keeps Jigsaw compatible with the shared engine-result primitive without redesigning the internal kernel chain.

## Garbage Collector Mapping

### Real integration points used

- Garbage Collector semantic retrieval API: `POST /api/retrieval/search`
- Garbage Collector item-ingest API: `POST /api/items`
- Garbage Collector SQLite `items` table as a fallback integration surface

### Jigsaw `MemoryAdapter` expectations

Required for Jigsaw:

- retrieve similar prior cases
- persist a completed decision trace

Optional for Jigsaw:

- richer typed outcomes for prior cases
- semantic similarity scores from the native retrieval engine
- direct trace-specific storage endpoints

### Current field mapping for retrieval

Garbage Collector API result:

- `item_id` -> `MemoryCase.case_id` as `gc-item-{item_id}`
- `score` -> `MemoryCase.similarity`
- `chunk_text` -> `MemoryCase.summary`
- `source_url`, `source_filename`, `item_title`, `chunk_id` -> `MemoryCase.provenance`

### Current field mapping for persistence

If using SQLite:

- `items.item_type` = `jigsaw_trace`
- `items.title` = `Jigsaw trace: <candidate title>`
- `items.content` = serialized envelope and trace payload
- `items.metadata_json` = Jigsaw trace metadata
- `items.entities_json` = empty entity buckets

If using HTTP only:

- trace is stored through `POST /api/items`
- it lands as ordinary pasted text because Garbage Collector does not yet expose a typed trace-ingestion endpoint

### Garbage Collector mismatches

- Garbage Collector does not currently expose a dedicated `persist_trace` API
- Garbage Collector retrieval responses return chunks, not explicit prior decision cases
- Garbage Collector does not natively store `outcome` for retrieved cases in the current public schema

### Adapter assumptions

- Jigsaw can treat retrieved Garbage Collector items as memory context even when they are not prior adjudicated cases
- `outcome` is therefore mapped to `unknown` unless a richer store is available
- direct SQLite persistence is acceptable for local integration realism when the HTTP API is insufficient

## Arbiter Mapping

### Real integration points used

- Arbiter public demo function `demo/run.py:adjudicate`
- Arbiter request schema in `schemas/arbiter_request.schema.json`
- Arbiter response schema in `schemas/arbiter_response.schema.json`

### Jigsaw `ArbiterAdapter` expectations

Required for Jigsaw:

- accept a structured evidence packet
- return a decision label, confidence, and reason

Optional for Jigsaw:

- richer policy explanations
- explicit escalation output
- more domain-specific context inputs

### Current field mapping for request

Jigsaw envelope -> Arbiter request:

- `candidate.candidate_id` -> `candidate_id`
- `candidate.kind` -> `candidate_type`
- `explanation.summary` or `candidate.summary` -> `summary`
- unique evidence source count -> `evidence.source_count`
- `scores.fit` -> `evidence.fit_score`
- `candidate.attributes.budget_band` -> `evidence.estimated_value_band`
- `candidate.attributes.freshness_days` or default `30` -> `evidence.freshness_days`
- Jigsaw metadata and candidate attributes -> `context.*`

### Current field mapping for response

Arbiter response -> Jigsaw decision:

- `promoted` -> `approve`
- `watchlist` -> `watchlist`
- `rejected` -> `reject`
- `confidence` -> `confidence`
- `reason_summary` -> `reason`
- `recommended_action` and `key_factors` -> `required_follow_up`

### Arbiter mismatches

- Jigsaw supports `approve`, `reject`, `watchlist`, `escalate`
- public Arbiter currently exposes `promoted`, `watchlist`, `rejected`
- there is no public `escalate` output in the current Arbiter contract
- Arbiter requires `freshness_days`, but Jigsaw does not model freshness as a first-class field yet

### Adapter assumptions

- public `promoted` is treated as Jigsaw `approve`
- `escalate` is not available through the current public Arbiter contract
- missing freshness is currently defaulted to `30` days unless supplied on the candidate

## Stability Assessment

Jigsaw remained stable as a middle layer because:

- the kernel chain did not need redesign
- the message envelope did not need invasive rewrite
- the mismatches were concentrated in adapter mapping logic

That is the main architectural result of this milestone.
