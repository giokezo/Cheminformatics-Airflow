# Airflow connections
S3_CONN_ID = 'aws_s3'
DWH_CONN_ID = 'dwh_connection'

# Airflow variables (with defaults, so the pipeline runs out of the box)
N_CLUSTERS_VARIABLE = 'chem_n_clusters'
FINGERPRINT_VARIABLE = 'chem_fingerprint'
MAX_MOLECULES_VARIABLE = 'chem_max_molecules'
DEFAULT_N_CLUSTERS = 5
DEFAULT_FINGERPRINT = 'ECFP4'
DEFAULT_MAX_MOLECULES = 50_000

# Object storage
RAW_BUCKET = 'raw'
RESULTS_BUCKET = 'results'
SCAFFOLDS_SUFFIX = '_scaffolds.csv'
R_GROUPS_SUFFIX = '_r_groups.csv'
SCAFFOLDS_KEY_TEMPLATE = '{dataset_id}' + SCAFFOLDS_SUFFIX
R_GROUPS_KEY_TEMPLATE = '{dataset_id}' + R_GROUPS_SUFFIX
RESULTS_KEY_TEMPLATE = 'datasets/{dataset_id}/{artifact}'

# Input CSV layout (both files are a single SMILES column)
SMILES_COLUMN = 'smiles'

# Warehouse (silver / gold layers)
SILVER_SCHEMA = 'silver'
MOLECULES_TABLE = 'molecules'
PROPERTIES_TABLE = 'properties'
GOLD_SCHEMA = 'gold'
CLUSTERS_TABLE = 'clusters'
PROCESSED_TABLE = 'processed_datasets'

# Soda data-quality checks (data source name + checks file under soda/cheminformatics/)
SILVER_DATA_SOURCE = 'cheminformatics_silver'
GOLD_DATA_SOURCE = 'cheminformatics_gold'
SILVER_CHECKS_FILE = 'cheminformatics/checks_silver.yml'
GOLD_CHECKS_FILE = 'cheminformatics/checks_gold.yml'

# DAG ids (the scheduler DAG fans out into runs of the processing DAG)
PROCESSING_DAG_ID = 'cheminformatics_dag'
SCHEDULER_DAG_ID = 'cheminformatics_scheduler_dag'
