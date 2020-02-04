"""Tests the functions contained within utilities.py"""

import numpy as np
import pytest

import quantum_heom.utilities as util

# -------------------------------------------------------------------
# MATH-BASED FUNCTIONS
# -------------------------------------------------------------------

@pytest.mark.parametrize(
    'mat, ans',
    [(np.array([[0.5, 0.5], [0.5, 0.5]]), 1.0),
     (np.array([[2**(-1/2), 0], [0, 2**(-1/2)]]), 1.0)])
def test_trace_matrix_squared_pure(mat, ans):

    """
    Tests that the correct value of 1 is returned for the
    trace of matrix squared for matrices that mimic a pure
    density matrix (i.e. tr(rho^2) = 1).
    """

    assert np.isclose(util.trace_matrix_squared(mat), ans)


@pytest.mark.parametrize(
    'mat, ans',
    [(np.array([[0.5, 0], [0, 0.5]]), 0.5)])
def test_trace_matrix_squared_not_pure(mat, ans):

    """
    Tests that the correct value of 1 is returned for the
    trace of matrix squared for matrices that mimic an
    impure density matrix (i.e. tr(rho^2) < 1).
    """

    assert np.isclose(util.trace_matrix_squared(mat), ans)


@pytest.mark.parametrize(
    'mat_a, mat_b, ans',
    [(np.array([[0, 0], [0, 0]]),
      np.array([[0, 0], [0, 0]]),
      np.array([[0, 0], [0, 0]])),
     (np.array([[1, 0.3], [0.3, 1]]),
      np.array([[1, 0.3], [0.3, 1]]),
      np.array([[0, 0], [0, 0]]))])
def test_commutator_zero(mat_a, mat_b, ans):

    """
    Tests that the correct commutator of A and B is returned.
    """

    assert np.all(util.commutator(mat_a, mat_b) == ans)


@pytest.mark.parametrize(
    'mat_a, mat_b, ans',
    [(np.array([[0, 0], [0, 0]]),
      np.array([[0, 0], [0, 0]]),
      np.array([[0, 0], [0, 0]])),
     (np.array([[1, 0], [0, 1]]),
      np.array([[1, 0], [0, 1]]),
      np.array([[2, 0], [0, 2]]))])
def test_anti_commutator(mat_a, mat_b, ans):

    """
    Tests that the correct anti-commutator of A and B is returned.
    """

    assert np.all(util.commutator(mat_a, mat_b, anti=True) == ans)


def test_basis_change_identity():

    """
    Tests that the function maintains the expected behaviour that
    the identity matrix (and multiples of) is invariant under
    basis transformation.
    """


def test_basis_change():

    """
    Tests that the correct matrix is returned when performing a
    basis change.
    """

# -------------------------------------------------------------------
# OTHER FUNCTIONS
# -------------------------------------------------------------------

@pytest.mark.parametrize(
    'sites, els, exp',
    [(2, 'all', ['11', '12', '21', '22']),
     (2, 'diagonals', ['11', '22']),
     (2, 'off-diagonals', ['12', '21']),
     (3, 'all', ['11', '12', '13', '21', '22', '23', '31', '32', '33']),
     (3, 'diagonals', ['11', '22', '33']),
     (3, 'off-diagonals', ['12', '13', '21', '23', '31', '32'])])
def test_elements_from_str(sites, els, exp):

    """
    Tests that the correct output for numerical string
    representations of the elements of the denisty matrix
    from a keywrod description is returned.
    """

    assert np.all(util.elements_from_str(sites, els) == exp)


@pytest.mark.parametrize(
    'elements, expected',
    [(['11', '33', '99'], 'diagonals'),
     (['12', '67', '28'], 'off-diagonals'),
     (['11', '44', '98', '43'], 'both')])
def test_types_of_elements_from_list(elements, expected):

    """
    Tests whether elements in list format (i.e. ['11', '21', ...]
    etc) are correctly characterised.
    """

    assert util.types_of_elements(elements) == expected


@pytest.mark.parametrize(
    'elements, expected',
    [('diagonals', 'diagonals'),
     ('off-diagonals', 'off-diagonals'),
     ('all', 'both')])
def test_types_of_elements_from_list(elements, expected):

    """
    Tests whether elements in string format (i.e. 'all') are
    correctly characterised.
    """

    assert util.types_of_elements(elements) == expected


def test_types_of_elements_none_input():

    """
    Tests that None is returned if None is passed.
    """

    assert util.types_of_elements(None) is None
