import logging
from datetime import datetime, timezone

from .constants import R_GROUPS_SUFFIX, RAW_BUCKET, S3_CONN_ID, SCAFFOLDS_SUFFIX

logger = logging.getLogger(__name__)


def _ids_with_suffix(keys, suffix):
    return {key[: -len(suffix)] for key in keys if key.endswith(suffix)}


def find_dataset_pairs(keys):
    """Return dataset ids that have BOTH a scaffolds and an r_groups file in the given keys."""
    scaffolds = _ids_with_suffix(keys, SCAFFOLDS_SUFFIX)
    r_groups = _ids_with_suffix(keys, R_GROUPS_SUFFIX)
    return scaffolds & r_groups


def build_trigger_kwargs(dataset_ids, stamp):
    """Map dataset ids to TriggerDagRunOperator kwargs with a unique run id per dataset per batch."""
    return [
        {'conf': {'dataset_id': dataset_id}, 'trigger_run_id': f'sched_{dataset_id}_{stamp}'}
        for dataset_id in dataset_ids
    ]


def discover_new_datasets(params):
    from ..utils.s3 import list_keys
    from .registry import list_processed_datasets

    overwrite = bool(params.get('overwrite'))
    keys = list_keys(RAW_BUCKET, S3_CONN_ID)
    pairs = find_dataset_pairs(keys)
    logger.info(f'Found {len(pairs)} complete dataset pair(s) in the raw bucket: {sorted(pairs)}')

    if overwrite:
        selected = sorted(pairs)
        logger.info(f'overwrite=True: reprocessing all {len(selected)} dataset(s)')
    else:
        processed = set(list_processed_datasets())
        selected = sorted(pairs - processed)
        logger.info(f'{len(processed)} already processed; {len(selected)} new to process: {selected}')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    return build_trigger_kwargs(selected, stamp)


def summarize_batch(ti):
    kwargs_list = ti.xcom_pull(task_ids='discover_datasets') or []
    dataset_ids = [item['conf']['dataset_id'] for item in kwargs_list]
    logger.info(f'Dispatched {len(dataset_ids)} dataset run(s): {dataset_ids}')
