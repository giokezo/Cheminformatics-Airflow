import itertools
import logging

import pandas as pd

from .constants import (
    DEFAULT_MAX_MOLECULES,
    DWH_CONN_ID,
    MAX_MOLECULES_VARIABLE,
    MOLECULES_TABLE,
    SILVER_SCHEMA,
)

logger = logging.getLogger(__name__)


def _attachment_points(mol):
    return [atom for atom in mol.GetAtoms() if atom.GetAtomicNum() == 0]


def _prepare_scaffold(scaffold_smiles):
    """Parse a scaffold and number its attachment points [*:1], [*:2], … for molzip."""
    from rdkit import Chem

    mol = Chem.MolFromSmiles(scaffold_smiles)
    if mol is None:
        raise ValueError(f'Invalid scaffold SMILES: {scaffold_smiles!r}')
    dummies = _attachment_points(mol)
    if not dummies:
        raise ValueError(f'Scaffold has no [*] attachment points: {scaffold_smiles!r}')
    for map_num, atom in enumerate(dummies, start=1):
        atom.SetAtomMapNum(map_num)
    return mol, len(dummies)


def _prepare_r_group(r_group_smiles, map_num):
    """Parse an R-group (exactly one attachment point) and tag its dummy with ``map_num``."""
    from rdkit import Chem

    mol = Chem.MolFromSmiles(r_group_smiles)
    if mol is None:
        raise ValueError(f'Invalid R-group SMILES: {r_group_smiles!r}')
    dummies = _attachment_points(mol)
    if len(dummies) != 1:
        raise ValueError(f'R-group must have exactly one [*] attachment point: {r_group_smiles!r}')
    dummies[0].SetAtomMapNum(map_num)
    return mol


def _assemble(scaffold_mol, r_group_mols):
    from rdkit import Chem

    combined = scaffold_mol
    for r_group_mol in r_group_mols:
        combined = Chem.CombineMols(combined, r_group_mol)
    product = Chem.molzip(combined)
    Chem.SanitizeMol(product)
    return Chem.MolToSmiles(product)


def generate_molecules_frame(dataset_id, scaffolds, r_groups, max_molecules):
    """Combinatorially attach R-groups to every scaffold attachment point.

    Returns (DataFrame[dataset_id, smiles, scaffold], stats). Invalid combinations are skipped;
    duplicate product SMILES are de-duplicated.
    """
    rows = []
    seen = set()
    attempted = skipped = 0

    for scaffold_smiles in scaffolds:
        scaffold_mol, n_points = _prepare_scaffold(scaffold_smiles)
        for combo in itertools.product(r_groups, repeat=n_points):
            if attempted >= max_molecules:
                logger.warning(f'Reached max_molecules cap ({max_molecules}); stopping early.')
                break
            attempted += 1
            try:
                r_group_mols = [_prepare_r_group(smiles, i) for i, smiles in enumerate(combo, start=1)]
                product_smiles = _assemble(scaffold_mol, r_group_mols)
            except Exception as error:
                logger.debug(f'Skipping combo {combo} on scaffold {scaffold_smiles!r}: {error}')
                skipped += 1
                continue
            if product_smiles in seen:
                continue
            seen.add(product_smiles)
            rows.append({'dataset_id': dataset_id, 'smiles': product_smiles, 'scaffold': scaffold_smiles})

    stats = {'attempted': attempted, 'valid': len(rows), 'skipped': skipped}
    logger.info(f'Generation complete: {stats}')
    return pd.DataFrame(rows, columns=['dataset_id', 'smiles', 'scaffold']), stats


def validate_inputs(params):
    from .artifacts import r_groups_key, raw_inputs_exist, scaffolds_key

    dataset_id = params['dataset_id']
    if not raw_inputs_exist(dataset_id):
        raise ValueError(
            f'Missing input files for dataset {dataset_id!r}: expected '
            f'{scaffolds_key(dataset_id)!r} and {r_groups_key(dataset_id)!r} in the raw bucket.'
        )
    logger.info(f'Input files present for dataset {dataset_id!r}')


def generate_molecules(params):
    from airflow.sdk import Variable

    from ..utils.warehouse import replace_dataset_rows
    from .artifacts import RAW_BUCKET, r_groups_key, read_smiles_list, scaffolds_key, write_results_csv

    dataset_id = params['dataset_id']
    max_molecules = int(Variable.get(MAX_MOLECULES_VARIABLE, DEFAULT_MAX_MOLECULES))

    scaffolds = read_smiles_list(RAW_BUCKET, scaffolds_key(dataset_id))
    r_groups = read_smiles_list(RAW_BUCKET, r_groups_key(dataset_id))
    logger.info(f'Loaded {len(scaffolds)} scaffolds and {len(r_groups)} R-groups for dataset {dataset_id!r}')

    df, stats = generate_molecules_frame(dataset_id, scaffolds, r_groups, max_molecules)
    if df.empty:
        raise ValueError('Generation produced 0 valid molecules. Check scaffolds and R-groups.')

    write_results_csv(df, dataset_id, 'molecules.csv')
    replace_dataset_rows(df, SILVER_SCHEMA, MOLECULES_TABLE, dataset_id, DWH_CONN_ID)
    logger.info(f"Loaded {stats['valid']} molecules into {SILVER_SCHEMA}.{MOLECULES_TABLE}")
