"""Tests the functions that build the lindbladian operators."""

from scipy import constants

import numpy as np
import pytest

from quantum_heom.quantum_system import QuantumSystem, INTERACTION_MODELS

N_SITES = 3
SETTINGS = {'atomic_units': True,
            'interaction_model': 'nearest neighbour cyclic',
            'dynamics_model': 'local dephasing lindblad'}

@pytest.fixture
def qsys():

    """
    Returns a QuantumSystem object initialised with sites=N_SITES
    """

    return QuantumSystem(N_SITES, **SETTINGS)


def test_quantum_system_atomic_units_getter(qsys):

    """
    Tests that the correct value for atomic_units can be retrieved
    """

    assert qsys.atomic_units == SETTINGS['atomic_units']


def test_quantum_system_atomic_units_setter(qsys):

    """
    Tests that the correct value for atomic_units can be set
    """

    old = qsys.atomic_units
    qsys.atomic_units = not old
    assert qsys.atomic_units != old


@pytest.mark.parametrize('atomic_units, exp', [(True, 1.),
                                               (False, constants.hbar)])
def test_quantum_system_hbar_getter(atomic_units, exp, qsys):

    """
    Tests that the correct value for hbar is returned when
    working either in or out of atomic units.
    """

    qsys.atomic_units = atomic_units
    assert qsys._hbar == exp


def test_quantum_system_sites_getter(qsys):

    """
    Tests that the correct number of sites is returned as set upon
    initialisation.
    """

    assert qsys.sites == N_SITES


@pytest.mark.parametrize('sites', [1, 2, 3, 4, 5])
def test_quantum_system_sites_setter(sites, qsys):

    """
    Tests that the number of sites can be set after initialisation,
    and the correct value returned.
    """

    qsys.sites = sites
    assert qsys.sites == sites


@pytest.mark.parametrize('sites', [0, -1])
def test_quantum_system_sites_init_error(sites):

    """
    Tests that the number of sites can be set after initialisation,
    and the correct value returned.
    """

    with pytest.raises(ValueError):
        QuantumSystem(sites, **SETTINGS)


def test_quantum_system_interaction_model_getter(qsys):

    """
    Tests that the correct value for the interaction_model is
    returned upon setting it at initialisation
    """

    assert qsys.interaction_model == SETTINGS['interaction_model']


@pytest.mark.parametrize('model', INTERACTION_MODELS)
def test_quantum_system_interaction_model_setter(model, qsys):

    """
    Tests that the correct value for the interaction_model is
    returned upon setting it after initialisation
    """

    qsys.interaction_model = model
    assert qsys.interaction_model == model


@pytest.mark.parametrize('sites, expected', [(1, np.array([1])),
                                             (2, np.array([[0, 1], [1, 0]])),
                                             (3, np.array([[0, 1, 1],
                                                           [1, 0, 1],
                                                           [1, 1, 0]])),
                                             (4, np.array([[0, 1, 0, 1],
                                                           [1, 0, 1, 0],
                                                           [0, 1, 0, 1],
                                                           [1, 0, 1, 0]]))])
def test_hamiltonian_nearest_neighbour_cyclic(sites, expected):

    """
    Tests that the correct Hamiltonian for a cyclic system
    in the nearest neighbour model is constructed.
    """
    settings = {'atomic_units': True,
                'interaction_model': 'nearest neighbour cyclic',
                'dynamics_model': 'dephasing lindblad'}

    assert np.all(QuantumSystem(sites, **settings).hamiltonian == expected)


@pytest.mark.parametrize('sites, expected', [(1, np.array([[0]])),
                                             (2, np.array([[0, 1], [1, 0]])),
                                             (3, np.array([[0, 1, 0],
                                                           [1, 0, 1],
                                                           [0, 1, 0]])),
                                             (4, np.array([[0, 1, 0, 0],
                                                           [1, 0, 1, 0],
                                                           [0, 1, 0, 1],
                                                           [0, 0, 1, 0]]))])
def test_hamiltonian_nearest_neighbour_linear(sites, expected):

    """
    Tests that the correct Hamiltonian for a linear system
    in the nearest neighbour model is constructed.
    """

    settings = {'atomic_units': True,
                'interaction_model': 'nearest neighbour linear',
                'dynamics_model': 'dephasing lindblad'}
    assert np.all(QuantumSystem(sites, **settings).hamiltonian == expected)


@pytest.mark.parametrize('sites, exp', [(2, np.array([[0, -1, 1, 0],
                                                      [-1, 0, 0, 1],
                                                      [1, 0, 0, -1],
                                                      [0, 1, -1, 0]]) * -1.0j)])
def test_hamiltonian_superop(sites, exp):

    """
    Tests, given an input N x N Hamiltonian, that the correct
    Hamiltonian superoperator is constructed.
    """

    assert np.all(QuantumSystem(sites, **SETTINGS).hamiltonian_superop == exp)


@pytest.mark.parametrize('sites', [2, 4, 6])
def test_hamiltonian_superop_shape(sites, qsys):

    """
    Tests that the correct shape Hamiltonian superoperator is
    returned. Should be N^2 N^2, where N is the number of sites
    of the quantum system.
    """

    qsys.sites = sites
    assert qsys.hamiltonian_superop.shape == (sites**2, sites**2)


@pytest.mark.parametrize('sites, exp', [(2, np.array([[1, 0],
                                                      [0, 0]])),
                                        (4, np.array([[1, 0, 0, 0],
                                                      [0, 0, 0, 0],
                                                      [0, 0, 0, 0],
                                                      [0, 0, 0, 0]]))])
def test_initial_density_matrix(sites, exp, qsys):

    """
    Tests that the correct initial density matrix for the system
    is constructed, for a various number of sites.
    """

    qsys.sites = sites
    assert np.all(qsys.initial_density_matrix == exp)


@pytest.mark.parametrize('input, exp', [([1], np.array([[1, 0, 0, 0],
                                                        [0, 0, 0, 0],
                                                        [0, 0, 0, 0],
                                                        [0, 0, 0, 0]])),
                                        ([1, 1, 3, 2], np.array([[2, 0, 0, 0],
                                                                 [0, 1, 0, 0],
                                                                 [0, 0, 1, 0],
                                                                 [0, 0, 0, 0]])
                                                       * 0.25)])
def test_init_site_pop(input, exp, qsys):

    """
    Tests that the correct site populations are built in
    the initial density matrix for a 4-site system.
    """

    qsys.init_site_pop = input

    assert np.all(qsys.initial_density_matrix == exp)
