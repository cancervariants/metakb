# PMKB Harvest + Transform

## Example usage

```shell
python3 analysis/pmkb/examples/harvester/pmkb_harvester_example.py
python3 analysis/pmkb/examples/transform/pmkb_transform_example.py
```

## Notes about data

* Online, PMKB publishes a number of interpretations where the text is simply "This gene is a known cancer gene." These interpretations are not included in the provided CSV.

* Sample input data are included under `analysis/pmkb/pmkb_input_sample_interps.csv` and `analysis/pmkb/pmkb_input_sample_variants.csv`.

* Currently, we successfully transform 179/624 (29%) of all PMKB interpretations.

* A majority of PMKB variations have generic/abstract labels: 29% include the string 'any' (eg "MYO5A any mutation"), and another 51% include "copy number gain" or "loss" (eg "MDM2 copy number gain"). Obviously these won't normalize at present.

* 29% of interpretations fail to normalize (at least in part) due to multiple given diseases. 20% fail (at least in part) due to multiple given variants.

* Interpretations include disease(s) and tissue type(s). We went back and forth on whether to try including tissue within the disease term to normalize (for disease "carcinoma" and tissue type "lung", it does make sense to make "lung carcinoma" the object qualifier of the proposition) but the combination of multiple diseases and multiple tissue types raised more questions in the short term, so we ultimately include tissue types as an Extension within the disease descriptor object, and drop any interpretation with multiple diseases. It'd be nice to resolve both of these issues in a more satisfactory way in the long term.

## Explanation of fields

### Tier

PMKB assigns each interpretation to a *tier*, according to the following rules:

> **Tier 1 - Variants with strong evidence of clinical utility**
>
> * Variants with strong evidence1 of clinical actionability for this tumor type, including FDA-approved targeted therapies for this tumor type.
> * Variants with strong evidence1 of prognostic significance for this tumor type.
> * Variants recognized as entity-defining molecular alterations by current WHO guidelines for this tumor type.
>
> **Tier 2 - Variants with potential clinical relevance**
>
> * Strong evidence1 of clinical actionability in this tumor or in a different tumor type.
> * Known investigational studies targeting this variant in this tumor type.
> * Variants may be included in this tier if they are characteristic of a particular tumor type and/or are thought to have functional relevance for this tumor type, but they do not meet criteria for Tier 1.
>
> **Tier 3 - Variants of undetermined clinical significance**
>
> * The functional and clinical relevance of these variants are undetermined for this tumor type. These variants are provided in the event that they are proven to be of clinical utility at a later date.
>
> *1 Evidence is considered “strong” if there is/are*:
>
> * An FDA-approved therapy included in professional guidelines related to this variant for this tumor type, and/or
> * Well-powered studies with consensus from experts in the field that guide therapy based on this variant as an independent parameter in this tumor type.
