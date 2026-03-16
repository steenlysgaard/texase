import numpy as np

from ase.db import connect
from ase.calculators.singlepoint import SinglePointCalculator
from ase import Atoms

# First some elements known from organic chemistry
organic_elements = ['H', 'C', 'N', 'O', 'F', 'Cl', 'Br', 'I']  
# Then some metals from the 3rd row of the periodic table
metals = ['Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn']
# And some more metals
metals += ['Pt', 'Au', 'Hg', 'Pd', 'Ru', 'Rh', 'Os', 'Ir', 'Ag', 'Cd']

rng = np.random.default_rng(seed=123)

with connect('example.db') as db:
    for _ in range(30):
        # Choose three of one metal and one additional metal
        chosen_metals = rng.choice(metals, size=2, replace=False)
        symbols = [chosen_metals[0]] * 3 + [chosen_metals[1]]

        # Choose three different organic elements
        chosen_organic = rng.choice(organic_elements, size=3, replace=False)
        # With a random number between 1 and 3 of each
        numbers = rng.integers(1, 4, size=3)
        # Add those to the formula
        for element, number in zip(chosen_organic, numbers):
            symbols += [element] * number

        atoms = Atoms(symbols, pbc=True,
                      cell=rng.uniform(10, 20, size=3),
                      positions=rng.uniform(0, 10, size=(len(symbols), 3)))

        # Add a string kvp with one of foo, bar, baz and a kvp with a number between 10 and 100
        kvps = {'state': rng.choice(['foo', 'bar', 'baz']), 'strength': rng.integers(10, 101)}

        atoms_forces = rng.uniform(0, 0.05, size=(len(symbols), 3))
        calc = SinglePointCalculator(atoms, energy=rng.uniform(-100, 0), forces=atoms_forces)
        atoms.calc = calc
        db.write(atoms, key_value_pairs=kvps)
