from datetime import timedelta

from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import DAG, Param
from airflow.utils.trigger_rule import TriggerRule

from lib.cheminformatics.constants import PROCESSING_DAG_ID, SCHEDULER_DAG_ID
from lib.cheminformatics.discovery import discover_new_datasets, summarize_batch
from lib.utils.teams import send_teams_alert

with DAG(
    dag_id=SCHEDULER_DAG_ID,
    schedule='@weekly',
    start_date=None,
    catchup=False,
    tags=['cheminformatics', 'de_school', 'scheduler'],
    params={
        'overwrite': Param(default=False, type='boolean'),
    },
    dagrun_timeout=timedelta(hours=2),
    default_args={
        'owner': 'data-platform',
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
        'on_failure_callback': send_teams_alert,
    },
) as dag:
    discover_datasets_op = PythonOperator(
        task_id='discover_datasets',
        python_callable=discover_new_datasets,
    )

    trigger_processing_op = TriggerDagRunOperator.partial(
        task_id='trigger_processing',
        trigger_dag_id=PROCESSING_DAG_ID,
        wait_for_completion=False,
    ).expand_kwargs(discover_datasets_op.output)

    summarize_op = PythonOperator(
        task_id='summarize',
        python_callable=summarize_batch,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    discover_datasets_op >> trigger_processing_op >> summarize_op
