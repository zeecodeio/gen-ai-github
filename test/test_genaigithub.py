from genaigithub.subsequence import Subsequence


def test_subsquence():
    subsequence = Subsequence([5, 1, 22, 25, 6, -1, 8, 10], [1, 6, -1, 10])
    subsequence.validate()
    assert subsequence.is_valid is True


def test_validate_invalid_subsequence():
    subsequence = Subsequence([5, 1, 22, 25, 6, -1, 8, 10], [1, 6, 10, -1])
    subsequence.validate()
    assert subsequence.is_valid is False


def test_validate_empty_sequence():
    subsequence = Subsequence([5, 1, 22, 25, 6, -1, 8, 10], [])
    subsequence.validate()
    assert subsequence.is_valid is True


def test_validate_empty_array():
    subsequence = Subsequence([], [1, 6, -1, 10])
    subsequence.validate()
    assert subsequence.is_valid is False


def test_validate_empty_array_and_sequence():
    subsequence = Subsequence([], [])
    subsequence.validate()
    assert subsequence.is_valid is True


def test_validate_subsequence_with_identical_elements():
    subsequence = Subsequence([1, 1, 1, 1], [1, 1])
    subsequence.validate()
    assert subsequence.is_valid is True


def test_validate_subsequence_with_non_consecutive_elements():
    subsequence = Subsequence([1, 2, 3, 4], [2, 4])
    subsequence.validate()
    assert subsequence.is_valid is True


def test_validate_subsequence_at_end():
    subsequence = Subsequence([1, 2, 3, 4], [3, 4])
    subsequence.validate()
    assert subsequence.is_valid is True
