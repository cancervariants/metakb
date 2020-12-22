# PMKB Harvester

## Notes about data

* While PMKB retains internal IDs for genes, variants, and interpretations ("therapies"), it does not publish these IDs in the provided CSV. It appears that interpretations are listed on the CSV in the order of their IDs, but it's not clear if this is a guarantee or not, and it's hard to verify without a REST API to check against.
* PMKB provides a number of interpretations where the text is simply "This gene is a known cancer gene." These interpretations are not included in the provided CSV.
* PMKB assertions may encompass multiple variants and draw from multiple pieces of evidence. These are not disaggregated in the published CSV.

## Example data

*Normally, columns are comma-separated and pipes (`|`) are used to separate data within columns, but that breaks Markdown table formatting, so I've altered this here.*

Gene | Tumor Type(s) | Tissue Type(s) | Variant(s) | Tier | Interpretations | Citations
--- | --- | --- | --- | --- | --- | ---
CSF3R | Myeloproliferative Neoplasm,Chronic Neutrophilic Leukemia,Atypical Chronic Myeloid Leukemia | Blood,Bone Marrow | CSF3R T618I,CSF3R any nonsense,CSF3R any frameshift | 1 | The activating missense membrane-proximal mutation in CSF3R (p.T618I) has been reported to occur in approximately 83% of cases of chronic neutrophilic leukemia; some reports indicate this mutation may be present in cases of atypical chronic myeloid leukemia as well.   The CS3R T618I mutation has been associated with response to JAK2 inhibitors but not dasatinib.  A germline activating CSF3R mutation (p. T617N) has been described in autosomal dominant hereditary neutrophilia associated with splenomegaly and increased circulating CD34-positive myeloid progenitors.  Nonsense and/or frameshift somatic mutations truncating the cytoplasmic domain of CSF3R have been described in approximately 40% of patients with severe congenital neutropenia and in the context of mutations in other genes may be associated with  progression to acute myeloid leukemia.  These activating truncating mutations have also been found in patients with chronic neutrophilic leukemia or atypical chronic myeloid leukemia. Some of these cytoplasmic truncating mutations have been associated with responses to dasatinib but not JAK2 inhibitors. | "Pardanani A, et al. CSF3R T618I is a highly prevalent and specific mutation in chronic neutrophilic leukemia. Leukemia 2013;27(9):1870-3,Maxson JE, et al. Oncogenic CSF3R mutations in chronic neutrophilic leukemia and atypical CML. N Engl J Med 2013;368(19):1781-90,Plo I, et al. An activating mutation in the CSF3R gene induces a hereditary chronic neutrophilia. J Exp Med 2009;206(8):1701-7"

## Explanation of fields

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

