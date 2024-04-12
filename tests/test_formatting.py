import pytest

import numpy as np

from texase.formatting import (
    pbc_str_to_array,
    is_numpy_array,
    string_to_list,
    convert_str_to_other_type,
    convert_value_to_int_float_or_bool, check_pbc_string_validity, correctly_typed_kvp
)


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
    assert string_to_list("[10 20 30]") == [10, 20, 30]
    assert string_to_list("np.array([10 20 30])") == [10, 20, 30]


def test_string_to_list_with_strings():
    assert string_to_list('["a" "b" "c"]') == ["a", "b", "c"]
    assert string_to_list('np.array(["a", "b", "c"])') == ["a", "b", "c"]


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("[1, 2, 3]", [1, 2, 3]),
        ('{"key": "value"}', {"key": "value"}),
        ('{"a": {"b": 2}}', {"a": {"b": 2}}),
        ('"a string"', "a string"),
        ("123", 123),
        ("12.3", 12.3),
        ("True", True),
        ("None", None),
        ("(1, 2, 3)", (1, 2, 3)),
    ],
)
def test_convert_str_to_other_type(test_input, expected):
    assert convert_str_to_other_type(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("np.array([1, 2, 3])", np.array([1, 2, 3])),
        ('np.array(["a", "b", "c"])', np.array(["a", "b", "c"])),
    ],
)
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


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("123", 123),  # int
        ("45.67", 45.67),  # float
        ("true", True),  # bool True
        ("false", False),  # bool False
        ("text", "text"),  # string
        ("123text", "123text"),  # alphanumeric string
        ("", ""),  # empty string
        ("None", "None"),  # string 'None'
        ("0", 0),  # zero as int
        ("0.0", 0.0),  # zero as float
        ("True", True),  # case-insensitive bool True
        ("False", False),  # case-insensitive bool False
    ],
)
def test_convert_value_to_int_float_or_bool(test_input, expected):
    assert convert_value_to_int_float_or_bool(test_input) == expected
    assert isinstance(convert_value_to_int_float_or_bool(test_input), type(expected))

@pytest.mark.parametrize("test_input,expected_exception,expected_message", [
    ("TFF", None, None),  # valid string
    ("tff", None, None),  # valid lowercase string
    ("TF", ValueError, "TF does not have exactly three characters!"),  # short string
    ("TFFT", ValueError, "TFFT does not have exactly three characters!"),  # long string
    ("TXF", ValueError, "TXF contains characters that are not T or F!"),  # invalid character
    ("123", ValueError, "123 contains characters that are not T or F!"),  # numbers
    ("", ValueError, " does not have exactly three characters!"),  # empty string
    ("True", ValueError, "True does not have exactly three characters!")  # word
])
def test_check_pbc_string_validity(test_input, expected_exception, expected_message):
    if expected_exception:
        with pytest.raises(expected_exception) as excinfo:
            check_pbc_string_validity(test_input)
        assert str(excinfo.value) == expected_message
    else:
        assert check_pbc_string_validity(test_input) is True    

@pytest.mark.parametrize("test_input,expected", [
    ("key1=123", ("key1", 123)),  # int
    ("key2=45.67", ("key2", 45.67)),  # float
    ("key3=true", ("key3", True)),  # bool True
    ("key4=false", ("key4", False)),  # bool False
    ("key5=text", ("key5", "text")),  # string
    (" key6 = 123text ", ("key6", "123text")),  # alphanumeric string with whitespace
    ("key7=", ("key7", "")),  # empty value
    ("key8=None", ("key8", "None")),  # string 'None'
    (" key9 = 0 ", ("key9", 0)),  # zero as int with whitespace
    ("key10=0.0", ("key10", 0.0)),  # zero as float
    ("key11=True", ("key11", True)),  # case-insensitive bool True
    ("key12=False", ("key12", False)),  # case-insensitive bool False
])
def test_correctly_typed_kvp(test_input, expected):
    assert correctly_typed_kvp(test_input) == expected
