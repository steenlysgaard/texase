from textual.validation import Function

from texase.formatting import convert_str_to_other_type


def contains_equals_sign(value: str) -> bool:
    return "=" in value


def not_only_whitespace(value: str) -> bool:
    for input in value.split("="):
        if not input.strip():
            return False
    return True


def no_comma(value: str) -> bool:
    return "," not in value


def can_be_interpreted_only_as_str_number_or_bool(value: str) -> bool:
    """Return True if the value can be interpreted as something else
    than a string, floating point number, integer or boolean."""
    new_value = convert_str_to_other_type(value.split("=")[-1].strip())
    return isinstance(new_value, (str, float, int, bool))


kvp_validators_edit = [
    Function(not_only_whitespace, "The key or value can't be only whitespace!"),
    Function(
        no_comma,
        "The key or value can't contain a comma! Only one key-value pair can be added at a time.",
    ),
    Function(
        can_be_interpreted_only_as_str_number_or_bool,
        "The value can be interpreted as something other than a string, number or boolean.",
    ),
]

kvp_validators_add = kvp_validators_edit + [
    Function(contains_equals_sign, "Must contain '='"),
]
