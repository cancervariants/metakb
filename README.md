[![Documentation Status](https://readthedocs.org/projects/vicc-metakb/badge/?version=latest)](https://vicc-metakb.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.org/cancervariants/metakb.svg?branch=main)](https://travis-ci.org/cancervariants/metakb) [![Coverage Status](https://coveralls.io/repos/github/cancervariants/metakb/badge.svg?branch=main)](https://coveralls.io/github/cancervariants/metakb?branch=main)

# metakb

The intent of the project is to leverage the collective knowledge of the disparate existing resources of the VICC to improve the comprehensiveness of clinical interpretation of genomic variation. An ongoing goal will be to provide and improve upon standards and guidelines by which other groups with clinical interpretation data may make it accessible and visible to the public. We have released a preprint discussing our initial harmonization effort and observed disparities in the structure and content of variant interpretations.

## Getting Started

> These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- Docker and Docker Compose v2
- A newer version of Python 3 (preferably 3.11+)
- [Node.js](https://nodejs.org/en) (v18 or later)
- [pnpm](https://pnpm.io/) package manager
- Optional (but useful): [Neo4j Desktop](https://neo4j.com/developer/neo4j-desktop) and Java (for local databases)

Check your python version with:

```bash
python3 --version
```

### Architecture Overview

MetaKB is composed of several services. Most are orchestrated with Docker Compose (except for the frontend)

- MetaKB API - FastAPI Backend (`server/`)
- MetaKB UI - Vite + React + Typescript frontend (`client/`)
- Neo4j - Graph database
- Normalizer services - Gene, disease, and therapy normalizers (DynamoDB-backed)

Two compose configurations are provided:

- `compose-dev.yaml` - Local development (editable installs, hot reload)
- `compose.yaml` - Image-based setup

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

#### 3. Start the API

From the root of the repo you can run either:

Image-based start up:

```bash
docker compose up
```

to reset everything:

```bash
docker compose down -v
```

or for local development:

```bash
docker compose -f compose-dev.yaml up
```

similarly, to reset:

```bash
docker compose -f compose-dev.yaml down -v
```

#### 4. Start the frontend

In a new terminal tab:

```bash
cd client
pnpm dev
```

Once running, you can visit:

- API: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/api](http://localhost:8000/api)
- Neo4j Browser: [http://localhost:7474](http://localhost:7474) (user: `neo4j`, password: `password`)
- UI: [http://localhost:5173](http://localhost:5173)

### Setting up normalizers

The normalizers are set up for you when using Docker Compose.

MetaKB can acquire all other needed normalizer data, except for that of [OMIM](https://www.omim.org/downloads), which must be manually placed:

```sh
cp ~/YOUR/PATH/TO/mimTitles.txt ~/.local/share/wags_tails/omim/omim_<date>.tsv  # replace <date> with date of data acquisition formatted as YYYYMMDD
```

### Environment Variables

MetaKB relies on environment variables to set in order to work.

- Common variables include:
  - `UTA_DB_URL` - PostgreSQL connection string for UTA
  - `METAKB_DB_URL` - Neo4j connection string
  - `SEQREPO_ROOT_DIR` - Local SeqRepo path

These are already set appropriately in the Compose files, but they can be modified to support local development with other locations or versions if needed.

### Neo4j Snapshot Image

MetaKB uses a pre-populated Neo4j image published to the GitHub Container Registry: `ghcr.io/cancervariants/metakb-neo4j:<tag>`

See `docker/neo4j/README.md` for full documentation on generating a Neo4j dump, building the snapshot image, and pushing to GHCR.

Note: Most developers will not need to rebuild this image.

### MetaKB API Image

The MetaKB backend itself is also distributed as a Docker image: `ghcr.io/cancervariants/metakb:<tag>`

This image:

- Contains the FastAPI backend
- Installs all Python dependencies at build time
- Does not include dev-only behavior (no bind mounts, no reload)

The image should be rebuilt and pushed for new releases.

#### Building and pushing the MetaKB API image

Note: most contributors will not need to do this routinely

From the repository root:

```bash
docker build -t metakb:local .
```

Tag and push:

```bash
docker tag metakb:local ghcr.io/cancervariants/metakb:<tag>
```

```bash
docker push ghcr.io/cancervariants/metakb:<tag>
```

Recommended tags:

- Feature branches: `issue-123-brief-description`
- Snapshots: `YYYYMMDD`
- Releases: semantic versioning corresponding with the MetaKB release (e.g. `2.0.1`)

## Testing

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

## Generating requirements

[requirements.txt](./requirements.txt) is used for Elastic Beanstalk to install the
dependencies. Anytime you update package requirements in
[pyproject.toml](./server/pyproject.toml) be sure to create a new virtual environment,
install only the required packages (`pip install -e .`) and update the
[requirements.txt](./requirements.txt).

To generate run the below command from `server` directory (ensure you have started the venv):

```commandline
pip freeze --exclude-editable > ../requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
