[![Documentation Status](https://readthedocs.org/projects/vicc-metakb/badge/?version=latest)](https://vicc-metakb.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.org/cancervariants/metakb.svg?branch=main)](https://travis-ci.org/cancervariants/metakb) [![Coverage Status](https://coveralls.io/repos/github/cancervariants/metakb/badge.svg?branch=main)](https://coveralls.io/github/cancervariants/metakb?branch=main)

# metakb

The intent of the project is to leverage the collective knowledge of the disparate existing resources of the VICC to improve the comprehensiveness of clinical interpretation of genomic variation. An ongoing goal will be to provide and improve upon standards and guidelines by which other groups with clinical interpretation data may make it accessible and visible to the public. We have released a preprint discussing our initial harmonization effort and observed disparities in the structure and content of variant interpretations.

## Getting Started

> These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- A newer version of Python 3 (preferably 3.11+)
- [Node.js](https://nodejs.org/en) (v18 or later)
- [pnpm](https://pnpm.io/) package manager
- [Neo4j Desktop](https://neo4j.com/developer/neo4j-desktop) and Java (for local databases)

Check your python version with:

```bash
python3 --version
```

### Monorepo Installation & Setup

We use a monorepo with [Turborepo](https://turbo.build) to coordinate development of the backend (FastAPI) and frontend (Vite + React).

#### 1. Clone the Repo

```bash
git clone https://github.com/cancervariants/metakb
cd metakb
```

#### 2. Install dependencies

```bash
pnpm install
```

#### 3. Set up the Python backend

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

#### 4. Set up required services

Before starting the app, you must set up required dependencies:

- [Neo4j Setup](#setting-up-neo4j)
- [Setting up Normalizers](#setting-up-normalizers)
- [Environment Variables](#environment-variables)

These services are required for the backend to function correctly.

Once all service and data dependencies are available, clear the graph, load normalizer data, and initiate harvest, transform, and data loading operations:

```shell
metakb update-normalizers
metakb update --refresh_source_caches
```

The `--help` flag can be provided to any CLI command to bring up additional documentation.

Ensure that both the MetaKB Neo4j and Normalizers databases are running.

#### 5. Start the development servers

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend Swagger docs: [http://localhost:8000/api/v2](http://localhost:8000/api/v2)

---

## Running the Backend by Itself

If you want to run the backend only:

```bash
cd server
source venv/bin/activate
uvicorn src.metakb.main:app --reload --host 0.0.0.0 --port 8000
```

You can then visit [http://localhost:8000/api/v2](http://localhost:8000/api/v2) for the Swagger UI.

---

### Setting up Neo4j

The MetaKB uses [Neo4j](https://neo4j.com/) for its database backend. To run a local MetaKB instance, you'll need to run a Neo4j database instance as well. The easiest way to do this is from Neo4j Desktop.

First, follow the [desktop setup instructions](https://neo4j.com/developer/neo4j-desktop) to download, install, and open Neo4j Desktop for the first time.

Once you have opened Neo4j desktop, use the `New` button in the upper-left region of the window to create a new project. Within that project, click the `Add` button in the upper-right region of the window and select `Local DBMS`. The name of the DBMS doesn't matter, but the password will be used later to connect the database to MetaKB (we have been using `password` by default). Select version `5.14.0` (other versions have not been tested). Click `Create`. Then, click the row within the project screen corresponding to your newly-created DBMS, and click the green `Start` button to start the database service.

The graph will initially be empty, but once you have successfully loaded data, Neo4j Desktop provides an interface for exploring and visualizing relationships within the graph. To access it, click the blue "Open" button. The prompt at the top of this window processes [Cypher queries](https://neo4j.com/docs/cypher-refcard/current/); to start, try `MATCH (n:Statement {id:"civic.eid:1409"}) RETURN n`. Buttons on the left-hand edge of the results pane let you select graph, tabular, or textual output.

### Setting up normalizers

The MetaKB calls a number of normalizer libraries to transform resource data and resolve incoming search queries. These will be installed as part of the package requirements, but may require additional setup.

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
cp ~/YOUR/PATH/TO/mimTitles.txt ~/.local/share/wags_tails/omim/omim_<date>.tsv  # replace <date> with date of data acquisition formatted as YYYYMMDD
```

### Environment Variables

MetaKB relies on environment variables to set in order to work.

- Always Required:
  - `UTA_DB_URL`
    - Used in Variation Normalizer which relies on UTA Tools
    - Format: `driver://user:pass@host/database/schema`
    - More info can be found [here](https://github.com/GenomicMedLab/uta-tools#connecting-to-the-database)

    Example:

    ```shell script
    export UTA_DB_URL=postgresql://uta_admin:password@localhost:5432/uta/uta_20210129
    ```

## Running tests

### Unit tests

To run unit tests, make sure you have a venv active and proper dependencies installed.

```bash
cd server
virtualenv venv
source venv/bin/activate
pip install -e ".[tests,dev]"
```

Then run the tests:

```sh
cd tests
pytest
```

Note: if you are getting errors signalling missing dependencies, make sure the dependency is installed with `pip show packagenamehere`. If it is installed, try refreshing your shell cache with `hash -r`. This will help your shell use the `pytest` in the `venv` instead of one that may be in your system elsewhere.

### And coding style tests

Code style is managed by [ruff](https://astral.sh/ruff) and checked prior to commit.

```bash
python3 -m ruff check --fix . && python3 -m ruff format .

```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

### Committing

We use [pre-commit](https://pre-commit.com/#usage) to run conformance tests.

This ensures:

- Check code style
- Check for added large files
- Detect AWS Credentials
- Detect Private Key

Before first commit run:

```sh
pre-commit install
```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/cancervariants/metakb/tags).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
