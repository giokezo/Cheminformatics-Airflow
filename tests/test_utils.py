import pandas as pd

from lib.utils.dataframe import normalize_columns
from lib.utils.smiles import is_valid_smiles, split_valid_invalid


def test_is_valid_smiles():
    assert is_valid_smiles('Cc1ccccc1')
    assert not is_valid_smiles('C1CC')
    assert not is_valid_smiles('')
    assert not is_valid_smiles(None)


def test_split_valid_invalid():
    df = pd.DataFrame({'smiles': ['Cc1ccccc1', 'C1CC', 'CCO']})
    valid, invalid = split_valid_invalid(df)
    assert list(valid['smiles']) == ['Cc1ccccc1', 'CCO']
    assert list(invalid['smiles']) == ['C1CC']


def test_normalize_columns():
    df = pd.DataFrame(columns=['Mol Weight', 'HBA #', 'smiles'])
    assert list(normalize_columns(df).columns) == ['mol_weight', 'hba', 'smiles']
