import pytest
from rdkit import Chem

from lib.cheminformatics.fingerprints import (
    ECFP4Fingerprint,
    FingerprintFactory,
    MACCSFingerprint,
)

MOL = Chem.MolFromSmiles('Cc1ccccc1')


def test_factory_creates_known_strategies():
    assert isinstance(FingerprintFactory.create('ECFP4'), ECFP4Fingerprint)
    assert isinstance(FingerprintFactory.create('MACCS'), MACCSFingerprint)


def test_factory_rejects_unknown_strategy():
    with pytest.raises(NotImplementedError):
        FingerprintFactory.create('does-not-exist')


def test_to_dense_has_expected_shape_and_is_binary():
    ecfp = ECFP4Fingerprint().to_dense(MOL)
    assert ecfp.shape == (2048,)
    assert set(ecfp.tolist()).issubset({0, 1})

    maccs = MACCSFingerprint().to_dense(MOL)
    assert maccs.shape == (167,)


def test_calculate_returns_valid_on_bit_indices():
    on_bits = ECFP4Fingerprint().calculate(MOL)
    assert on_bits
    assert all(0 <= bit < 2048 for bit in on_bits)
