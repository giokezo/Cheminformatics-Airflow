-- depends: 0001_create_schemas

-- Generated molecules (one row per generated SMILES per dataset).
CREATE TABLE IF NOT EXISTS silver.molecules (
    "id"         BIGSERIAL PRIMARY KEY,
    "dataset_id" VARCHAR(128) NOT NULL,
    "smiles"     TEXT NOT NULL,
    "scaffold"   TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_molecules_dataset_id ON silver.molecules ("dataset_id");

-- Physicochemical properties per molecule.
CREATE TABLE IF NOT EXISTS silver.properties (
    "id"              BIGSERIAL PRIMARY KEY,
    "dataset_id"      VARCHAR(128) NOT NULL,
    "smiles"          TEXT NOT NULL,
    "mol_weight"      DOUBLE PRECISION,
    "log_p"           DOUBLE PRECISION,
    "tpsa"            DOUBLE PRECISION,
    "hba"             INTEGER,
    "hbd"             INTEGER,
    "rotatable_bonds" INTEGER,
    "aromatic_rings"  INTEGER,
    "created_at"      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_properties_dataset_id ON silver.properties ("dataset_id");
