import io
import logging
import os
import tempfile
import zipfile

import pandas as pd

from .constants import DEFAULT_FINGERPRINT, FINGERPRINT_VARIABLE
from .fingerprints import FingerprintFactory

logger = logging.getLogger(__name__)

LAYOUT_K = 100
DEFAULT_PLOT_NAME = 'tmap'
EXCLUDED_COLOR_COLUMNS = ('smiles', 'scaffold', 'dataset_id')


def _build_lsh_forest(fingerprints):
    import tmap as tm

    enc = tm.Minhash()
    lsh = tm.LSHForest()
    vectors = [tm.VectorUint(fp) for fp in fingerprints]
    lsh.batch_add(enc.batch_from_sparse_binary_array(vectors))
    lsh.index()
    return lsh


def _layout_from_forest(lsh, k):
    import tmap as tm

    config = tm.LayoutConfiguration()
    config.k = k
    x, y, s, t, _ = tm.layout_from_lsh_forest(lsh, config=config)
    return list(x), list(y), list(s), list(t)


def _numeric_property_columns(df):
    return [
        col for col in df.columns
        if col not in EXCLUDED_COLOR_COLUMNS and pd.api.types.is_numeric_dtype(df[col])
    ]


def _build_faerun_plot(x, y, s, t, df, plot_name):
    from faerun import Faerun

    labels = list(df['smiles'].astype(str))
    numeric_cols = _numeric_property_columns(df)
    if numeric_cols:
        c_series = [df[col].tolist() for col in numeric_cols]
        series_titles = numeric_cols
    else:
        c_series = [[0] * len(df)]
        series_titles = ['default']

    faerun = Faerun(view='front', coords=False, clear_color='#222222')
    faerun.add_scatter(
        plot_name,
        {'x': x, 'y': y, 'c': c_series, 'labels': labels},
        colormap='rainbow',
        point_scale=5.0,
        max_point_size=20,
        shader='smoothCircle',
        has_legend=True,
        series_title=series_titles,
        legend_title=series_titles,
        label_index=0,
        title_index=0,
    )
    faerun.add_tree(
        f'{plot_name}_tree',
        {'from': s, 'to': t},
        point_helper=plot_name,
        color='#666666',
    )
    return faerun


def _zip_files(file_paths):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in file_paths:
            zf.write(path, arcname=os.path.basename(path))
    return buf.getvalue()


def build_graph_archive(fingerprints, df, plot_name=DEFAULT_PLOT_NAME, layout_k=LAYOUT_K):
    """Build the tmap + faerun visualization and return the HTML+JS as a zip archive."""
    effective_k = min(layout_k, max(1, len(fingerprints) - 1))
    logger.info(f'Building tmap layout for {len(fingerprints)} molecules (k={effective_k})')
    lsh = _build_lsh_forest(fingerprints)
    x, y, s, t = _layout_from_forest(lsh, k=effective_k)

    faerun = _build_faerun_plot(x, y, s, t, df, plot_name)
    with tempfile.TemporaryDirectory() as tmpdir:
        faerun.plot(plot_name, path=tmpdir, template='smiles')
        html_path = os.path.join(tmpdir, f'{plot_name}.html')
        js_path = os.path.join(tmpdir, f'{plot_name}.js')
        return _zip_files([html_path, js_path])


def build_faerun_graph(params):
    from airflow.sdk import Variable
    from rdkit import Chem

    from ..utils.smiles import split_valid_invalid
    from .artifacts import read_results_csv, write_results_bytes

    dataset_id = params['dataset_id']
    fingerprint_name = Variable.get(FINGERPRINT_VARIABLE, DEFAULT_FINGERPRINT)

    df = read_results_csv(dataset_id, 'molecules.csv')
    try:
        properties = read_results_csv(dataset_id, 'properties.csv').drop(columns=['dataset_id'])
        df = df.merge(properties, on='smiles', how='left')
    except Exception as error:
        logger.warning(f'Properties not available for coloring, continuing without them: {error}')

    valid_df, invalid_df = split_valid_invalid(df)
    if valid_df.empty:
        raise ValueError('No valid molecules to visualize.')
    if not invalid_df.empty:
        logger.warning(f'Excluding {len(invalid_df)} invalid molecules from the graph')

    strategy = FingerprintFactory.create(fingerprint_name)
    fingerprints = [strategy.calculate(Chem.MolFromSmiles(s)) for s in valid_df['smiles']]

    archive = build_graph_archive(fingerprints, valid_df)
    key = write_results_bytes(archive, dataset_id, 'graph.zip')
    logger.info(f'Faerun graph written to {key}')
