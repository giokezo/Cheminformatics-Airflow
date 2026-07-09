import logging

from .constants import DWH_CONN_ID, GOLD_SCHEMA, PROCESSED_TABLE

logger = logging.getLogger(__name__)


def notify_success(params):
    from airflow.providers.postgres.hooks.postgres import PostgresHook

    from ..utils.teams import send_success_card

    dataset_id = params['dataset_id']
    hook = PostgresHook(postgres_conn_id=DWH_CONN_ID)
    row = hook.get_first(
        f'SELECT n_molecules, n_clusters FROM {GOLD_SCHEMA}.{PROCESSED_TABLE} WHERE dataset_id = %s',
        parameters=(dataset_id,),
    )
    n_molecules, n_clusters = row if row else (0, 0)

    send_success_card(
        'Cheminformatics pipeline complete',
        [
            ('Dataset', dataset_id),
            ('Molecules', n_molecules),
            ('Clusters', n_clusters),
            ('Faerun', 'yes' if params.get('run_faerun') else 'no'),
            ('ChemProp', 'yes' if params.get('run_chemprop') else 'no'),
        ],
    )
    logger.info(f'Sent success notification for dataset {dataset_id!r}')
