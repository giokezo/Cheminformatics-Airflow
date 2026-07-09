from airflow.providers.postgres.hooks.postgres import PostgresHook


def get_engine(conn_id):
    return PostgresHook(postgres_conn_id=conn_id).get_sqlalchemy_engine()


def replace_dataset_rows(df, schema, table, dataset_id, conn_id):
    """Idempotently load a dataset's rows: delete any existing rows for the dataset, then append.

    Makes re-runs and ``overwrite`` safe — a dataset is never double-loaded.
    """
    hook = PostgresHook(postgres_conn_id=conn_id)
    hook.run(
        f'DELETE FROM {schema}.{table} WHERE dataset_id = %s',
        parameters=(dataset_id,),
    )
    df.to_sql(table, hook.get_sqlalchemy_engine(), schema=schema, index=False, if_exists='append')
