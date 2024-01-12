import pytest

import numpy as np

from texase.formatting import pbc_str_to_array

def test_pbc_str_to_array():
    # Test valid inputs
    assert np.all(pbc_str_to_array("TFT") == np.array([True, False, True]))
    assert np.all(pbc_str_to_array("FTF") == np.array([False, True, False]))
    assert np.all(pbc_str_to_array("TTT") == np.array([True, True, True]))
    assert np.all(pbc_str_to_array("FFF") == np.array([False, False, False]))

    # Test invalid inputs
    with pytest.raises(AttributeError):
        pbc_str_to_array(123)  # type: ignore
