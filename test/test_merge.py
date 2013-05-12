from __future__ import unicode_literals
from unittest import TestCase
from obraz import merge


class MergeTest(TestCase):
    def test_merge_dicts(self):
        x1 = {'a': {'x': 1, 'y': 2}, 'b': None}
        x2 = {'a': {'z': True}, 'c': [1, 2, 3]}
        res = {'a': {'x': 1, 'y': 2, 'z': True}, 'b': None, 'c': [1, 2, 3]}
        self.assertEqual(merge(x1, x2), res)
        self.assertRaises(ValueError, lambda: merge({'a': 1}, {'a': 2}))

    def test_merge_lists(self):
        self.assertEqual(merge([1], [2, 3]), [1, 2, 3])
        self.assertEqual(merge([[1, 2], [3]], [4]), [[1, 2], [3], 4])

    def test_merge_nested(self):
        x1 = {'a': [1, 2], 'b': [3, 4], 'c': {'k1': 'v1'}}
        x2 = {'a': [3, 4], 'z': [5, 6], 'c': {'k2': 'v2'}}
        res = {
            'a': [1, 2, 3, 4],
            'b': [3, 4],
            'c': {
                'k1': 'v1',
                'k2': 'v2',
            },
            'z': [5, 6],
        }
        self.assertEqual(merge(x1, x2), res)

    def test_merge_equal(self):
        self.assertEqual(merge(1, 1), 1)
        self.assertEqual(merge(True, True), True)

    def test_merge_not_equal(self):
        self.assertRaises(ValueError, lambda: merge(1, 2))
        self.assertRaises(ValueError, lambda: merge(1, 'foo'))
