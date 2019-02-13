Getting Started
===============

Basic Search
------------

Searching the meta-knowledgebase is done via free-text entry through the search bar at the top
of the page:

.. image:: /images/search_bar.png

Typical terms entered in this box include HGNC gene symbols, variant names, HGVS strings,
drug names, or diseases. See examples **TODO: link to examples** page for examples of common
queries that may be made in this box.

After entering terms into the box, hit "Enter" or click on the search icon to perform the query.
Clicking the help icon will bring you to this documentation site.


Advanced Search
---------------
By default, the search results must match all terms put in the search box somewhere in the result
record, though this behavior is customizable by adjusting the query.

Logical operations can be achieved through the use of the `AND`, `OR`, and `NOT` keywords and
parentheticals (e.g. `BRAF AND (V600E OR V600D) AND NOT melanoma`). Additional documentation on how
to construct these and other advanced search queries (e.g. fuzzy searching, regular expressions)
may be found in the `ElasticSearch query documentation`_.

Individual record fields **TODO: link to record field documentation** are queryable by searching
using a `fieldname:term` pattern (e.g. `genes:BRAF`). By default, each search term is searched
against every field of the dataset. This can be helpful for removing evidence records that describe
terms that are not the subject of the evidence, but are mentioned in the record text (e.g. as a
study cofactor; see BRAF mention in a CIViC `MET evidence`_ record).


.. _paper-filter:

The Paper Filter
----------------

The original goal of the meta-knowledgebase was the harmonization of clinical interpretations of
somatic variants in cancers. Our manuscript describes this harmonization across six established
clinical interpretation knowledgebases. However, we have since expanded the meta-kb to include
additional sources of information, including matching on clinical trial data. These data are an
exploratory and highly experimental component of the project.

We want to provide the research community both with the set of data explicitly described in our
manuscript, as well as the latest sources as we work to integrate them. Consequently, we have
implemented a "paper filter" which filters the results to the sources described in our manuscript,
which is enabled by default. To disable the filter (and view results from all sources), you may
hover over the paper filter icon and select "disable filter":

.. image:: /images/filter_disable.png
    :width: 300px


.. # Links

.. _`MET evidence`: https://civicdb.org/events/genes/52/summary/variants/621/summary/evidence/1584/summary#evidence
.. _`ElasticSearch query documentation`: https://www.elastic.co/guide/en/elasticsearch/reference/6.6/query-dsl-query-string-query.html#query-string-syntax
