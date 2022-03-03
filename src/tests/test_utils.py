import sys

sys.path.insert(0, '..')

from copy import deepcopy

from learnvcs.utils import cut, prune_tree
from lxml.builder import E
from lxml.etree import _Element, tostring

from common import Vector, VectorFailure


def serialize(element: _Element | None) -> str:
    if element is None:
        return None
    else:
        return tostring(element).decode('utf8')


def test_pruning():
    test_map = {
        E('div'): None,
        E('div', E('p', E('br'))): None,
        E('div', 'TEXT', E('b')): E('div', 'TEXT'),
        E('div', E('b'), 'TEXT'): E('div', 'TEXT'),
        E('span', 'FRONT ', E('span', 'MID'), ' END'):
            E('span', 'FRONT ', E('span', 'MID'), ' END'),
        E('div', E('span', 'whee')): E('div', E('span', 'whee'))
    }

    for test in test_map:
        expect = serialize(test_map[test])
        result = serialize(prune_tree(deepcopy(test)))
        if result != expect:
            raise VectorFailure(
                Vector(tostring(test).decode('utf8'), expect),
                result
            )
        else:
            print(f'PASS {serialize(test)}')


def test_cut():
    vectors: list[Vector] = [
        Vector(['ABC DEF'], ['ABC', 'DEF']),
        Vector(['ABC DEF', 'A B C'], ['ABC', 'DEF', 'A', 'B', 'C'])
    ]

    for test in vectors:
        result = cut(test.test, ' ')
        if result != test.expect:
            raise VectorFailure(test, result)
