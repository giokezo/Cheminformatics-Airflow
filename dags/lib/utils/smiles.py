from rdkit import Chem


def is_valid_smiles(smiles):
    """True when RDKit can parse the SMILES into a molecule."""
    if not smiles or not str(smiles).strip():
        return False
    return Chem.MolFromSmiles(str(smiles).strip()) is not None


def split_valid_invalid(df, smiles_column='smiles'):
    """Split a DataFrame into (valid, invalid) frames by RDKit-parseability of the SMILES column."""
    mask = df[smiles_column].apply(is_valid_smiles)
    return df[mask].reset_index(drop=True), df[~mask].reset_index(drop=True)
