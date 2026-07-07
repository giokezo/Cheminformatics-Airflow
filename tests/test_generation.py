import pytest

from lib.cheminformatics.generation import (
    _assemble,
    _prepare_r_group,
    _prepare_scaffold,
    generate_molecules_frame,
)


def test_prepare_scaffold_numbers_attachment_points():
    mol, n_points = _prepare_scaffold('c1ccc(*)cc1')
    assert n_points == 1
    dummy_maps = sorted(a.GetAtomMapNum() for a in mol.GetAtoms() if a.GetAtomicNum() == 0)
    assert dummy_maps == [1]


def test_prepare_scaffold_rejects_missing_attachment_point():
    with pytest.raises(ValueError, match='no .* attachment points'):
        _prepare_scaffold('c1ccccc1')


def test_prepare_scaffold_rejects_invalid_smiles():
    with pytest.raises(ValueError, match='Invalid scaffold'):
        _prepare_scaffold('C1CC')


def test_prepare_r_group_requires_exactly_one_attachment_point():
    with pytest.raises(ValueError, match='exactly one'):
        _prepare_r_group('CC', 1)


def test_assemble_attaches_r_group_at_star():
    scaffold_mol, _ = _prepare_scaffold('c1ccc(*)cc1')
    smiles = _assemble(scaffold_mol, [_prepare_r_group('C*', 1)])
    assert smiles == 'Cc1ccccc1'


def test_generate_single_attachment_combinations():
    df, stats = generate_molecules_frame('d', ['c1ccc(*)cc1'], ['C*', 'CC*'], 1000)
    assert stats == {'attempted': 2, 'valid': 2, 'skipped': 0}
    assert set(df['smiles']) == {'Cc1ccccc1', 'CCc1ccccc1'}
    assert list(df.columns) == ['dataset_id', 'smiles', 'scaffold']
    assert (df['dataset_id'] == 'd').all()


def test_generate_deduplicates_identical_products():
    df, stats = generate_molecules_frame('d', ['c1ccc(*)cc1', 'c1ccc(*)cc1'], ['C*'], 1000)
    assert stats['valid'] == 1
    assert list(df['smiles']) == ['Cc1ccccc1']


def test_generate_respects_max_molecules_cap():
    df, stats = generate_molecules_frame('d', ['c1ccc(*)cc1'], ['C*', 'CC*', 'CCC*'], 2)
    assert stats['attempted'] == 2
    assert stats['valid'] <= 2


def test_generate_skips_invalid_r_groups():
    df, stats = generate_molecules_frame('d', ['c1ccc(*)cc1'], ['C*', 'CC'], 1000)
    assert stats['skipped'] == 1
    assert set(df['smiles']) == {'Cc1ccccc1'}
