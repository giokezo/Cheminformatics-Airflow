import logging

import pandas as pd

from .constants import DWH_CONN_ID, PROPERTIES_TABLE, SILVER_SCHEMA

logger = logging.getLogger(__name__)

PROPERTY_NAMES = ['mol_weight', 'log_p', 'tpsa', 'hba', 'hbd', 'rotatable_bonds', 'aromatic_rings']


def _property_functions():
    from rdkit.Chem import Descriptors, rdMolDescriptors

    return {
        'mol_weight': Descriptors.MolWt,
        'log_p': Descriptors.MolLogP,
        'tpsa': Descriptors.TPSA,
        'hba': rdMolDescriptors.CalcNumHBA,
        'hbd': rdMolDescriptors.CalcNumHBD,
        'rotatable_bonds': rdMolDescriptors.CalcNumRotatableBonds,
        'aromatic_rings': rdMolDescriptors.CalcNumAromaticRings,
    }


def calculate_properties_frame(dataset_id, smiles_values):
    """Compute the physicochemical property set for each valid SMILES."""
    from rdkit import Chem

    property_functions = _property_functions()
    rows = []
    failed = 0
    for smiles in smiles_values:
        mol = Chem.MolFromSmiles(str(smiles))
        if mol is None:
            failed += 1
            continue
        row = {'dataset_id': dataset_id, 'smiles': smiles}
        for name, function in property_functions.items():
            row[name] = round(function(mol), 4)
        rows.append(row)

    if failed:
        logger.warning(f'Skipped {failed} molecules with invalid SMILES during property calculation')
    columns = ['dataset_id', 'smiles', *PROPERTY_NAMES]
    return pd.DataFrame(rows, columns=columns)


def calculate_properties(params):
    from ..utils.warehouse import replace_dataset_rows
    from .artifacts import read_results_csv, write_results_csv

    dataset_id = params['dataset_id']
    molecules = read_results_csv(dataset_id, 'molecules.csv')

    df = calculate_properties_frame(dataset_id, molecules['smiles'])
    if df.empty:
        raise ValueError('Property calculation produced 0 rows.')

    write_results_csv(df, dataset_id, 'properties.csv')
    replace_dataset_rows(df, SILVER_SCHEMA, PROPERTIES_TABLE, dataset_id, DWH_CONN_ID)
    logger.info(f'Calculated properties for {len(df)} molecules in dataset {dataset_id!r}')
