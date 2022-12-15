[![Documentation Status](https://readthedocs.org/projects/vicc-metakb/badge/?version=latest)](https://vicc-metakb.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.org/cancervariants/metakb.svg?branch=main)](https://travis-ci.org/cancervariants/metakb) [![Coverage Status](https://coveralls.io/repos/github/cancervariants/metakb/badge.svg?branch=main)](https://coveralls.io/github/cancervariants/metakb?branch=main)

# metakb

The intent of the project is to leverage the collective knowledge of the disparate existing resources of the VICC to improve the comprehensiveness of clinical interpretation of genomic variation. An ongoing goal will be to provide and improve upon standards and guidelines by which other groups with clinical interpretation data may make it accessible and visible to the public. We have released a preprint discussing our initial harmonization effort and observed disparities in the structure and content of variant interpretations.

## Getting Started

> These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

* A newer version of Python 3, preferably 3.8 or greater. To confirm on your system, run:

```
python3 --version
```

* [Pipenv](https://pipenv.pypa.io/en/latest/), for package management.

```
pip3 install --user pipenv
```

### Installing


Once Pipenv is installed, clone the repo and install the package requirements into a Pipenv environment:

```sh
git clone https://github.com/cancervariants/metakb
cd metakb
pipenv lock && pipenv sync
```

If you intend to provide development support, install the development dependencies:

```sh
pipenv lock --dev && pipenv sync
```

### Setting up Neo4j

The MetaKB uses [Neo4j](https://neo4j.com/) for its database backend. To run a local MetaKB instance, you'll need to run a Neo4j database instance as well. The easiest way to do this is from Neo4j Desktop.

First, follow the [desktop setup instructions](https://neo4j.com/developer/neo4j-desktop) to download, install, and open Neo4j Desktop for the first time.

Once you have opened Neo4j desktop, use the "New" button in the upper-left region of the window to create a new project. Within that project, click the "Add" button in the upper-right region of the window and select "Local DBMS". The name of the DBMS doesn't matter, but the password will be used later to connect the database to MetaKB (we have been using "admin" by default). Click "Create". Then, click the row within the project screen corresponding to your newly-created DBMS, and click the green "Start" button to start the database service.

The graph will initially be empty, but once you have successfully loaded data, Neo4j Desktop provides an interface for exploring and visualizing relationships within the graph. To access it, click the blue "Open" button. The prompt at the top of this window processes [Cypher queries](https://neo4j.com/docs/cypher-refcard/current/); to start, try `MATCH (n:Statement {id:"civic.eid:1409"}) RETURN n`. Buttons on the left-hand edge of the results pane let you select graph, tabular, or textual output.


### Setting up normalizers

The MetaKB calls a number of normalizer libraries to transform resource data and resolve incoming search queries. These will be installed as part of the package requirements, but require additional setup.

First, [follow these instructions for deploying DynamoDB locally on your computer](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html). Once setup, in a separate terminal instance, navigate to its source directory and run the following to start the database instance:

```sh
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
```

Next, navigate to the `site-packages` directory of your virtual environment. Assuming Pipenv is installed to your user directory, this should be something like:

```sh
cd ~/.local/share/virtualenvs/metakb-<various characters>/lib/python<python-version>/site-packages/  # replace <various characters> and <python-version>
```

Next, initialize the [Variation Normalizer](https://github.com/cancervariants/variation-normalization) by following the instructions in the [README](https://github.com/cancervariants/variation-normalization#installation). When setting up the UTA database, [these](https://github.com/ga4gh/vrs-python/tree/main/docs/setup_help) docs may be helpful.


The MetaKB can acquire all other needed normalizer data, except for that of [OMIM](https://www.omim.org/downloads), which must be manually placed:

```sh
cd disease/  # starting from the site-packages dir of your virtual environment's Python instance
mkdir -p data/omim
cp ~/YOUR/PATH/TO/mimTitles.txt data/omim/omim_<date>.tsv  # replace <date> with date of data acquisition formatted as YYYYMMDD
```

### Environment Variables

MetaKB relies on environment variables to set in order to work.

* Always Required:
  * `UTA_DB_URL`
    * Used in Variation Normalizer which relies on UTA Tools
    * Format: `driver://user:pass@host/database/schema`
    * More info can be found [here](https://github.com/GenomicMedLab/uta-tools#connecting-to-the-database)

    Example:

    ```shell script
    export UTA_DB_URL=postgresql://uta_admin:password@localhost:5432/uta/uta_20210129
    ```

  * `ONCOKB_API_TOKEN`
    * Required to harvest OncoKB data. If you do not set this environment variable, you can set during the initialization of the OncoKBHarvester.
    * Used to access OncoKB data via their REST API. See [here](https://www.oncokb.org/apiAccess) for more information on how to register an account and get an OncoKB API token.

    Example for setting environment variable:
    ```shell script
    export ONCOKB_API_TOKEN={api_token}
    ```

    Example for setting during OncoKB Harvester initialization:
    ```python
    OncoKBHarvester(api_token={api_token})
    ```

* Required when using the `--load_normalizers_db` or `--force_load_normalizers_db` arguments in CLI commands
  * `RXNORM_API_KEY`
    * Used in Therapy Normalizer to retrieve RxNorm data
    * RxNorm requires a UMLS license, which you can register for one [here](https://www.nlm.nih.gov/research/umls/index.html). You must set the `RxNORM_API_KEY` environment variable to your API key. This can be found in the [UTS 'My Profile' area](https://uts.nlm.nih.gov/uts/profile) after singing in.

    Example:

    ```shell script
    export RXNORM_API_KEY={rxnorm_api_key}
    ```

  * `DATAVERSE_API_KEY`
    * Used in Therapy Normalizer to retrieve HemOnc data
    * HemOnc.org data requires a Harvard Dataverse API key. After creating a user account on the Harvard Dataverse website, you can follow [these instructions](https://guides.dataverse.org/en/latest/user/account.html) to generate a key. You will create or login to your account at [this](https://dataverse.harvard.edu/) site. You must set the `DATAVERSE_API_KEY` environment variable to your API key.

    Example:

    ```shell script
    export DATAVERSE_API_KEY={dataverse_api_key}
    ```

### Data files

Some sources in MetaKB require user provided files to harvest data.

* OncoKB
  * In addition to setting the `ONCOKB_API_TOKEN` environment variable to harvest OncoKB data, you also need to provide a CSV file containing a header row with `hugo_symbol` and `protein_change`, associated rows containing protein variants you wish to harvest, and using a comma as the delimiter. The file will look something like:

    ```csv
    hugo_symbol,protein_change
    BRAF,V600E
    ...
    ```
  * This file will harvest OncoKB evidence based on the variants provided.

### Loading data

Once Neo4j and DynamoDB instances are both running, and necessary normalizer data has been placed, run the MetaKB CLI with the `--initialize_normalizers` flag to acquire all other necessary normalizer source data, and execute harvest, transform, and load operations into the graph datastore.

In the MetaKB project root, run the following:

```sh
pipenv shell
python3 -m metakb.cli --db_url=bolt://localhost:7687 --db_username=neo4j --db_password=<neo4j-password-here> --load_normalizers_db
```

For more information on the different CLI arguments, see the [CLI README](docs/cli/README.md).

### Starting the server

Once data has been loaded successfully, use the following to start service on localhost port 8000:

```sh
uvicorn metakb.main:app --reload
```

Ensure that both the MetaKB Neo4j and Normalizers databases are running.

Navigate to [http://localhost:8000/api/v2](http://localhost:8000/api/v2) in your browser to enter queries.

## Running tests

### Unit tests

Explain how to run the automated tests for this system

```sh
python3 -m pytest
```


### And coding style tests

Code style is managed by [flake8](https://github.com/PyCQA/flake8) and checked prior to commit.

```
see .flake8

```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

### Committing

We use [pre-commit](https://pre-commit.com/#usage) to run conformance tests.

This ensures:

* Check code style
* Check for added large files
* Detect AWS Credentials
* Detect Private Key

Before first commit run:

```sh
pre-commit install
```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/cancervariants/metakb/tags).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
