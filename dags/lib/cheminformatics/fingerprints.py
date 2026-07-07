import abc

import numpy as np
from rdkit.Chem import AllChem, MACCSkeys
from rdkit.Chem.rdchem import Mol


class FingerprintStrategy(abc.ABC):
    n_bits: int

    @abc.abstractmethod
    def calculate(self, mol: Mol) -> list[int]:
        """Return indices of bits set in the fingerprint (sparse, for tmap)."""

    def to_dense(self, mol: Mol) -> np.ndarray:
        """Return the fingerprint as a dense 0/1 vector (for K-means)."""
        vector = np.zeros(self.n_bits, dtype=np.int8)
        vector[self.calculate(mol)] = 1
        return vector


class _MorganFingerprint(FingerprintStrategy):
    radius: int
    n_bits = 2048

    def calculate(self, mol: Mol) -> list[int]:
        bit_vect = AllChem.GetMorganFingerprintAsBitVect(mol, self.radius, nBits=self.n_bits)
        return list(bit_vect.GetOnBits())


class ECFP4Fingerprint(_MorganFingerprint):
    radius = 2


class ECFP6Fingerprint(_MorganFingerprint):
    radius = 3


class MACCSFingerprint(FingerprintStrategy):
    n_bits = 167

    def calculate(self, mol: Mol) -> list[int]:
        bit_vect = MACCSkeys.GenMACCSKeys(mol)
        return list(bit_vect.GetOnBits())


class FingerprintFactory:
    _strategies: dict[str, type[FingerprintStrategy]] = {
        'ECFP4': ECFP4Fingerprint,
        'ECFP6': ECFP6Fingerprint,
        'MACCS': MACCSFingerprint,
    }

    @classmethod
    def create(cls, name: str) -> FingerprintStrategy:
        strategy_class = cls._strategies.get(name)
        if not strategy_class:
            raise NotImplementedError(f'Unsupported fingerprint: {name}')
        return strategy_class()
