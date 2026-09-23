# Evaluation Framework

Evaluation criteria for the ExceptionLineage investigation system.

## Purpose

Define how to measure whether the investigation system produces correct, complete, and evidence-backed determinations.

## Evaluation Dimensions

### Accuracy

Does the system reach the correct determination for a given exception?

- **Metric:** Percentage of determinations that match expert-reviewed ground truth.
- **Measurement:** Compare system output against a curated set of known-answer investigations.
- **Not yet implemented.** Requires ground truth dataset and investigation pipeline.

### Evidence Completeness

Does the system find and use all relevant evidence?

- **Metric:** Recall of relevant documents and clauses for each investigation.
- **Measurement:** Compare evidence cited by the system against expert-identified evidence sets.
- **Not yet implemented.** Requires evidence collection pipeline.

### Evidence Traceability

Can every claim in the determination be traced back to a source document?

- **Metric:** Percentage of claims with valid source references.
- **Measurement:** Automated verification that each claim links to an existing document and location.
- **Not yet implemented.** Requires determination output format and verification tooling.

### Contradiction Detection

Does the system correctly identify and surface contradictory evidence?

- **Metric:** Precision and recall of detected contradictions against known contradictions.
- **Measurement:** Run system against curated contradictory evidence sets.
- **Not yet implemented.** Requires contradiction detection logic.

### Performance

Does the system complete investigations within acceptable time bounds?

- **Metric:** Investigation completion time (p50, p95, p99).
- **Measurement:** Time from investigation request to determination output.
- **Not yet implemented.** Requires investigation pipeline.

## Current State

No evaluation metrics are implemented yet. This framework defines the target criteria for when the investigation system is built.
