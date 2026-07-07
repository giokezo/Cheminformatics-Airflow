import pytest

from lib.cheminformatics.clustering import cluster_molecules_frame

SMILES = ['Cc1ccccc1', 'CCc1ccccc1', 'CCCc1ccccc1', 'O=C(C)c1ccccc1']


def test_one_label_per_molecule():
    df = cluster_molecules_frame('d', SMILES, 'ECFP4', 2)
    assert len(df) == len(SMILES)
    assert list(df.columns) == ['dataset_id', 'smiles', 'cluster_id']
    assert set(df['cluster_id'].unique()).issubset({0, 1})


def test_effective_k_is_capped_at_molecule_count():
    df = cluster_molecules_frame('d', SMILES[:2], 'ECFP4', 10)
    assert df['cluster_id'].nunique() <= 2


def test_invalid_only_input_raises():
    with pytest.raises(ValueError, match='No valid molecules'):
        cluster_molecules_frame('d', ['C1CC'], 'ECFP4', 2)
