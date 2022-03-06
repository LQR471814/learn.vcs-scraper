import sys

sys.path.insert(0, '..')

from copy import deepcopy

from learnvcs.utils import cut, get_next, prune_tree
from lxml.builder import E
from lxml.etree import _Element, tostring

from common import Vector, VectorFailure


def serialize(element: _Element | None) -> str | None:
    if element is None:
        return None
    else:
        return tostring(element).decode('utf8')


def nodes_equal(e1: _Element | None, e2: _Element | None) -> bool:
    return serialize(e1) == serialize(e2)


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
        result = prune_tree(deepcopy(test))
        if not nodes_equal(result, test_map[test]):
            raise VectorFailure(
                Vector(serialize(test), serialize(test_map[test])),
                serialize(result)
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


def test_getnext():
    vectors: list[Vector] = [
        Vector(
            (E('div',
                E('div', target := E('b')),
                expect := E('span', 'text')
               ), target),
            expect
        ),
        Vector(
            (E('div',
                target := E('b'),
                expect := E('span', 'text')
               ), target),
            expect
        ),
        Vector(
            (E('div', target := E('b')), target),
            None
        ),
    ]

    for test in vectors:
        result = get_next(test.test[1])
        if result != test.expect:
            raise VectorFailure(test, result)
