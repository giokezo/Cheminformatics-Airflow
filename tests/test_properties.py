from lib.cheminformatics.properties import PROPERTIES, calculate_properties_frame


def test_columns_match_property_set():
    df = calculate_properties_frame('d', ['Cc1ccccc1'])
    assert list(df.columns) == ['dataset_id', 'smiles', *PROPERTIES.keys()]


def test_values_are_physically_sane():
    df = calculate_properties_frame('d', ['Cc1ccccc1', 'OCc1ccccc1'])
    assert len(df) == 2
    assert (df['mol_weight'] > 0).all()
    assert (df['hba'] >= 0).all()
    assert (df['hbd'] >= 0).all()

    benzyl_alcohol = df[df['smiles'] == 'OCc1ccccc1'].iloc[0]
    assert benzyl_alcohol['hbd'] == 1
    assert benzyl_alcohol['hba'] == 1


def test_invalid_smiles_are_skipped():
    df = calculate_properties_frame('d', ['Cc1ccccc1', 'C1CC'])
    assert list(df['smiles']) == ['Cc1ccccc1']
