import unittest

from tests.utils import generate_many_randoms


class TestGenerateManyRandoms(unittest.TestCase):
    def test_valid_input(self):
        # Test with valid inputs
        lows = [1, 10, 5]
        highs = [10, 20, 15]
        many = len(lows)
        result = list(generate_many_randoms(many, lows, highs))

        # Check that the length of the result matches the expected length
        self.assertEqual(len(result), many)

        # Check that each generated random number is within the specified range
        for i in range(many):
            self.assertGreaterEqual(result[i], lows[i])
            self.assertLessEqual(result[i], highs[i])

    def test_invalid_input_lengths(self):
        # Test with invalid input lengths
        lows = [1, 10, 5]
        highs = [10, 20]
        many = len(lows)

        # Check that ValueError is raised for mismatched array lengths
        with self.assertRaises(ValueError):
            generate_many_randoms(many, lows, highs)

    def test_empty_input(self):
        # Test with empty input arrays
        many = 0
        result = list(generate_many_randoms(many, [], []))

        # Check that the result is an empty list
        self.assertEqual(result, [])
