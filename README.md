[![Documentation Status](https://readthedocs.org/projects/vicc-metakb/badge/?version=latest)](https://vicc-metakb.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.org/cancervariants/metakb.svg?branch=main)](https://travis-ci.org/cancervariants/metakb) [![Coverage Status](https://coveralls.io/repos/github/cancervariants/metakb/badge.svg?branch=main)](https://coveralls.io/github/cancervariants/metakb?branch=main)

# metakb

The intent of the project is to leverage the collective knowledge of the disparate existing resources of the VICC to improve the comprehensiveness of clinical interpretation of genomic variation. An ongoing goal will be to provide and improve upon standards and guidelines by which other groups with clinical interpretation data may make it accessible and visible to the public. We have released a preprint discussing our initial harmonization effort and observed disparities in the structure and content of variant interpretations.

## Getting Started

> These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- Docker and Docker Compose v2 (required)
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

#### 2. Start the API

##### Get UTA data

For now, we must manually get UTA data. Before starting the api, you will need to grab `uta_20241220.pgd.gz` from [biocommons (click here)](https://dl.biocommons.org/uta/)

Download the file and drag it into the `uta-init/` folder in this repo. Docker will handle the rest!
Note: if you opt to use a different version of the uta `gz` than the one specified, you will need to update `init-uta.sh` and `uta-setup.sql` to match the version you chose.

##### Set up SeqRepo

Additionally, some of the normalizer services rely on [seqrepo](https://github.com/biocommons/biocommons.seqrepo), which we need to set up before starting MetaKB.

Run:

```shell
pip install seqrepo
sudo mkdir /usr/local/share/seqrepo
sudo chown $USER /usr/local/share/seqrepo
seqrepo pull -i 2024-12-20/  # Replace with latest version using `seqrepo list-remote-instances` if outdated
```

Note: if you use a different version than specified, you may need to manually update `SEQREPO_ROOT_DIR` in the compose files.

If you get an error similar to the one below:

```shell
PermissionError: [Error 13] Permission denied: '/usr/local/share/seqrepo/2024-12-20/._fkuefgd' -> '/usr/local/share/seqrepo/2024-12-20/'
```

You will want to do the following:\
(_Might not be .\_fkuefgd, so replace with your error message path_)

```shell
sudo mv /usr/local/share/seqrepo/2024-12-20._fkuefgd /usr/local/share/seqrepo/2024-12-20
exit
```

You will also need to add this to your Virtual file shares in Docker Desktop. To do this:

1. Open Docker Desktop
2. Go to Settings
3. Go to Resources
4. Scroll down to Virtual file shares
5. Click the + button to add a new one
6. Paste `/usr/local/share/seqrepo`
7. Click Apply

##### Virtual environment

You'll want to work in a virtual environment. To set that up, run the following from the root of this project:

```bash
virtualenv venv
source venv/bin/activate
```

##### Starting the API

Now, we can start the API. From the root of the repo you can run either:

Image-based start up:

```bash
docker compose up
```

or for local development:

```bash
docker compose -f compose-dev.yaml up
```

to reset everything (if using image-based start):

```bash
docker compose down -v
```

similarly, to reset local development containers:

```bash
docker compose -f compose-dev.yaml down -v
```

#### 3. Start the frontend

Open a new terminal tab.

From the root repository, install frontend dependencies:

```bash
pnpm install
```

Start the frontend in the `client` directory

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

MetaKB relies on environment variables to be set in order to work. These are already set appropriately in the Compose files, but they can be modified to support local development with other locations or versions if needed.

- Common variables include:
  - `UTA_DB_URL` - PostgreSQL connection string for UTA
  - `METAKB_DB_URL` - Neo4j connection string
  - `SEQREPO_ROOT_DIR` - Local SeqRepo path

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

If you have a venv already set up from running the API, `deactivate` it and run the following:

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
uv pip compile pyproject.toml --extra deploy -o ../requirements.txt --no-annotate
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
