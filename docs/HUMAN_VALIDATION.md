# Human validation of the reconstructed forms gold

The Brazilian forms accuracy axis is scored against a gold that was **reconstructed from the
form images** because the source benchmark's key-value gold is contaminated (printed checkbox
instructions and mislinked labels mixed into the answer set). The reconstruction was done with
**Claude Opus**, a large multimodal model that is **not among the evaluated engines**, so no
engine is scored against its own output.

That reconstructed gold was then **validated by two human annotators, independently**.

## Method

1. `scripts/validation/sample_validation_fields.py` draws a **reproducible uniform random
   sample** of **250** of the **1428** scored fields (non-empty values) across the forms.
   The pool is sorted deterministically before sampling, so the draw does not depend on the
   filesystem, and the seed is fixed (**seed 0**): the same command reproduces the same 250
   fields. The field values carry the source dataset's licence, so the sample itself stays
   local; only the PII-free result below is published.
2. `scripts/validation/gen_review_html.py` renders the sample into a self-contained browser
   page: each sampled form's image sits beside its sampled fields, and the reviewer marks every
   field **OK** or **Wrong** (with a correction box) and exports the verdicts as JSON.
3. Two annotators reviewed the **same** 250-field sample independently and returned their
   exports.

![Annotation screen](img/human_validation.png)

## Result (`results/forms_validation.json`)

| Annotator | Reviewed | OK | Wrong |
|-----------|---------:|---:|------:|
| rater-1   | 250      | 250 | 0 |
| rater-2   | 250      | 250 | 0 |

Both annotators found **no error**. Field-level gold accuracy is **1.00**, Wilson 95% interval
**[0.985, 1.000]** (n = 250), with **full agreement** between the annotators.

## One discussed non-error

The annotators flagged a representation choice rather than a mistake: **marked-option answers are
not encoded uniformly** across forms. An alternative shown as `Alternativa A (X)` can be encoded
two equally valid ways: the full option text as the answer, or the option label as the field with
the `X` as the answer (one consent form takes the second, recording seven checklist items each as
a `V`). The consensus was that the reconstructed value is **correct**; the correction prompt
simply does not standardize which encoding it uses. This is a prompt artifact of the gold
correction, not a wrong value; it changes how an answer is written, not whether it is correct.

## Provenance / licence

The underlying forms gold derives from **XFUND** (CC BY-NC-SA 4.0); its images are Brazilian
administrative form templates filled with **synthetic** data by the benchmark's annotators, so
they carry no real personal data. The raw per-field annotations and field values are not
redistributed here; this directory records only PII-free counts. The screenshot is a single
illustrative frame of the annotation tool.
