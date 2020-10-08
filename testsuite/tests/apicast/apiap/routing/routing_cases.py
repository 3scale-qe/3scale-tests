"""
Test cases that are specifying paths that are used to connect product with backend
"""


def path_valid_chars():
    """Path valid characters that are used in test cases"""
    return ["-", "_", "~", "!", "&", ",", ";", "=", "@", "/"]


def case_default_get():
    """Default test that checks routing with /get path"""
    return ['/get']


def case_url_valid_chars():
    """
    Array of paths '/foo{p}bar', where p is each char of path valid characters
    Regression: THREESCALE-4937
    """
    return [f"/foo{char}bar" for char in path_valid_chars()]


def case_url_valid_chars_in_two_directories():
    """
    Array of paths '/foo{p}bar/foo{p}bar', where p is each char of path valid characters
    Regression: THREESCALE-4937
    """
    return [f"/foo{char}bar/foo{char}bar" for char in path_valid_chars()]
