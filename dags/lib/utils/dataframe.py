def normalize_columns(df):
    """Lower-case and snake-case column names (e.g. 'Mol Weight' -> 'mol_weight')."""
    return df.rename(
        lambda column_name: column_name.lower().replace(' ', '_').replace('#', '_').strip('_'),
        axis='columns',
    )
