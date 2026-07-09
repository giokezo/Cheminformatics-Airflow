import logging

from .constants import (
    CLUSTERS_CHECKS_FILE,
    GOLD_DATA_SOURCE,
    MOLECULES_CHECKS_FILE,
    PROPERTIES_CHECKS_FILE,
    SILVER_DATA_SOURCE,
)

logger = logging.getLogger(__name__)


def validate_molecules_frame(df):
    """Pandera schema for generated molecules: non-null, unique, RDKit-parseable SMILES."""
    import pandera.pandas as pa
    from rdkit import Chem

    schema = pa.DataFrameSchema(
        {
            'dataset_id': pa.Column(str, nullable=False),
            'smiles': pa.Column(
                str,
                nullable=False,
                unique=True,
                checks=pa.Check(lambda s: Chem.MolFromSmiles(str(s)) is not None, element_wise=True),
            ),
        },
        strict=False,
    )
    schema.validate(df, lazy=True)


def validate_properties_frame(df):
    """Pandera schema for calculated properties: sane, non-negative physicochemical values."""
    import pandera.pandas as pa

    schema = pa.DataFrameSchema(
        {
            'dataset_id': pa.Column(str, nullable=False),
            'smiles': pa.Column(str, nullable=False),
            'mol_weight': pa.Column(float, checks=pa.Check.gt(0), coerce=True),
            'hba': pa.Column(int, checks=pa.Check.ge(0), coerce=True),
            'hbd': pa.Column(int, checks=pa.Check.ge(0), coerce=True),
        },
        strict=False,
    )
    schema.validate(df, lazy=True)


def molecules_quality(params):
    from ..utils.soda import run_soda_scan
    from .artifacts import read_results_csv

    dataset_id = params['dataset_id']
    validate_molecules_frame(read_results_csv(dataset_id, 'molecules.csv'))
    run_soda_scan(SILVER_DATA_SOURCE, MOLECULES_CHECKS_FILE, variables={'dataset_id': dataset_id})
    logger.info(f'Molecules quality checks passed for dataset {dataset_id!r}')


def properties_quality(params):
    from ..utils.soda import run_soda_scan
    from .artifacts import read_results_csv

    dataset_id = params['dataset_id']
    validate_properties_frame(read_results_csv(dataset_id, 'properties.csv'))
    run_soda_scan(SILVER_DATA_SOURCE, PROPERTIES_CHECKS_FILE, variables={'dataset_id': dataset_id})
    logger.info(f'Properties quality checks passed for dataset {dataset_id!r}')


def clustering_quality(params):
    from ..utils.soda import run_soda_scan

    dataset_id = params['dataset_id']
    run_soda_scan(GOLD_DATA_SOURCE, CLUSTERS_CHECKS_FILE, variables={'dataset_id': dataset_id})
    logger.info(f'Clustering quality checks passed for dataset {dataset_id!r}')
