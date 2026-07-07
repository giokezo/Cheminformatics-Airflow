from datetime import timedelta

from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator, ShortCircuitOperator
from airflow.sdk import DAG, Param
from airflow.utils.trigger_rule import TriggerRule

from lib.cheminformatics.chemprop import predict_properties
from lib.cheminformatics.clustering import run_clustering
from lib.cheminformatics.constants import PROCESSING_DAG_ID
from lib.cheminformatics.faerun import build_faerun_graph
from lib.cheminformatics.generation import generate_molecules, validate_inputs
from lib.cheminformatics.properties import calculate_properties
from lib.cheminformatics.registry import record_processed
from lib.utils.teams import send_teams_alert


def _should_run_faerun(params):
    return bool(params.get('run_faerun'))


def _should_run_chemprop(params):
    return bool(params.get('run_chemprop'))


with DAG(
    dag_id=PROCESSING_DAG_ID,
    schedule=None,
    start_date=None,
    catchup=False,
    tags=['cheminformatics', 'de_school', 'processing'],
    params={
        'dataset_id': Param(default='sample', type='string'),
        'run_faerun': Param(default=False, type='boolean'),
        'run_chemprop': Param(default=False, type='boolean'),
    },
    dagrun_timeout=timedelta(minutes=30),
    default_args={
        'owner': 'data-platform',
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
        'on_failure_callback': send_teams_alert,
    },
) as dag:
    start_op = EmptyOperator(task_id='start')

    validate_inputs_op = PythonOperator(
        task_id='validate_inputs',
        python_callable=validate_inputs,
    )

    generate_molecules_op = PythonOperator(
        task_id='generate_molecules',
        python_callable=generate_molecules,
    )

    calculate_properties_op = PythonOperator(
        task_id='calculate_properties',
        python_callable=calculate_properties,
    )

    run_clustering_op = PythonOperator(
        task_id='run_clustering',
        python_callable=run_clustering,
    )

    record_processed_op = PythonOperator(
        task_id='record_processed',
        python_callable=record_processed,
    )

    faerun_gate_op = ShortCircuitOperator(
        task_id='faerun_gate',
        python_callable=_should_run_faerun,
    )

    build_faerun_op = PythonOperator(
        task_id='build_faerun',
        python_callable=build_faerun_graph,
    )

    chemprop_gate_op = ShortCircuitOperator(
        task_id='chemprop_gate',
        python_callable=_should_run_chemprop,
    )

    chemprop_op = PythonOperator(
        task_id='chemprop_predict',
        python_callable=predict_properties,
    )

    finish_op = EmptyOperator(
        task_id='finish',
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    start_op >> validate_inputs_op >> generate_molecules_op >> calculate_properties_op >> run_clustering_op
    run_clustering_op >> record_processed_op >> finish_op
    run_clustering_op >> faerun_gate_op >> build_faerun_op >> finish_op
    run_clustering_op >> chemprop_gate_op >> chemprop_op >> finish_op
