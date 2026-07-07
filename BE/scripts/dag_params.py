from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DagParams(BaseModel):
    """Base for all DAG params: forbid unknown fields so bad params are caught."""
    model_config = ConfigDict(extra='forbid')


class CheminformaticsParams(DagParams):
    dataset_id: str
    run_faerun: bool = False
    run_chemprop: bool = False


class CheminformaticsSchedulerParams(DagParams):
    overwrite: bool = False


# dag_id -> params model
DAG_PARAMS: dict[str, type[DagParams]] = {
    'cheminformatics_dag': CheminformaticsParams,
    'cheminformatics_scheduler_dag': CheminformaticsSchedulerParams,
}
