-- depends: 0002_create_silver_tables

-- K-means cluster assignment per molecule.
CREATE TABLE IF NOT EXISTS gold.clusters (
    "id"         BIGSERIAL PRIMARY KEY,
    "dataset_id" VARCHAR(128) NOT NULL,
    "smiles"     TEXT NOT NULL,
    "cluster_id" INTEGER NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_clusters_dataset_id ON gold.clusters ("dataset_id");

-- Control registry: which datasets have been processed (drives the "new since last run" logic).
CREATE TABLE IF NOT EXISTS gold.processed_datasets (
    "dataset_id"   VARCHAR(128) PRIMARY KEY,
    "n_molecules"  INTEGER NOT NULL DEFAULT 0,
    "n_clusters"   INTEGER NOT NULL DEFAULT 0,
    "processed_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
