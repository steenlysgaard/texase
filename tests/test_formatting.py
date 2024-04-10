import pytest

import numpy as np

from texase.formatting import pbc_str_to_array, is_numpy_array, string_to_list, convert_str_to_other_type


def test_pbc_str_to_array():
    # Test valid inputs
    assert np.all(pbc_str_to_array("TFT") == np.array([True, False, True]))
    assert np.all(pbc_str_to_array("FTF") == np.array([False, True, False]))
    assert np.all(pbc_str_to_array("TTT") == np.array([True, True, True]))
    assert np.all(pbc_str_to_array("FFF") == np.array([False, False, False]))

    # Test invalid inputs
    with pytest.raises(AttributeError):
        pbc_str_to_array(123)  # type: ignore


# Test cases for numbers
def test_numbers():
    assert is_numpy_array("[10 20 30]") == True
    assert is_numpy_array("np.array([10, 20, 30])") == True
    assert is_numpy_array("[10 20, 30]") == False  # Mixed separators
    assert is_numpy_array("np.array(10, 20, 30)") == False  # Missing brackets


# Test cases for floats
def test_floats():
    assert is_numpy_array("[10.5 20.6 30.7]") == True
    assert is_numpy_array("np.array([10.5, 20.6, 30.7])") == True
    assert is_numpy_array("[10.5 20, 30.7]") == False  # Mixed separators
    assert is_numpy_array("np.array(10.5, 20.6, 30.7)") == False  # Missing brackets


# Test cases for strings
def test_strings():
    assert is_numpy_array('["apple", "banana", "cherry"]') == False  # commas
    assert is_numpy_array('np.array(["apple", "banana", "cherry"])') == True
    assert is_numpy_array('["apple" "banana" "cherry"]') == True
    assert (
        is_numpy_array('np.array("apple", "banana", "cherry")') == False
    )  # Missing brackets


# Test cases for mixed types
def test_mixed_types():
    assert is_numpy_array('np.array([10, "apple", 20])') == False
    assert is_numpy_array('[10 "apple" 20]') == False

    
def test_string_to_list_with_numbers():
    assert string_to_list('[10 20 30]') == [10, 20, 30]
    assert string_to_list('np.array([10 20 30])') == [10, 20, 30]

def test_string_to_list_with_strings():
    assert string_to_list('["a" "b" "c"]') == ['a', 'b', 'c']
    assert string_to_list('np.array(["a", "b", "c"])') == ['a', 'b', 'c']

@pytest.mark.parametrize("test_input,expected", [
    ('[1, 2, 3]', [1, 2, 3]),
    ('{"key": "value"}', {"key": "value"}),
    ('{"a": {"b": 2}}', {"a": {"b": 2}}),
    ('"a string"', "a string"),
    ('123', 123),
    ('12.3', 12.3),
    ('True', True),
    ('None', None),
    ('(1, 2, 3)', (1, 2, 3)),
])
def test_convert_str_to_other_type(test_input, expected):
    assert convert_str_to_other_type(test_input) == expected

@pytest.mark.parametrize("test_input,expected", [
    ('np.array([1, 2, 3])', np.array([1, 2, 3])),
    ('np.array(["a", "b", "c"])', np.array(["a", "b", "c"])),
])
def test_convert_str_to_array_types(test_input, expected):
    assert np.all(convert_str_to_other_type(test_input) == expected)
    
# # You can also add tests for invalid inputs to ensure the function raises exceptions as expected
# @pytest.mark.parametrize("invalid_input", [
#     'not a valid input',
#     '[1, 2, 3',  # Missing closing bracket
#     'np.array(1, 2, 3)',  # Incorrect numpy array format
#     # Add more invalid test cases as needed
# ])
# def test_invalid_input(invalid_input):
#     with pytest.raises(ValueError):
#         convert_str_to_other_type(invalid_input)
    
