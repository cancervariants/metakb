# MetaKB Scripts

This directory contains utility scripts that support various development and maintenance tasks
for the MetaKB monorepo.  
Scripts in this folder are **not part of the runtime application** — they are intended for
developers to use locally or in CI pipelines to assist with build, data, or code generation workflows.

---

## Current Scripts

| Script | Description |
|---------|--------------|
| **`generate_ts_models.py`** | Generates TypeScript model definitions for GA4GH Variant Annotation Specification entities, writing them to the frontend (`client/models/domain.ts`). |

---

## Generating TypeScript Models

The `generate_ts_models.py` script converts backend [Pydantic](https://docs.pydantic.dev/)
models (from [GA4GH Variant Annotation Specification](https://github.com/ga4gh/va-spec))
into TypeScript interfaces used by the frontend.

### What It Does

- Uses [`pydantic-to-typescript`](https://github.com/phillipdupuis/pydantic-to-typescript) to generate TypeScript definitions.  
- Runs inside the existing Python virtual environment in `server/.venv`.  
- Uses the Node CLI [`json-schema-to-typescript`](https://github.com/bcherny/json-schema-to-typescript) to generate type definitions.  
- Outputs the result to: `client/models/domain.ts`

### Requirements

Make sure you have the following tools available:

- Python >= 3.11
- [Node.js](https://nodejs.org/en) (v18 or later)
- [pnpm](https://pnpm.io/) package manager
- GNU Make

### How to Run

From the **root** of the repository, run:

```bash
make typescript-models
```

### Troubleshooting

| Problem | Cause | Fix |
| - | - | - |
| `json2t: command not found` | `node_modules` missing or stale | run `pnpm install --workspace-root` |
| `pydantic2ts` import errors | outdated virtual environment | Delete `server/.venv` and rerun `make typescript-models` |
| Generated file not updating | Possible path mismatch | Confirm the output path in `scripts/generate_ts_models.py` points to `client/models/domain.ts` |

### Notes

- This script should only be run if the Pydantic models have changed (e.g., whenever va-spec version is updated).
- The generated file should be committed so the frontend can use it.
- The python package `pydantic-to-typescript` is used for Pydantic v2 compatibility. The old `pydantic2ts` package is not compatible with Pydantic v2.
