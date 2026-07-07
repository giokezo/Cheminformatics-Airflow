# Cheminformatics Airflow Pipeline

An Apache Airflow pipeline that supports a drug-discovery cheminformatics workflow.

## Domain context

During the week, scientists upload two CSV files per dataset to object storage:

- `<id>_scaffolds.csv` — molecular scaffolds (a single `smiles` column, `*` marks attachment points)
- `<id>_r_groups.csv` — R-groups to attach (same single `smiles` column format, e.g. `CCC*`)

For every dataset `id` the pipeline:

1. **generates molecules** by combinatorially attaching R-groups to scaffold attachment points (RDKit),
2. **calculates molecular properties** (LogP, HBA, HBD, molecular weight, TPSA, …),
3. **clusters** the molecules with **K-means** (over molecular fingerprints),
4. *(optional)* predicts properties with **ChemProp**,
5. *(optional)* builds a **Faerun/tmap** similarity graph.

## Architecture

A thin-DAG / fat-lib layout — DAG files only wire tasks together; all logic lives in `dags/lib/`.

```
dags/
  cheminformatics_dag.py            # processes ONE dataset_id (Step 1)
  cheminformatics_scheduler_dag.py  # weekly, fans out to all new datasets (Step 2)
  lib/
    cheminformatics/                # domain logic (generation, properties, clustering, ...)
    utils/                          # generic helpers (s3, soda, teams, dataframe, smiles)
migrations/                         # yoyo SQL migrations for the warehouse (bronze/silver/gold)
soda/                               # Soda data-quality checks
BE/                                 # optional FastAPI service to trigger DAGs with a dataset_id
```

### Medallion layers

| Layer  | Where                    | Contents                                                        |
|--------|--------------------------|-----------------------------------------------------------------|
| raw    | S3 `raw` bucket          | the two input CSVs uploaded by scientists                        |
| silver | Postgres `silver` + S3   | `silver.molecules`, `silver.properties`                          |
| gold   | Postgres `gold` + S3     | `gold.clusters`, `gold.processed_datasets` (run registry)        |

Optional artifacts (Faerun `graph.zip`, ChemProp `predictions.csv`) are written to the `results`
bucket only.

## Data quality (Step 3)

- **Pandera** validates DataFrames before they are loaded into Postgres.
- **Soda** validates the warehouse tables after load (`soda/cheminformatics/*.yml`).
- Any failed check fails the task, which fires an **MS Teams** alert.

## MS Teams notifications (Step 3)

- Failure: `on_failure_callback` posts an alert card.
- Success: a summary card (dataset, #molecules, #clusters, optional-step status).
- The webhook URL lives only in the `msteams_webhook` Airflow Connection (provisioned via env,
  masked in logs). With no connection configured, the notifier logs instead of failing.

## Configuration

Everything secret is an Airflow **Connection** provisioned via environment variables (see
`.env.example`):

| Connection        | Purpose                                  |
|-------------------|------------------------------------------|
| `aws_s3`          | S3-compatible storage (MinIO locally)    |
| `dwh_connection`  | Postgres warehouse (silver/gold + Soda)  |
| `msteams_webhook` | MS Teams incoming webhook                |

Tunable Airflow **Variables** (all have defaults): `chem_n_clusters` (5), `chem_fingerprint`
(`ECFP4`), `chem_max_molecules` (50000).

## Local development

```bash
cp .env.example .env          # fill in the Teams webhook if you have one
docker compose up --build
```

- Airflow UI: http://localhost:8080 (admin / admin)
- MinIO console: http://localhost:9090 (minio_access_key / minio_secret_key)

`docker compose up` also runs the warehouse migrations and seeds a `sample` dataset into the `raw`
bucket.

### Run the pipeline

- **Step 1 (single dataset):** trigger `cheminformatics_dag` with conf `{"dataset_id": "sample"}`
  (Airflow UI → *Trigger DAG w/ config*, or the `BE/` API). Add `"run_faerun": true` /
  `"run_chemprop": true` to enable the optional steps.
- **Step 2 (weekly batch):** `cheminformatics_scheduler_dag` runs on `@weekly` and processes every
  dataset that appeared since the last run. Set conf `{"overwrite": true}` to reprocess everything.

## Tests

Unit tests cover the pure logic (generation, properties, clustering, fingerprints, SMILES/dataframe
helpers). The Airflow-dependent imports live inside the task callables, so the tests run in a plain
virtualenv without Airflow:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest tests/ -v
```

## Branch policy

`feature -> dev -> prod`. Feature branches are cut from `dev`; PRs merge into `dev`; `dev` is
promoted to `prod` (the default branch) via a release PR.

## Optional dependencies

The Faerun/tmap step needs heavy native packages kept out of the default image — see
`requirements-faerun.txt` (add them via `_PIP_ADDITIONAL_REQUIREMENTS` or the image build to enable
`run_faerun`). ChemProp is shipped as a documented stub task.
