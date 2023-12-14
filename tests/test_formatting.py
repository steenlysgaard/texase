import pytest

from asetui.formatting import pbc_str_to_list

def test_pbc_str_to_list():
    # Test valid inputs
    assert pbc_str_to_list("TFT") == [True, False, True]
    assert pbc_str_to_list("FTF") == [False, True, False]
    assert pbc_str_to_list("TTT") == [True, True, True]
    assert pbc_str_to_list("FFF") == [False, False, False]

    # Test invalid inputs
    with pytest.raises(TypeError):
        pbc_str_to_list(123)  # type: ignore
