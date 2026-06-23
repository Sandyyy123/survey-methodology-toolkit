# Survey Methodology Toolkit

A small, transparent toolkit for designing **unbiased surveys and representative
samples** — sample-size determination, quota planning with rake weighting, and a
rule-based question bias auditor. Built for studies run on panel platforms such
as Pollfish, where the panel skews and the question wording both need active
correction.

Pure Python standard library — `python main.py` runs the full workflow with no
install.

## Workflow

```
            STEP 1                 STEP 2                    STEP 3
        ┌────────────┐        ┌──────────────┐        ┌────────────────┐
 inputs │ precision  │        │ benchmark    │        │ draft          │
   ──▶  │ confidence │  ──▶   │ population   │  ──▶   │ questionnaire  │
        │ pop split  │        │ margins      │        │                │
        └─────┬──────┘        └──────┬───────┘        └───────┬────────┘
              │                      │                        │
        sample_size.py        quota_weighting.py        bias_audit.py
              │                      │                        │
        required completes    quota plan + rake        per-question findings
              ▼                 weights + eff. n               ▼
        ┌──────────────────────────────────────────────────────────┐
        │  Deliverable: sizing memo + sampling plan + clean survey  │
        └──────────────────────────────────────────────────────────┘
```

## Modules

| File | What it does | Key functions |
|------|--------------|---------------|
| `sample_size.py` | Cochran's formula, finite-population correction, design-effect adjustment, subgroup sizing | `required_sample`, `subgroup_total` |
| `quota_weighting.py` | Census-benchmarked quota plan; rake (IPF) weighting; Kish design effect & effective sample size | `build_quota_plan`, `rake_weights`, `effective_sample_size` |
| `bias_audit.py` | Rule-based screen for leading/loaded, double-barreled, absolute terms, unbalanced scales, assumptive framing, jargon, missing "Don't know" | `audit_question`, `audit_survey` |
| `main.py` | Runs all three steps end to end | — |

## Example

```python
from sample_size import required_sample
r = required_sample(margin_of_error=0.03, confidence=0.95)
print(r.n_final)        # 1068  -> completes for a national +/-3% study
```

```python
from bias_audit import audit_question
a = audit_question("How much did you enjoy our easy-to-use product?")
print(a.report())       # flags the leading descriptor and suggests a fix
```

## Why rule-based (not a black box)

The bias auditor is deliberately explainable: every finding names the bias type,
the trigger, and a concrete rewrite. It handles the mechanical issues so a
methodologist's time goes to the judgment calls. It is a first pass, not a
replacement for expert review.

---

Built by **Dr. Sandeep Grover** — PhD Data Science; study design, sampling, and
statistical methodology across 60+ peer-reviewed publications.
