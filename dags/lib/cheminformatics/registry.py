import logging

from airflow.providers.postgres.hooks.postgres import PostgresHook

from .constants import (
    CLUSTERS_TABLE,
    DWH_CONN_ID,
    GOLD_SCHEMA,
    MOLECULES_TABLE,
    PROCESSED_TABLE,
    SILVER_SCHEMA,
)

logger = logging.getLogger(__name__)


def list_processed_datasets():
    """Return the ids of datasets already processed (present in the registry)."""
    hook = PostgresHook(postgres_conn_id=DWH_CONN_ID)
    records = hook.get_records(f'SELECT dataset_id FROM {GOLD_SCHEMA}.{PROCESSED_TABLE}')
    return [row[0] for row in records]


def record_processed(params):
    dataset_id = params['dataset_id']
    hook = PostgresHook(postgres_conn_id=DWH_CONN_ID)

    n_molecules = hook.get_first(
        f'SELECT count(*) FROM {SILVER_SCHEMA}.{MOLECULES_TABLE} WHERE dataset_id = %s',
        parameters=(dataset_id,),
    )[0]
    n_clusters = hook.get_first(
        f'SELECT count(DISTINCT cluster_id) FROM {GOLD_SCHEMA}.{CLUSTERS_TABLE} WHERE dataset_id = %s',
        parameters=(dataset_id,),
    )[0]

    hook.run(
        f'''
        INSERT INTO {GOLD_SCHEMA}.{PROCESSED_TABLE} (dataset_id, n_molecules, n_clusters, processed_at)
        VALUES (%s, %s, %s, now())
        ON CONFLICT (dataset_id) DO UPDATE SET
            n_molecules = EXCLUDED.n_molecules,
            n_clusters = EXCLUDED.n_clusters,
            processed_at = now()
        ''',
        parameters=(dataset_id, n_molecules, n_clusters),
    )
    logger.info(f'Recorded dataset {dataset_id!r} in registry ({n_molecules} molecules, {n_clusters} clusters)')
