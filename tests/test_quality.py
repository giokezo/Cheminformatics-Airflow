import pandas as pd
import pytest

from lib.cheminformatics.quality import validate_molecules_frame, validate_properties_frame


def test_valid_molecules_pass():
    df = pd.DataFrame({'dataset_id': ['d', 'd'], 'smiles': ['Cc1ccccc1', 'CCO']})
    validate_molecules_frame(df)


def test_molecules_reject_duplicate_smiles():
    df = pd.DataFrame({'dataset_id': ['d', 'd'], 'smiles': ['Cc1ccccc1', 'Cc1ccccc1']})
    with pytest.raises(Exception):
        validate_molecules_frame(df)


def test_molecules_reject_invalid_smiles():
    df = pd.DataFrame({'dataset_id': ['d', 'd'], 'smiles': ['Cc1ccccc1', 'C1CC']})
    with pytest.raises(Exception):
        validate_molecules_frame(df)


def test_valid_properties_pass():
    df = pd.DataFrame({
        'dataset_id': ['d'],
        'smiles': ['Cc1ccccc1'],
        'mol_weight': [92.14],
        'hba': [0],
        'hbd': [0],
    })
    validate_properties_frame(df)


def test_properties_reject_non_positive_weight():
    df = pd.DataFrame({
        'dataset_id': ['d'],
        'smiles': ['Cc1ccccc1'],
        'mol_weight': [0.0],
        'hba': [0],
        'hbd': [0],
    })
    with pytest.raises(Exception):
        validate_properties_frame(df)


def test_properties_reject_negative_hbd():
    df = pd.DataFrame({
        'dataset_id': ['d'],
        'smiles': ['Cc1ccccc1'],
        'mol_weight': [92.14],
        'hba': [0],
        'hbd': [-1],
    })
    with pytest.raises(Exception):
        validate_properties_frame(df)
