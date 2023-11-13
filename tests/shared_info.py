user_dct = {"str_key": "hav", "float_key": 4.2, "int_key": 42}
cell = [2, 2, 2]
pbc = [1, 1, 0]

test_atoms = ['Au', 'Ag']

def get_column_labels(columns) -> list:
    return [str(c.label) for c in columns.values()]

