# PMKB Harvest + Transform

## Example usage

```shell
python3 analysis/pmkb/examples/harvester/pmkb_harvester_example.py
python3 analysis/pmkb/examples/transform/pmkb_transform_example.py
```

## Notes about data

* Online, PMKB publishes a number of interpretations where the text is simply "This gene is a known cancer gene." These interpretations are not included in the provided CSV.

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
