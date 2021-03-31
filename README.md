[![Documentation Status](https://readthedocs.org/projects/vicc-metakb/badge/?version=latest)](https://vicc-metakb.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.org/cancervariants/metakb.svg?branch=master)](https://travis-ci.org/cancervariants/metakb) [![Coverage Status](https://coveralls.io/repos/github/cancervariants/metakb/badge.svg?branch=master)](https://coveralls.io/github/cancervariants/metakb?branch=master)

# metakb

The intent of the project is to leverage the collective knowledge of the disparate existing resources of the VICC to improve the comprehensiveness of clinical interpretation of genomic variation. An ongoing goal will be to provide and improve upon standards and guidelines by which other groups with clinical interpretation data may make it accessible and visible to the public. We have released a preprint discussing our initial harmonization effort and observed disparities in the structure and content of variant interpretations.

## Getting Started

> These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them:

* python3

```
python3 --version
Python 3.7.1
```

### Installing

Install requirements

```
pip3 install -r requirements.txt
```

Install requirements-dev

```
pip3 install -r requirements-dev.txt
```

### Setting up Neo4j

The MetaKB uses [Neo4j](https://neo4j.com/) for its database backend. To run a local MetaKB instance, you'll need to run a Neo4j database instance as well. The easiest way to do this is from Neo4j Desktop.

First, follow the [desktop setup instructions](https://neo4j.com/developer/neo4j-desktop) to download, install, and open Neo4j Desktop for the first time.

Once you have opened Neo4j desktop, use the "New" button in the upper-left region of the window to create a new project. Within that project, click the "Add" button in the upper-right region of the window and select "Local DBMS". The name of the DBMS doesn't matter, but the password will be used later to connect the database to MetaKB (we have been using "admin" by default). Click "Create". Then, click the row within the project screen corresponding to your newly-created DBMS, and click the green "Start" button to start the database service.

The graph will initially be empty, but once you have successfully loaded data, Neo4j Desktop provides an interface for exploring and visualizing relationships within the graph. To access it, click the blue "Open" button. The prompt at the top of this window processes [Cypher queries](https://neo4j.com/docs/cypher-refcard/current/); to start, try `MATCH (n:DiseaseDescriptor {label:"Leukemia"}) RETURN n`. Toggles on the left-hand edge of the results pane let you select graph, tabular, or textual output.


### Loading data

[Future releases](https://github.com/cancervariants/metakb/pull/63) will include basic command-line tools to trigger data harvest, transformation, and load procedures, but in the meantime, we provide a simple script to load an existing resource CDM file (i.e. the JSON output of the MetaKB `transform` routines). After changing the second value of the tuple on line 7 to the password you selected for your Neo4j database, and changing the path on line 10 to the location of your target CDM file, run the following from the project root directory:

```
python3 analysis/graph/db_helper.py
```


## Running tests

### Unit tests

Explain how to run the automated tests for this system

```
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

```
pre-commit install
```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/cancervariants/metakb/tags).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
