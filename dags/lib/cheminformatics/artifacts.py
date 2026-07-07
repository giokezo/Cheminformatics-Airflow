import io

import pandas as pd

from ..utils.s3 import download_object, object_exists, upload_bytes
from .constants import (
    R_GROUPS_KEY_TEMPLATE,
    RAW_BUCKET,
    RESULTS_BUCKET,
    RESULTS_KEY_TEMPLATE,
    S3_CONN_ID,
    SCAFFOLDS_KEY_TEMPLATE,
    SMILES_COLUMN,
)


def scaffolds_key(dataset_id):
    return SCAFFOLDS_KEY_TEMPLATE.format(dataset_id=dataset_id)


def r_groups_key(dataset_id):
    return R_GROUPS_KEY_TEMPLATE.format(dataset_id=dataset_id)


def results_key(dataset_id, artifact):
    return RESULTS_KEY_TEMPLATE.format(dataset_id=dataset_id, artifact=artifact)


def raw_inputs_exist(dataset_id):
    return (
        object_exists(scaffolds_key(dataset_id), RAW_BUCKET, S3_CONN_ID)
        and object_exists(r_groups_key(dataset_id), RAW_BUCKET, S3_CONN_ID)
    )


def read_smiles_list(bucket, key):
    """Read a single-column SMILES CSV from S3 and return the cleaned, non-empty SMILES."""
    raw = download_object(key, bucket, S3_CONN_ID)
    df = pd.read_csv(io.BytesIO(raw))
    if SMILES_COLUMN not in df.columns:
        raise ValueError(f"Column '{SMILES_COLUMN}' not found in s3://{bucket}/{key}: {list(df.columns)}")
    return [s.strip() for s in df[SMILES_COLUMN].astype(str) if s and s.strip()]


def read_results_csv(dataset_id, artifact):
    raw = download_object(results_key(dataset_id, artifact), RESULTS_BUCKET, S3_CONN_ID)
    return pd.read_csv(io.BytesIO(raw))


def write_results_csv(df, dataset_id, artifact):
    key = results_key(dataset_id, artifact)
    upload_bytes(df.to_csv(index=False).encode('utf-8'), key, RESULTS_BUCKET, S3_CONN_ID)
    return key


def write_results_bytes(data, dataset_id, artifact):
    key = results_key(dataset_id, artifact)
    upload_bytes(data, key, RESULTS_BUCKET, S3_CONN_ID)
    return key
