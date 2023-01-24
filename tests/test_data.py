from asetui.data import format_value

def test_format_value_string():
    assert format_value("hello") == "hello"

def test_format_value_float():
    returned_text = format_value(1.23456)
    assert str(returned_text) == "1.23"
    assert returned_text.justify == "right"
    assert str(format_value(0.0000123456)) == "1.23e-05"

def test_format_value_int():
    assert str(format_value(123)) == "123"

def test_format_value_other():
    assert format_value(None) == "None"
