"""Contains functions to plot the dynamics and spectral densities
of the quantum system.
Functions:
    plot_dynamics
        Plot the dynamics of one or more QuantumSystem objects.
    plot_spectral_density
        Plot the spectral densities of one or more QuantumSystem
        objects.
    """

import os
from typing import Optional

from math import ceil
from mpl_toolkits import mplot3d
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import numpy as np

from quantum_heom import bath
from quantum_heom import evolution as evo
from quantum_heom import utilities as util
from quantum_heom.bath import SPECTRAL_DENSITIES
from quantum_heom.evolution import TEMP_INDEP_MODELS, TEMP_DEP_MODELS

TRACE_MEASURES = ['squared', 'distance']

def plot_dynamics(systems, elements: [list, str] = None,
                  coherences: str = 'imag', trace_measure: list = None,
                  asymptote: bool = False, view_3d: bool = False,
                  save: bool = False):

    """
    Plots the dynamics of multiple QuantumSystem objects for the
    specified elements of the density matrix, in either 2D or 3D.
    Can plot matrix elements with or without plotting the trace
    measures of the systems (i.e. trace squared or trace distance),
    or just the trace metric(s) on their own. Can also just plot
    1 QuantumSystem.

    Parameters
    ----------
    systems : list of QuantumSystem
        A list of systems whose data is to be plotted.
    elements : list or None
        The density matrix elements of systems to plot. Can be a
        list of form ['11', '21', ...], as a string of the form
        'all', 'diagonals', or 'off-diagonals', or just passed as
        None to plot none of the elements. Default is None.
    coherences : str or list of str
        Which components of the density matrix coherences to plot.
        Can be both, either, or neither of 'real', 'imag'. Must
        specify some coherences in elements (i.e. 'all' or
        'off-diagonals' or ['21', '12'] for this to take effect.
        Default is 'imag'.
    trace_measure : str or list of str or None
        The trace measure
    asymptote : bool
        If True, plots an asymptote on the real axis at 1/N, where
        N is the number of sites in qsys.
    view_3d : bool
        If True, formats the axes in 3D, otherwise just formats
        in 2D. Default is False.
    save : bool
        If True, saves a .pdf figure in the quantum_HEOM/doc/figures
        relative directory of this package, as a .pdf file with a
        descriptive filename. Also saves a .txt file of the same
        name that contains all the arguments used to define the
        systems and plot the dynamics, in Python-copyable format for
        reproducibility. If False, does no saving.
    """

    # ----------------------------------------------------------------------
    # CHECK INPUTS
    # ----------------------------------------------------------------------
    if not isinstance(systems, list):
        systems = [systems]
    assert systems, 'Must pass a QuantumSystem to plot dynamics for.'
    # Check the sites, timesteps, and time_intervals are the same for all
    # systems passed
    if len(systems) > 1:
        site_check = [sys.sites for sys in systems]
        timestep_check = [sys.timesteps for sys in systems]
        interval_check = [sys.time_interval for sys in systems]
        for var, name in [(site_check, 'sites'),
                          (timestep_check, 'timesteps'),
                          (interval_check, 'time_interval')]:
            assert var.count(var[0]) == len(var), ('For all systems passed the '
                                                   + name + ' must be'
                                                   ' the same.')
    sites = systems[0].sites
    # Checks the elements input, and convert to i.e. ['11', '21', ...] format
    elements = util.elements_from_str(sites, elements)
    if isinstance(coherences, str):
        assert coherences in ['real', 'imag'], ('Must pass coherences as either'
                                                ' "real" or "imag", or a list'
                                                ' containing both.')
        coherences = [coherences]
    elif isinstance(coherences, list):
        assert all(item in ['real', 'imag'] for item in coherences)
    else:
        raise ValueError('Invalid type for passing coherences')
    # Check trace_measure
    if isinstance(trace_measure, str):
        assert trace_measure in TRACE_MEASURES, ('Must choose a trace measure'
                                                 ' from ' + str(TRACE_MEASURES))
        trace_measure = [trace_measure]
    elif trace_measure is None:
        trace_measure = [trace_measure]
    elif isinstance(trace_measure, list):
        assert all(item in TRACE_MEASURES for item in trace_measure)
    # Check view_3d, asymptote, save
    assert isinstance(view_3d, bool), 'view_3d must be passed as a bool'
    assert isinstance(asymptote, bool), 'asymptote must be passed as a bool'
    assert isinstance(save, bool), 'save must be passed as a bool'
    # ----------------------------------------------------------------------
    # PROCESS AND PLOT DATA
    # ----------------------------------------------------------------------
    # Determine whether multiple systems will be plotted (affects labelling)
    multiple = len(systems) > 1
    # Initialise axes
    if view_3d:  # 3D PLOT
        ratio, scaling = 1.8, 6
        figsize = (ratio * scaling, scaling)
        axes = plt.figure(figsize=figsize)
        axes = plt.axes(projection='3d')
    else:  # 2D PLOT
        ratio, scaling = 1.7, 5
        figsize = (ratio * scaling, scaling)
        _, axes = plt.subplots(figsize=figsize)
    # Process and plot
    for sys in systems:
        time_evo = sys.time_evolution
        processed = evo.process_evo_data(time_evo, elements, trace_measure)
        times = processed[0]
        axes = _plot_data(axes, processed, sys, multiple, elements,
                          coherences, asymptote, view_3d)
        axes = _format_axes(axes, sys, elements, times, view_3d)
    # ----------------------------------------------------------------------
    # SAVE PLOT
    # ----------------------------------------------------------------------
    # Save the figure in a .pdf and the arguments used in a .txt
    if save:
        plot_args = {'elements': elements,
                     'coherences': coherences,
                     'trace_measure': trace_measure,
                     'asymptote': asymptote,
                     'view_3d': view_3d,
                     'save': save,
                    }
        save_figure_and_args(systems, plot_args, plot_type='dynamics')
    plt.show()

def _plot_data(ax, processed, qsys, multiple: bool, elements: list,
               coherences: str, asymptote: bool, view_3d: bool):

    """
    Takes an initialised set of matplotlib axes and plots the time
    evolution data of the QuantumSystem object qsys passed, in a
    2D or 3D plot.

    Parameters
    ----------
    ax : matplotlib.axes._subplots.AxesSubplot
        The matplotlib axes to be formatted.
    processed : tuple
        The processed time evolution data of the qsys QuantumSystem
        as produced by the evolution.process_evo_data() method.
        Contains times, matrix_data, and trace metrics (squared and
        distance).
    qsys : QuantumSystem
        The system whose data is being plotted.
    multiple : bool
        If True, indicates that multiple QuantumSystems are being
        plotted on the same axes.
    elements : list or None
        The elements of qsys's density matrix that have been
        plotted. Can be a list of form ['11', '21', ...] or
        just passed as None if no elements have been plotted.
    coherences : str or list of str
        Which components of the density matrix coherences to plot.
        Can be both, either, or neither of 'real', 'imag'.
    asymptote : bool
        If True, plots an asymptote on the real axis at 1/N, where
        N is the number of sites in qsys.
    view_3d : bool
        If True, formats the axes in 3D, otherwise just formats
        in 2D.

    Returns
    -------
    ax : matplotlib.axes._subplots.AxesSubplot
        The input axes, but formatted.
    """

    # Unpack the processed data
    times, matrix_data, squared, distance = processed
    zeros = np.zeros(len(times), dtype=float)
    # Get the types of elements; 'diagonals', 'off-diagonals', or 'both'
    elem_types = util.types_of_elements(elements)
    linewidth = 2.
    if matrix_data is not None:
        # -------------------------------------------------------------------
        # PLOT MATRIX ELEMENTS
        # -------------------------------------------------------------------
        for idx, (elem, amplitudes) in enumerate(matrix_data.items(), start=0):
            # Configure the line's label
            if elem_types == 'diagonals':
                label = ('BChl ' + elem[0] if qsys.interaction_model == 'FMO'
                         else 'Site ' + elem[0])
            else:
                label = '$\\rho_{' + elem + '}$'
            if multiple:
                labels = {'local dephasing lindblad': 'Local Deph.',
                          'global thermalising lindblad': 'Global Therm.',
                          'local thermalising lindblad': 'Local Therm.',
                          'HEOM': 'HEOM',
                          'ohmic': 'Ohmic',
                          'debye': 'Debye',
                         }
                lines = {'local dephasing lindblad':
                         ['-', 'red', 'indianred', 'coral', 'lightcoral'],
                         'global thermalising lindblad':
                         {'debye': ['-', 'blueviolet', 'mediumpurple', 'violet',
                                    'thistle'],
                          'ohmic': ['-', 'thistle', 'violet', 'mediumpurple',
                                    'blueviolet'],
                         },
                         'local thermalising lindblad':
                         {'debye': ['-', 'forestgreen', 'limegreen',
                                    'springgreen', 'lawngreen'],
                          'ohmic': ['-', 'lawngreen', 'springgreen',
                                    'limegreen', 'forestgreen'],
                         },
                         # 'HEOM': ['--', 'k', 'dimgray', 'silver', 'lightgrey'],
                         'HEOM':
                         {'debye': ['--', 'mediumblue', 'royalblue',
                                    'lightsteelblue', 'deepskyblue']
                         },
                        }
                if qsys.dynamics_model == 'local dephasing lindblad':
                    # Local dephasing model doesn't use a spectral density
                    label += (' (' + labels[qsys.dynamics_model] + ')')
                    style = lines[qsys.dynamics_model][0]
                    colour = lines[qsys.dynamics_model][(idx % 4) + 1]
                else:
                    label += (' (' + labels[qsys.dynamics_model] + ', '
                              + labels[qsys.spectral_density] + ')')
                    style = lines[qsys.dynamics_model][qsys.spectral_density][0]
                    colour = lines[qsys.dynamics_model]
                    colour = colour[qsys.spectral_density][(idx % 4) + 1]
            else:
                style = '-'
                colour = None
            # Plot matrix elements
            if int(elem[0]) == int(elem[1]):  # diagonal; TAKE REAL
                args = ((zeros, np.real(amplitudes))
                        if view_3d else (np.real(amplitudes),))
                ax.plot(times, *args, ls=style, c=colour,
                        linewidth=linewidth, label=label)
            else:  # off-diagonal
                if 'real' in coherences:
                    if multiple:
                        lab = ('Re(' + label[:label.rfind('(') - 1]
                               + ')' + label[label.rfind('(') - 1:])
                    else:
                        lab = 'Re(' + label + ')'
                    args = ((np.real(amplitudes), zeros)
                            if view_3d else (np.real(amplitudes),))
                    ax.plot(times, *args, ls=style, c=colour,
                            linewidth=linewidth, label=lab)
                if 'imag' in coherences:
                    if multiple:
                        lab = ('Im(' + label[:label.rfind('(') - 1]
                               + ')' + label[label.rfind('(') - 1:])
                    else:
                        lab = 'Im(' + label + ')'
                    args = ((np.imag(amplitudes), zeros)
                            if view_3d else (np.imag(amplitudes),))
                    ax.plot(times, *args, ls=style, c=colour,
                            linewidth=linewidth, label=lab)
    # -------------------------------------------------------------------
    # PLOT TRACE METRICS
    # -------------------------------------------------------------------
    if squared is not None:
        args = ((zeros, squared) if view_3d else (squared,))
        ax.plot(times, *args, dashes=[1, 1], linewidth=linewidth,
                c='gray', label='$tr(\\rho^2)$')
    if distance is not None:
        args = ((zeros, distance) if view_3d else (distance,))
        ax.plot(times, *args, dashes=[3, 1], linewidth=linewidth,
                c='gray', label='$0.5\\ tr\\ |\\rho(t) - \\rho^{eq}|$')
    if asymptote:
        asym = [1 / qsys.sites] * len(times)
        args = ((zeros, asym) if view_3d else (asym,))
        ax.plot(times, *args, ls='--', linewidth=linewidth, c='gray',
                label='$y = \\frac{1}{N}$')
    return ax

def _format_axes(ax, qsys, elements: [list, None], times: np.array,
                 view_3d: bool):

    """
    Formats pre-existing axis. For use by the plot_dynamics()
    method, after the _plot_data() method has been used.

    Parameters
    ----------
    ax : matplotlib.axes._subplots.AxesSubplot
        The matplotlib axes to be formatted.
    qsys : QuantumSystem
        The quantum system whose data is being plotted.
    elements : list or None
        The elements of qsys's density matrix that have been
        plotted. Can be a list of form ['11', '21', ...] or
        just passed as None if no elements have been plotted.
    times : np.array of float
        Array of times over which the dynamics of qsys have
        plotted.
    view_3d : bool
        If True, formats the axes in 3D, otherwise just formats
        in 2D.

    Returns
    -------
    ax : matplotlib.axes._subplots.AxesSubplot
        The input axes, but formatted.
    """

    # Get the types of elements; 'diagonals', 'off-diagonals', or 'both'
    elem_types = util.types_of_elements(elements)
    # Define parameters
    label_size = '25'
    # Apply formatting
    if view_3d:
        # Set axes labels
        ax.legend(loc='center left', fontsize='x-large')
        ax.set_xlabel('Time / fs', size=label_size, labelpad=30)
        ax.set_ylabel('Coherences', size=label_size, labelpad=30)
        ax.set_zlabel('Site Population', size=label_size, labelpad=10)
        ax.view_init(20, -50)
        # Format axes ranges
        upper_bound = list(ax.get_xticks())[5]
        ax.xaxis.set_minor_locator(MultipleLocator(upper_bound / 20))
        ax.set_ylim(top=0.5, bottom=-0.5)
        ax.set_zlim(top=1., bottom=0.)
        ax.yaxis.set_major_locator(MultipleLocator(0.5))
        ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax.zaxis.set_major_locator(MultipleLocator(0.5))
        ax.zaxis.set_minor_locator(MultipleLocator(0.1))
        ax.tick_params(axis='both', which='major', size=10, labelsize=20)
        ax.tick_params(axis='both', which='minor', size=5)
    else:
        pad = 10
        # Set axes labels
        ax.legend(loc='upper right', fontsize='x-large')
        ax.set_xlabel('Time / fs', size=label_size, labelpad=pad)
        if elem_types == 'both':
            ax.set_ylabel('Amplitude', size=label_size, labelpad=pad)
        elif elem_types == 'diagonals':
            ax.set_ylabel('Site Population', size=label_size, labelpad=pad)
        elif elem_types == 'off-diagonals':
            ax.set_ylabel('Coherences', size=label_size, labelpad=pad)
        else:
            ax.set_ylabel('Trace Measure', size=label_size, labelpad=pad)
        ax.set_xlim(times[0], ceil((times[-1] - 1e-9) / 100) * 100)
        # Format axes ranges
        upper_bound = list(ax.get_xticks())[5]
        ax.xaxis.set_minor_locator(MultipleLocator(upper_bound / 20))
        if elem_types == 'both':
            ax.set_ylim(top=1., bottom=-0.5)
        elif elem_types == 'diagonals' or elem_types is None:
            ax.set_ylim(top=1., bottom=0.)
        else:
            ax.set_ylim(top=0.5, bottom=-0.5)
        # Format axes ticks
        ax.yaxis.set_major_locator(MultipleLocator(0.5))
        ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax.tick_params(axis='both', which='major', size=10, labelsize=20)
        ax.tick_params(axis='both', which='minor', size=5)
    return ax

def save_figure_and_args(systems, plot_args: dict, plot_type: str):

    """
    Saves the figure to a descriptive filename in the relative
    path quantum_HEOM/doc/figures/ as a .pdf file, and saves a
    .txt file of the same name in the same directory that contains
    all of the arguments used to define the system as plot the
    dynamics.

    Parameters
    ----------
    systems : list of QuantumSystem
        The QuantumSystem objects whose dynamics have been plotted.
    plot_args : dict
        The arguments passed to the plot_dynamics() method,
        used to plot the dynamics of the systems.
    plot_type : str
        The type of plot in in the figure; either 'dynamics' or
        'spectral_density'.
    """

    # Define some abbreviations of terms to use in file naming
    abbrevs = {'nearest neighbour linear': '_near_neigh_lin',
               'nearest neighbour cyclic': '_near_neigh_cyc',
               'FMO': '_FMO',
               'local thermalising lindblad': '_local_therm',
               'global thermalising lindblad': '_global_therm',
               'local dephasing lindblad': '_local_deph',
               'HEOM': '_HEOM',
               'ohmic': '_ohmic',
               'debye': '_debye',
              }
    # date_stamp = util.date_stamp()  # avoid duplicates in filenames
    fig_dir = (os.getcwd()[:os.getcwd().find('quantum_HEOM')]
               + 'quantum_HEOM/doc/figures/')
    fig_dir += plot_type + '_'
    if len(systems) == 1:
        filename = (fig_dir + str(systems[0].sites) + '_sites'
                    + abbrevs[systems[0].interaction_model]
                    + abbrevs[systems[0].dynamics_model])
    else:
        # Ascertain which variables are being compared between systems.
        interactions = [sys.interaction_model for sys in systems]
        interactions = interactions.count(interactions[0]) == len(interactions)
        dynamics = [sys.dynamics_model for sys in systems]
        dynamics = dynamics.count(dynamics[0]) == len(dynamics)
        temp = [sys.temperature for sys in systems]
        temp = temp.count(temp[0]) == len(temp)
        spec = [sys.spectral_density for sys in systems]
        spec = spec.count(spec[0]) == len(spec)
        # Include the constant arguments in the filename and highlight variables
        filename = fig_dir + str(systems[0].sites) + '_sites'
        if interactions:
            filename += abbrevs[systems[0].interaction_model]
        else:
            filename += '_variable_interactions'
        if dynamics:
            filename += abbrevs[systems[0].dynamics_model]
        else:
            filename += '_variable_dynamics'
        if temp:
            filename += '_' + str(int(systems[0].temperature)) + 'K'
        else:
            filename += '_variable_temp'
        if spec:
            filename += 'variable_spec_dens'
        else:
            for sys in systems:
                try:
                    filename += '_' + sys.spectral_density
                except TypeError:
                    continue
                break
        filename += '_elements'
        if 'dynamics' in filename:
            for elem in plot_args['elements']:
                filename += '_' + elem
        elif 'spectral_density' in filename:
            if plot_args['debye'] is not None:
                filename += '-' + 'debye'
            if plot_args['ohmic'] is not None:
                filename += '-' + 'ohmic'
    # Create a file index number to avoid overwriting existing files
    filename += '_version_'
    index = 0
    while os.path.exists(filename + str(index) + '.pdf'):
        index += 1
    filename += str(index)
    # Save the figure and write the argument info to file.
    plt.savefig(filename + '.pdf', bbox_inches='tight')
    util.write_args_to_file(systems, plot_args, filename + '.txt')

def plot_spectral_density(systems: list = None, models: list = None,
                          debye: dict = None, ohmic: dict = None,
                          save: bool = False):

    """
    Plots either the Debye or Ohmic - or both - spectral densities
    as a function of frequency. Units of all the frequencies and
    the cutoff frequency must be consistent; in rad ps^-1.

    Parameters
    ----------
    systems : list of QuantumSystem
        A list of systems whose spectral densities are to be
        plotted. Optional; can just pass dictionaries containing
        arguments for spectral densities manually.
    models : list of str
        Must specify if systems is passed as None. The spectral
        density(s) model to plot. Must be a list containing either
        or both of 'debye', 'ohmic'.
    debye : dict
        Must specify if systems is passed as None. A dictionary
        containing the arguments used to define the Debye spectral
        density. Must contain values under the keys 'frequencies',
        'cutoff_freq' and 'reorg_energy'. Check the docstring in
        bath.py 's debye_spectral_density() function for details
        on these arguments. If models contains both 'debye' and
        'ohmic' and ohmic is passed as None, the arguments given in
        debye will be used to plot the ohmic spctral density too.
    ohmic : dict
        Must specify if systems is passed as None. A dictionary
        containing the arguments used to define the Ohmic spectral
        density. Must contain values under the keys 'frequencies',
        'cutoff_freq', 'reorg_energy', and 'exponent'. Check the
        docstring in bath.py 's ohmic_spectral_density() function
        for details on these arguments.
    save : bool
        Whether or not to save the figure. Saves to the relative
        directory quantum_HEOM/doc/figures/. Default is False.
    """

    # PLOTTING
    # Set up axes
    gold_ratio, scaling = 1.61803, 5
    figsize = (gold_ratio * scaling, scaling)
    _, axes = plt.subplots(figsize=figsize)
    # Plot systems if list of QuantumSystems is passed.
    if systems is not None:
        if not isinstance(systems, list):
            systems = [systems]
        for sys in systems:
            if sys.dynamics_model == 'local dephasing lindblad':
                raise ValueError(
                    'No spectral density used for local dephasing model.')
            cutoff = sys.cutoff_freq
            frequencies = np.arange(0., cutoff * 10., cutoff / 100.)
            specs = []
            for freq in frequencies:
                if sys.spectral_density == 'debye':
                    label = 'Debye'
                    specs.append(bath.debye_spectral_density(freq, cutoff,
                                                             sys.reorg_energy))
                else:  # Ohmic
                    label = 'Ohmic'
                    specs.append(bath.ohmic_spectral_density(freq,
                                                             cutoff,
                                                             sys.reorg_energy,
                                                             sys.ohmic_exponent
                                                             ))
            specs = np.array(specs)
            axes.plot(frequencies, specs, label=label)
    # Plot if just specifications are passed.
    else:
        if isinstance(models, str):
            models = [models]
        assert all(i in SPECTRAL_DENSITIES for i in models)
        assert debye is not None or ohmic is not None, (
            'Must pass arguments for either debye or ohmic spectral densities.')
        if models == ['debye']:
            assert debye is not None, (
                'Must pass arguments for Debye spectral density to plot it.')
        if models == ['ohmic']:
            assert ohmic is not None, (
                'Must pass arguments for Ohmic spectral density to plot it.')
        if len(models) == 2 and debye is None:
            debye = ohmic
        if len(models) == 2 and ohmic is None:
            ohmic = debye
        deb, ohm = [], []
        if 'debye' in models:
            frequencies = np.array(debye['frequencies'])
            for freq in frequencies:
                deb.append(bath.debye_spectral_density(freq,
                                                       debye['cutoff_freq'],
                                                       debye['reorg_energy']))
        if 'ohmic' in models:
            frequencies = ohmic['frequencies']
            for freq in frequencies:
                ohm.append(bath.ohmic_spectral_density(freq,
                                                       ohmic['cutoff_freq'],
                                                       ohmic['reorg_energy'],
                                                       ohmic['exponent']))
        frequencies *= 1e-12
        if 'debye' in models:
            deb = np.array(deb) * 1e-12
            axes.plot(frequencies * 1e-12, deb, label='Debye')
        if 'ohmic' in models:
            ohm = np.array(ohm) * 1e-12
            axes.plot(frequencies * 1e-12, ohm, label='Ohmic')

    # FORMATTING
    # Format labels
    axes.set_xlabel('$\\omega$ / $rad\\ ps^{-1}$', size=20)
    axes.set_ylabel('J($\\omega$) / $rad\\ ps^{-1}$', size=20)
    # Format x-axis
    axes.set_xlim(frequencies[0], frequencies[-1])
    upper_x_bound = list(axes.get_xticks())[5]
    axes.xaxis.set_minor_locator(MultipleLocator(upper_x_bound / 20))
    # Format y-axis
    axes.set_ylim(bottom=0.)
    upper_y_bound = list(axes.get_yticks())[5]
    axes.yaxis.set_minor_locator(MultipleLocator(upper_y_bound / 20))
    # Format tick size
    axes.tick_params(axis='both', which='major', size=10, labelsize=17)
    axes.tick_params(axis='both', which='minor', size=5)
    # Other formatting
    axes.legend(fontsize='x-large')
    # Save figure as .pdf in quantum_HEOM/doc/figures directory
    if save:
        plot_args = {'models': models,
                     'debye': debye,
                     'ohmic': ohmic,
                     'save': save,
                    }
        save_figure_and_args(systems, plot_args, plot_type='spectral_density')
    plt.show()

# UNUSED TITLE SETTINGS
# title_size = '20'
# title = ('Time evolution of a ' + qsys.interaction_model + ' '
#          + str(qsys.sites) + '-site system modelled with '
#          + qsys.dynamics_model + ' dynamics. \n(')
# if qsys.dynamics_model in TEMP_INDEP_MODELS:
#     title += ('$\\Gamma_{deph}$ = ' + str(qsys.decay_rate * 1E-12)
#               + ' $ps^{-1})$')
# elif qsys.dynamics_model in TEMP_DEP_MODELS:
#     title += ('T = ' + str(qsys.temperature) + ' K, ')
#     title += ('$\\omega_c$ = ' + str(qsys.cutoff_freq * 1e-12)
#               + ' $rad\\ ps^{-1}$, $f$ = ' + str(qsys.reorg_energy * 1e-12)
#               + ' $rad\\ ps^{-1})$')
# if set_title:
#     ax.set_title(title, size=title_size, pad=20)
