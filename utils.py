def clean_number(num):
    """Return only digits from `num` as a string.

    Always converts the input to str first to avoid type errors.
    """
    return ''.join(filter(str.isdigit, str(num)))
