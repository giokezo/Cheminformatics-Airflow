import logging

import pandas as pd

from .constants import (
    CLUSTERS_TABLE,
    DEFAULT_FINGERPRINT,
    DEFAULT_N_CLUSTERS,
    DWH_CONN_ID,
    FINGERPRINT_VARIABLE,
    GOLD_SCHEMA,
    N_CLUSTERS_VARIABLE,
)
from .fingerprints import FingerprintFactory

logger = logging.getLogger(__name__)


def cluster_molecules_frame(dataset_id, smiles_values, fingerprint_name, n_clusters):
    """K-means cluster molecules by fingerprint. Returns DataFrame[dataset_id, smiles, cluster_id]."""
    import numpy as np
    from rdkit import Chem
    from sklearn.cluster import KMeans

    strategy = FingerprintFactory.create(fingerprint_name)

    smiles_list = []
    vectors = []
    for smiles in smiles_values:
        mol = Chem.MolFromSmiles(str(smiles))
        if mol is None:
            continue
        smiles_list.append(smiles)
        vectors.append(strategy.to_dense(mol))

    if not vectors:
        raise ValueError('No valid molecules to cluster.')

    matrix = np.vstack(vectors)
    effective_k = max(1, min(n_clusters, len(vectors)))
    logger.info(f'Clustering {len(vectors)} molecules into {effective_k} clusters ({fingerprint_name})')

    model = KMeans(n_clusters=effective_k, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)

    return pd.DataFrame({
        'dataset_id': dataset_id,
        'smiles': smiles_list,
        'cluster_id': labels.astype(int),
    })


def run_clustering(params):
    from airflow.sdk import Variable

    from ..utils.warehouse import replace_dataset_rows
    from .artifacts import read_results_csv, write_results_csv

    dataset_id = params['dataset_id']
    fingerprint_name = Variable.get(FINGERPRINT_VARIABLE, DEFAULT_FINGERPRINT)
    n_clusters = int(Variable.get(N_CLUSTERS_VARIABLE, DEFAULT_N_CLUSTERS))

    molecules = read_results_csv(dataset_id, 'molecules.csv')
    df = cluster_molecules_frame(dataset_id, molecules['smiles'], fingerprint_name, n_clusters)

    write_results_csv(df, dataset_id, 'clusters.csv')
    replace_dataset_rows(df, GOLD_SCHEMA, CLUSTERS_TABLE, dataset_id, DWH_CONN_ID)
    logger.info(f"Loaded {len(df)} cluster assignments into {GOLD_SCHEMA}.{CLUSTERS_TABLE}")
