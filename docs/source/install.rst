.. _install:

Installation
============

Prerequisites
-------------

* A recent version of Python (>= 3.10)
* A recent Neo4j database server (e.g. `Neo4j Desktop <https://neo4j.com/download>`_, version 5.14 or newer)
* A recent `PostgreSQL database server <https://www.postgresql.org/download/>`_ (version 14 or newer)

Installing the service
----------------------

Install the most recent prerelease version of the MetaKB from `PyPI <https://pypi.org/project/metakb>`_:

.. code-block::

   python3 -m pip install --pre metakb

Or, install from the latest available commit via the `GitHub repo <https://github.com/cancervariants/metakb>`_:

.. code-block::

   git clone https://github.com/cancervariants/metakb
   cd metakb
   python3 -m virtualenv venv
   source venv/bin/activate
   pip install -e .

.. note::

   Stable (1.x) releases can be acquired from `PyPI <https://pypi.org/project/metakb>`_:

   .. code-block::

      python3 -m pip install metakb

Setting up dependencies
-----------------------

MetaKB's data loading and searching functions employ a variety of upstream services and data providers:

.. thumbnail:: _assets/images/deps_layout.png
   :width: 50%
   :align: center

SeqRepo
+++++++

MetaKB requires access to `SeqRepo <https://github.com/biocommons/biocommons.seqrepo>`_ data for reloading the Gene Normalizer and for normalizing variation queries. In general, we recommend the following for local setup:

.. long-term, it would be best to move this over to seqrepo to avoid duplication

.. code-block::

   pip install seqrepo
   export SEQREPO_VERSION=2024-02-20  # or newer if available -- check `seqrepo list-remote-instances`
   sudo mkdir /usr/local/share/seqrepo
   sudo chown $USER /usr/local/share/seqrepo
   seqrepo pull -i $SEQREPO_VERSION

If you encounter a permission error similar to the one below:

.. code-block::

   PermissionError: [Error 13] Permission denied: '/usr/local/share/seqrepo/2021-01-29._fkuefgd' -> '/usr/local/share/seqrepo/2021-01-29'

Try moving data manually with ``sudo``:

.. code-block::

   sudo mv /usr/local/share/seqrepo/$SEQREPO_VERSION.* /usr/local/share/seqrepo/$SEQREPO_VERSION

See `mirroring documentation <https://github.com/biocommons/biocommons.seqrepo/blob/main/docs/mirror.rst>`_ on the SeqRepo GitHub repo for instructions and additional troubleshooting.

Universal Transcript Archive (UTA)
++++++++++++++++++++++++++++++++++

The MetaKB requires an available instance of the Universal Transcript Archive (UTA) database, managed by the `Cool-Seq-Tool library <https://coolseqtool.readthedocs.io/latest/index.html>`_ for normalizing variation queries. Complete installation instructions (via Docker or a local server) are available at the `UTA GitHub repository <https://github.com/biocommons/uta>`_. For local usage, we recommend the following:

.. long-term, it would be best to move this over to the UTA repo to avoid duplication

.. code-block::

   createuser -U postgres uta_admin
   createuser -U postgres anonymous
   createdb -U postgres -O uta_admin uta

   export UTA_VERSION=uta_20210129b.pgd.gz  # most recent as of 2024/06/20
   curl -O https://dl.biocommons.org/uta/$UTA_VERSION
   gzip -cdq ${UTA_VERSION} | psql -h localhost -U uta_admin --echo-errors --single-transaction -v ON_ERROR_STOP=1 -d uta -p 5432

By default, MetaKB expects to connect to the UTA database via a PostgreSQL connection served local on port 5432, under the PostgreSQL username ``uta_admin`` and the schema ``uta_20210129b``. Use the environment variable ``UTA_DB_URL`` to specify an alternate `libpq-compliant URI <https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING-URIS>`_.

Gene, Disease, and Therapy Normalizers
++++++++++++++++++++++++++++++++++++++

.. therapy docs are unavailable -- return once they're up

The MetaKB uses the `Gene <https://gene-normalizer.readthedocs.io/>`_, `Disease <https://disease-normalizer.readthedocs.io/>`_, and `Therapy <https://github.com/cancervariants/therapy-normalization>`_ normalizer services to resolve biomedical concept referents during data loading and searching.

To set up databases from scratch, first set up an instance of DynamoDB (e.g. `locally <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html>`_).

Next, two environment variables are required for data access. First, Thera-Py requires a UMLS license to access RxNorm data. Register for a license `here <https://www.nlm.nih.gov/research/umls/index.html>`_, then acquire your API key from the `UTS 'My Profile' page <https://uts.nlm.nih.gov/uts/profile>`_ after signing in, and set it under the key ``UMLS_API_KEY``:

.. code-block::

   export UMLS_API_KEY=12345-6789-abcdefg-hijklmnop

Thera-Py also requires a Harvard Dataverse API key to access HemOnc.org data. Create a user account on the `website <https://dataverse.harvard.edu/>`_, follow `these instructions <https://guides.dataverse.org/en/latest/user/account.html>`_ to generate an API token, and set it under the key ``HARVARD_DATAVERSE_API_KEY``:

.. code-block::

   export HARVARD_DATAVERSE_API_KEY=12345-6789-abcdefgh-hijklmnop

.. this should be revisited -- the disease norm docs should be touched up and some additional methods should be added to make it easier:

Finally, disease term data from the `Online Mendelian Inheritance in Man (OMIM) resource <https://www.omim.org/>`_ must be acquired manually and placed in the Disease Normalizer data folder (located by default at ``~/.local/share/wags-tails/omim``). Acquire the OMIM file ``mimTitles.txt`` and rename it in the pattern ``omim_YYYYMMDD.tsv`` corresponding to the file's versioning.

Once these prerequisites are fulfilled, the normalizers can be loaded from scratch in succession with a CLI command:

.. code-block::

   $ metakb update-normalizers

.. TODO we should be able to reference parts of the CLI docs?

See the :ref:`CLI reference <cli-reference>` for more information about commands for accessing and managing normalizer data.

.. note::

   See specific instructions for each (`Therapy <https://github.com/cancervariants/therapy-normalization?tab=readme-ov-file#usage>`_, `Gene <https://gene-normalizer.readthedocs.io/latest/install.html>`_, `Disease <https://disease-normalizer.readthedocs.io/latest/install.html>`_) for additional setup options and more detailed instructions/troubleshooting.

Neo4j
+++++

For local use, we recommend Neo4j Desktop. First, follow the `desktop setup instructions <https://neo4j.com/developer/neo4j-desktop>`_ to download, install, and open Neo4j Desktop for the first time.

Once you have opened Neo4j desktop, use the ``New`` button in the upper-left region of the window to create a new project. Within that project, click the ``Add`` button in the upper-right region of the window and select ``Local DBMS``. The name of the DBMS doesn't matter, but the password will be used later to connect the database to MetaKB. Select version ``5.14.0`` (other versions have not been tested). Click ``Create``. Then, click the row within the project screen corresponding to your newly-created DBMS, and click the green Start button to start the database service.

By default, Neo4j Desktop serves to port ``7687``. Use the enviroment variable ``METAKB_NORM_DB_URL`` to configure an alternate port (default value: ``bolt://localhost:7687``).

Loading Data
------------

.. TODO add link to sources page once it's up

Once all dependencies are available, use the ``update`` console command to transform and load all :ref:`MetaKB source data`:

.. code-block::

   $ metakb update

.. TODO we should be able to reference parts of the CLI docs?

See the :ref:`CLI reference <cli-reference>` for more information about the ``update`` command.
