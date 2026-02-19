# MetaKB Neo4j Snapshot Image

This directory contains everything needed to build and publish a pre-populated Neo4j image for MetaKB. The resulting image is pushed to GitHub Container Registry (GHCR) and used by Docker Compose for local development and (optionally) other environments.

Core ideas:

- Neo4j data is treated as versioned, immutable data
- The database is restored at image build time from a `neo4j.dump`
- Developers do not need Neo4j Desktop or local dumps to run the MetaKB stack

## What lives in this directory

```bash
docker/neo4j/
├── Dockerfile        # Recipe for building the Neo4j snapshot image
├── README.md         # (this file)
└── neo4j.dump        # Input dump (NOT committed)
```

The `neo4j.dump` is intentionally not committed. It is a build-time input only.

## How the snapshot image works

1. A Neo4j database is exported to `neo4j.dump` in this folder. (This is done manually by a developer)
2. The Dockerfile copies the dump into the image.
3. `neo4j-admin database load` restores the database during docker build
4. The resulting image contains a fully populated Neo4j database.

At runtime:

- Neo4j starts normally
- No loaders need to be run or volumes are required

## Prerequisites

- Docker
- Access to the MetaKB Neo4j database (locally or remotely)
- GitHub account with permission to push to `ghcr.io/cancervariants`

## Step 1: Generate a Neo4j dump

** NOTE: MAKE SURE YOUR DATABASE IS FULLY UP TO DATE PRIOR TO COMPLETING THESE STEPS.

### Using Neo4j Desktop

1. Open Neo4j Desktop
2. Stop the database you want to snapshot
3. Click the ... menu
4. Click Export databases to .dump option
5. Once finished, rename the file to `neo4j.dump` and drag it into this directory (`docker/neo4j`)

## Step 2: Build the snapshot image

From the repository root:

```bash
docker build \
  -t metakb-neo4j:local \
  ./docker/neo4j
```

This will:

- Copy `neo4j.dump` into the image
- Restore the database at build time
- Produce a reusable local image

## Step 3: Test the image locally

Run the image directly:

```bash
docker run --rm \
  -e NEO4J_AUTH=neo4j/password \
  -p 7474:7474 \
  -p 7687:7687 \
  metakb-neo4j:local
```

Then:

- Open [http://localhost:7474](http://localhost:7474)
- Log in with:
  - user: neo4j
  - password: password
- Verify data `MATCH (n) RETURN count(n);`
If this returns a non-zero and the count matches the known-correct database you used to create the image, the image is correct.

## Step 4: Tag and push to GHCR (GitHub Container Registry)

### Authenticate to GHCR

Use a GitHub Personal Access Token. See [here](https://docs.github.com/en/enterprise-cloud@latest/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry) for information about authenticating to the container registry. If you do not already have a PAT, you will need to create one and ensure you have the permissions `read:packages` and `write:packages`.

To create a PAT, you can:

1. Go to GitHub -> Settings -> Developer Settings -> Personal access tokens -> Tokens (classic)
2. Generate new token
3. Make sure to select `write:packages` and `read:packages` under "Select scopes"
4. Generate the token + copy to your clipboard

If you already have a token, you can skip the above steps. You will use it as your password for authenticating to GHCR.

To authenticate:

```bash
docker login ghcr.io
```

- Username: your GitHub username
- Password: Paste your GitHub PAT (must have `write:packages` permission)

### Tag the image

```bash
docker tag metakb-neo4j:local \
  ghcr.io/cancervariants/metakb-neo4j:DATEHERE
```

Replace DATEHERE with the date version of the most recent CDMs/CDMs that were used to populate your fully up-to-date database that you made a snapshot of.

ex: if your database was populated with civic_cdm_20260116.json and moa_cdm_20260116.json, you would run:

```bash
docker tag metakb-neo4j:local \
  ghcr.io/cancervariants/metakb-neo4j:20260116
```

Note: This assumes that all CDMs used in populating the db have the same date. We may want to re-visit this versioning schema if we ever expect this to change.

### Push the image

```bash
docker push ghcr.io/cancervariants/metakb-neo4j:DATEHERE
```

Again, replace DATEHERE with the date version above.

Once pushed, the image will be available under:

- GitHub -> cancervariants -> Packages -> metakb-neo4j

## Update the version in the Docker Compose files

The neo4j entry in `compose.yaml` and `compose-dev.yaml` should look something like this:

```yaml
neo4j:
  image: ghcr.io/cancervariants/metakb-neo4j:20260116
  ports:
    - "7474:7474"
    - "7687:7687"
  environment:
    NEO4J_AUTH: neo4j/password
```

## When to rebuild the snapshot

Rebuild and publish a new image when:

- MetaKB graph data changes
- A new or updated CDM is loaded
- Neo4j version changes
- You want to pair a DB snapshot with a MetaKB release

To reiterate, each rebuild should:

1. Generate a fresh `neo4j.dump`
2. Build a new image (make sure to test it! :-) )
3. Push a new tag
