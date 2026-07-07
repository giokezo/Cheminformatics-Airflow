import logging

from .artifacts import read_results_csv, write_results_csv

logger = logging.getLogger(__name__)


def predict_properties(params):
    """Optional ChemProp property prediction — STUB.

    A real implementation would load a trained ChemProp model (or train one) and predict properties
    for the generated molecules. ChemProp pulls in torch and is heavy, so this ships as a stub that
    writes a placeholder artifact and marks the extension point.
    """
    dataset_id = params['dataset_id']
    molecules = read_results_csv(dataset_id, 'molecules.csv')

    predictions = molecules[['dataset_id', 'smiles']].copy()
    predictions['prediction'] = None
    predictions['model'] = 'chemprop-stub'

    # TODO: replace with real ChemProp inference (load checkpoint, predict, fill `prediction`).
    write_results_csv(predictions, dataset_id, 'predictions.csv')
    logger.warning(f'ChemProp is a stub — wrote placeholder predictions for {len(predictions)} molecules')
