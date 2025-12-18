from utils import clean_number


def test_clean_number_basic():
    assert clean_number('(+1) 987-654-3210') == '19876543210'
    assert clean_number('919876543210') == '919876543210'
    assert clean_number('abc123') == '123'
