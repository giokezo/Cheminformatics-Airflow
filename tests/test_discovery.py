from lib.cheminformatics.discovery import build_trigger_kwargs, find_dataset_pairs


def test_find_dataset_pairs_requires_both_files():
    keys = ['a_scaffolds.csv', 'a_r_groups.csv', 'b_scaffolds.csv', 'c_r_groups.csv', 'notes.txt']
    assert find_dataset_pairs(keys) == {'a'}


def test_find_dataset_pairs_multiple_complete():
    keys = ['x_scaffolds.csv', 'x_r_groups.csv', 'y_scaffolds.csv', 'y_r_groups.csv']
    assert find_dataset_pairs(keys) == {'x', 'y'}


def test_find_dataset_pairs_empty():
    assert find_dataset_pairs([]) == set()


def test_build_trigger_kwargs_is_unique_per_dataset_and_batch():
    out = build_trigger_kwargs(['a', 'b'], '20260707T000000')
    assert out == [
        {'conf': {'dataset_id': 'a'}, 'trigger_run_id': 'sched_a_20260707T000000'},
        {'conf': {'dataset_id': 'b'}, 'trigger_run_id': 'sched_b_20260707T000000'},
    ]
