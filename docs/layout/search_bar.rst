Getting Started
===============

Searching the meta-knowledgebase is done via free-text entry through the search bar at the top
of the page:

.. image:: /images/search_bar.png

Typical terms entered in this box include HGNC gene symbols, variant names, HGVS strings,
drug names, or diseases. See examples **TODO: link to examples** page for example queries that
may be made in this box.

After entering terms into the box, hit "Enter" or click on the search icon to perform the query.
Clicking the help icon will bring you to this documentation site.


Advanced search
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

