"""Contains functions to plot the time evolution of the quantum system."""

from itertools import permutations, product

from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
import numpy as np

import utilities as util


def complex_space_time(qsys, view_3d: bool = True,
                       elements: [np.array, str] = 'diagonals',
                       save_as: str = None,) -> np.array:

    """
    Creates a 3D plot of time vs imaginary vs real-amplitude.
    Used to plot the time-evolution of the diagonal and off-diagonal
    elements of the density matrix for a quantum system.

    Parameters
    ----------
    qsys : QuantumSystem
        The QuantumSystem object that defines the system and
        its dynamics.
    view_3d : bool
        If true, views the plot in 3d, showing real and imaginary
        amplitude axes as well as time. If false, only shows the
        real amplitude axis with time as a 2d plot.
    elements : str, or list of str
        The elements of the density matrix whose time-evolution
        should be plotted. Can be passed as a string, choosing
        either 'all', 'diagonals' (default), 'off-diagonals'.
        Can also be passed as a list, where each string element
        in is of the form 'nm', where n is the row index and m
        the column. For example, for a 2-site quantum system,
        all elements are plotted by either passing elements='all'
        or elements=['11', '12', '21', '22'].
    """

    # Check elements input
    if isinstance(elements, list):
        assert len(elements) <= qsys.sites ** 2, (
            'The number of elements plotted must be a positive integer less'
            ' than or equal to the number of elements in the density matrix.')
        for element in elements:
            try:
                int(element)
            except ValueError:
                raise ValueError('Invalid format of string representation of'
                                 ' density matrix element.')
    elif isinstance(elements, str):
        assert elements in ['all', 'diagonals', 'off-diagonals'], (
            'Must choose from "all", "diagonals", or "off-diagonals".')
        if elements == 'all':
            elements = [str(i) + str(j)
                        for i, j in product(range(1, qsys.sites + 1), repeat=2)]
        elif elements == 'diagonals':
            elements = [str(i) + str(i) for i in range(1, qsys.sites + 1)]
        else:  # off-diagonals
            elements = [str(i) + str(j)
                        for i, j in permutations(range(1, qsys.sites + 1), 2)]
    else:
        raise ValueError('elements argument passed as invalid value.')

    # Process time evolution data
    times = np.empty(len(qsys.time_evolution), dtype=float)
    tr_rho_sq = np.empty(len(qsys.time_evolution), dtype=float)
    matrix_data = {element: np.empty(len(qsys.time_evolution), dtype=float)
                   for element in elements}
    for t_idx, (t, rho_t, trace) in enumerate(qsys.time_evolution, start=0):
        times[t_idx] = t * 1E15  # convert s --> fs
        tr_rho_sq[t_idx] = np.real(trace)
        for element in elements:
            n, m = int(element[0]), int(element[1])
            value = rho_t[n - 1][m - 1]
            if n == m:  # diagonal element; retrieve real part of amplitude
                matrix_data[element][t_idx] = np.real(value)
            else:  # off-diagonal; retrieve imaginary part of amplitude
                matrix_data[element][t_idx] = np.imag(value)
    # Initialize plots
    if view_3d:
        ax = plt.figure(figsize=(25, 15))
        ax = plt.axes(projection='3d')
    else:
        ax = plt.figure(figsize=(15, 10))
        ax = plt
    # Plot the data
    zeros = np.zeros(len(qsys.time_evolution), dtype=float)
    for element, amplitudes in matrix_data.items():
        if int(element[0]) == int(element[1]):
            label = '$\\rho_{' + element + '}$'
            if view_3d:
                ax.plot3D(times, zeros, amplitudes, ls='-', label=label)
            else:
                ax.plot(times, amplitudes, ls='-', label=label)
        else:
            label = '$\\rho_{' + element + '}$'
            if view_3d:
                ax.plot3D(times, amplitudes, zeros, ls='-', label=label)
    # Plot tr(rho^2) and asymptote at 1 / N or thermal_eq
    if view_3d:
        ax.plot3D(times, zeros, tr_rho_sq, dashes=[1, 1],
                  label='$tr(\\rho^2)$')
        if qsys.dynamics_model.endswith('thermalising lindblad'):
            ax.plot3D(times, zeros,
                      util.get_trace_matrix_squared(qsys.thermal_eq_state),
                      c='gray', ls='--', label='$z = tr(\\rho_{eq}^2)$')
        else:
            ax.plot3D(times, zeros, 1/qsys.sites, c='gray', ls='--',
                      label='$z = \\frac{1}{N}$')
    else:  # 2D plot
        ax.plot(times, tr_rho_sq, dashes=[1, 1], label='$tr(\\rho^2)$')
        if qsys.dynamics_model.endswith('thermalising lindblad'):
            ax.plot(times,
                    [util.get_trace_matrix_squared(qsys.thermal_eq_state)]
                    * len(times),
                    c='gray', ls='--', label='$z = tr(\\rho_{eq}^2)$')
        else:
            ax.plot(times, [1/qsys.sites] * len(times), c='gray',
                    ls='--', label='$y = \\frac{1}{N}$')
    # Format plot
    label_size = '15'
    title_size = '20'
    title = ('Time evolution of a ' + qsys.interaction_model + ' '
             + str(qsys.sites) + '-site system modelled with '
             + qsys.dynamics_model + ' dynamics. \n(dt = '
             + str(qsys.time_interval * 1E15) + ' $fs$, $\\Gamma$ = '
             + str(qsys.decay_rate * 1E-12) + ' $rad\ ps^{-1})$')
    if view_3d:
        plt.legend(loc='center left', fontsize='large')
        ax.set_xlabel('time / fs', size=label_size, labelpad=30)
        ax.set_ylabel('Imaginary Site Population', size=label_size, labelpad=30)
        ax.set_zlabel('Real Site Population', size=label_size, labelpad=10)
        ax.set_title(title, size=title_size, pad=20)
        ax.view_init(20, -50)
    else:  # 2D plot
        plt.legend(loc='center right', fontsize='large', borderaxespad=-10.)
        ax.xlabel('time / fs', size=label_size, labelpad=20)
        ax.ylabel('Site Population', size=label_size, labelpad=20)
        ax.title(title, size=title_size, pad=20)
    if save_as:
        plt.savefig(save_as)


def site_cartesian_coordinates(N: int) -> np.array:

    """
    Returns an array of site coordinates on an xy plane
    for an N-site system, where the coordinates represent
    the vertices of an N-sided regular polygon with its
    centre at the origin.
    """

    assert N > 1

    r = 5  # distance of each site from the origin

    site_coords = np.empty(N, dtype=tuple)
    site_coords[0] = (0, r)
    for i in range(1, N):

        phi = i * 2 * np.pi / N  # internal angle of the N-sided polygon
        site_coords[i] = (r * np.sin(phi), r * np.cos(phi))

    return site_coords
