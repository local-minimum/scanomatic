from scipy.ndimage import label
from scipy.stats import linregress
from scipy import signal
import numpy as np
from matplotlib import pyplot as plt
from scanomatic.data_processing import growth_phenotypes
from enum import Enum
import warnings
from functools import partial


class CurvePhases(Enum):

    Multiple = -1
    """:type : CurvePhases"""
    Undetermined = 0
    """:type : CurvePhases"""
    Flat = 1
    """:type : CurvePhases"""
    Acceleration = 2
    """:type : CurvePhases"""
    Retardation = 3
    """:type : CurvePhases"""
    Impulse = 4
    """:type : CurvePhases"""


class Thresholds(Enum):

    ImpulseExtension = 0
    """:type : Thresholds"""
    ImpulseSlopeRequirement = 1
    """:type : Thresholds"""
    FlatlineSlopRequirement = 2
    """:type : Thresholds"""


class CurvePhasePhenotypes(Enum):

    # Curvature = 0
    PopulationDoublingTime = 1
    Duration = 2
    FractionYield = 3
    Start = 4
    LinearModelSlope = 5
    LinearModelIntercept = 6
    AsymptoteAngle = 7
    AsymptoteIntersection = 8


class VectorPhenotypes(Enum):

    PhasesClassifications = 0
    PhasesPhenotypes = 1

PHASE_PLOTTING_COLORS = {
    CurvePhases.Multiple: "#5f3275",
    CurvePhases.Flat: "#f9e812",
    CurvePhases.Acceleration: "#ea5207",
    CurvePhases.Impulse: "#99220c",
    CurvePhases.Retardation: "#c797c1"}


def plot_segments(
        times, curve, phases, segment_alpha=0.3, f=None,
        colors=None):

    if colors is None:
        colors = PHASE_PLOTTING_COLORS

    if f is None:
        f = plt.figure()

    ax = f.gca()

    # noinspection PyTypeChecker
    for phase in CurvePhases:

        if phase == CurvePhases.Undetermined:
            continue

        labels, label_count = label(phases == phase.value)
        for id_label in range(1, label_count + 1):
            positions = np.where(labels == id_label)[0]
            left = positions[0]
            right = positions[-1]
            left = np.linspace(times[max(left - 1, 0)], times[left], 3)[1]
            right = np.linspace(times[min(curve.size - 1, right + 1)], times[right], 3)[1]
            ax.axvspan(left, right, color=colors[phase], alpha=segment_alpha)

    curve_color = CurvePhases(np.unique(phases)[0]) if np.unique(phases).size == 1 else CurvePhases.Multiple
    ax.semilogy(times, curve, basey=2, color=colors[curve_color], lw=2)
    ax.set_xlim(xmin=times[0], xmax=times[-1])
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Population Size [cells]")

    return f


def _filter_find(vector, filt, func=np.max):

    return np.where((vector == func(vector[filt])) & filt)[0]

DEFAULT_THRESHOLDS = {
    Thresholds.ImpulseExtension: 0.75,
    Thresholds.ImpulseSlopeRequirement: 0.1,
    Thresholds.FlatlineSlopRequirement: 0.02}


def _segment(dydt, dydt_ranks, ddydt_signs, phases, filt, offset,
             thresholds=None):

    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    if np.unique(phases[offset: -offset][filt]).size != 1:
        raise ValueError("Impossible to segment due to multiple phases {0} filter {1}".format(
            np.unique(phases[filt][offset: -offset]), filt
        ))

    # 1. Find segment's borders
    left, right = _locate_segment(filt)

    # 2. Find segment's maximum growth
    loc_max = _filter_find(dydt_ranks, filt)

    no_impulse = filt.all()

    # 3. Further sementation requires existance of reliable growth impulse
    if dydt[loc_max] < thresholds[Thresholds.ImpulseSlopeRequirement]:
        if no_impulse:
            warnings.warn("No impulse detected, max rate is {0} (threshold {1}).".format(
                dydt[loc_max], thresholds[Thresholds.ImpulseSlopeRequirement]))
        if left == 0:
            phases[:offset] = phases[offset]

        if right == phases.size:
            phases[-offset:] = phases[-offset - 1]
        return

    # 4. Locate impulse
    impulse_left, impulse_right = _locate_impulse(dydt, loc_max, phases, filt, offset,
                                                  thresholds[Thresholds.ImpulseExtension])

    if impulse_left is None or impulse_right is None:
        if no_impulse:
            warnings.warn("No impulse phase detected though max rate super-seeded threshold")
        if left == 0:
            phases[:offset] = phases[offset]
        if right == phases.size:
            phases[-offset:] = phases[-offset - 1]

        return

    # 5. Locate acceleration phase
    (accel_left, _), next_phase = _locate_acceleration(
        dydt, ddydt_signs, phases, left, impulse_left, offset,
        flatline_threshold=thresholds[Thresholds.FlatlineSlopRequirement])

    # 5b. If there's anything remaining, it is candidate flatline, but investigated for more impulses
    if left != accel_left:
        phases[left + offset: accel_left + 1 + offset] = next_phase.value
        _segment(dydt, dydt_ranks, ddydt_signs, phases, _get_filter(left, accel_left, size=dydt.size, filt=filt),
                 offset, thresholds)

    # 6. Locate retardation phase
    (_, retard_right), next_phase = _locate_retardation(
        dydt, ddydt_signs, phases, impulse_right, right, offset,
        flatline_threshold=thresholds[Thresholds.FlatlineSlopRequirement])

    # 6b. If there's anything remaining, it is candidate flatline, but investigated for more impulses
    if right != retard_right:
        phases[retard_right + offset: right + offset] = next_phase.value
        _segment(dydt, dydt_ranks, ddydt_signs, phases, _get_filter(retard_right, right, size=dydt.size, filt=filt),
                 offset, thresholds)

    # 7. Update phases edges
    phases[:offset] = phases[offset]
    phases[-offset:] = phases[-offset - 1]


def _locate_impulse(dydt, loc, phases, filt, offset, extension_threshold):

    candidates = (dydt > dydt[loc] * extension_threshold) & filt
    candidates = signal.medfilt(candidates, 3).astype(bool)

    candidates, _ = label(candidates)
    phases[offset: -offset][candidates == candidates[loc]] = CurvePhases.Impulse.value
    return _locate_segment(candidates)


def _locate_segment(filt):  # -> (int, int)
    """

    Args:
        filt: a boolean array

    Returns:
        Left and exclusive right indices of filter
    """
    labels, n = label(filt)
    if n == 1:
        where = np.where(labels == 1)[0]
        return where[0], where[-1] + 1
    elif n > 1:
        warnings.warn("Filter is not homogenous, contains {0} segments".format(n))
        return None, None
    else:
        return None, None


def _get_filter(left=None, right=None, filt=None, size=None):
    """

    Args:
        left: inclusive left index or None (sets index as 0)
        right: exclusive right index or None (sets at size of filt)
        filt: previous filter array to reuse
        size: if no previous filter is supplied, size determines filter creation

    Returns: Filter array
        :rtype: numpy.ndarray
    """
    if filt is None:
        filt = np.zeros(size).astype(bool)
    else:
        filt[:] = False
        size = filt.size

    if left is None:
        left = 0
    if right is None:
        right = size

    filt[left: right] = True
    return filt


def _locate_acceleration(dydt, ddydt_signs, phases, left, right, offset, flatline_threshold, filt=None):

    candidates = _get_filter(left, right, size=dydt.size, filt=filt)
    candidates2 = candidates & (np.abs(dydt) > flatline_threshold) & (ddydt_signs == 1)

    candidates2 = signal.medfilt(candidates2, 3).astype(bool)
    candidates2, label_count = label(candidates2)

    if label_count:
        acc_candidates = candidates2 == label_count
        phases[offset: -offset][acc_candidates] = CurvePhases.Acceleration.value
        return _locate_segment(acc_candidates), CurvePhases.Flat
    else:
        phases[offset: -offset][candidates] = CurvePhases.Undetermined.value
        return (left, right), CurvePhases.Undetermined


def _locate_retardation(dydt, ddydt_signs, phases, left, right, offset, flatline_threshold, filt=None):

    candidates = _get_filter(left, right, size=dydt.size, filt=filt)
    candidates2 = candidates & (np.abs(dydt) > flatline_threshold) & (ddydt_signs == -1)

    candidates2 = signal.medfilt(candidates2, 3).astype(bool)
    candidates2, label_count = label(candidates2)

    if label_count:
        ret_cantidates = candidates2 == 1
        phases[offset: -offset][ret_cantidates] = CurvePhases.Retardation.value
        return _locate_segment(ret_cantidates), CurvePhases.Flat
    else:
        phases[offset: -offset][candidates] = CurvePhases.Undetermined.value
        return (left, right), CurvePhases.Undetermined


def _phenotype_phases(curve, derivative, phases, times, doublings):

    derivative_offset = (times.shape[0] - derivative.shape[0]) / 2
    phenotypes = []

    # noinspection PyTypeChecker
    for phase in CurvePhases:

        labels, label_count = label(phases == phase.value)
        for id_label in range(1, label_count + 1):

            if phase == CurvePhases.Undetermined or phase == CurvePhases.Multiple:
                phenotypes.append((phase, None))
                continue

            filt = labels == id_label
            left, right = _locate_segment(filt)
            time_right = times[right - 1]
            time_left = times[left]
            current_phase_phenotypes = {}

            if phase == CurvePhases.Acceleration or phase == CurvePhases.Retardation:
                # A. For non-linear phases use the X^2 coefficient as curvature measure

                a1 = np.array((time_left, np.log2(curve[left])))
                a2 = np.array((time_right, np.log2(curve[right - 1])))
                k1 = derivative[left - derivative_offset]
                k2 = derivative[right - 1 - derivative_offset]
                m1 = a1[1] - k1 * a1[0]
                m2 = a2[1] - k2 * a2[1]
                i_x = (m2 - m1) / (k1 - k2)
                i = np.array((i_x, k1 * i_x + m1))
                a1 -= i
                a2 -= i
                current_phase_phenotypes[CurvePhasePhenotypes.AsymptoteIntersection] = \
                    (i_x - time_left) / (time_right - time_left)
                current_phase_phenotypes[CurvePhasePhenotypes.AsymptoteAngle] = \
                    np.arctan((k2 - k1) / (1 + k1 * k2))

            else:
                # B. For linear phases get the doubling time
                slope, intercept, _, _, _ = linregress(times[filt], np.log2(curve[filt]))
                current_phase_phenotypes[CurvePhasePhenotypes.PopulationDoublingTime] = 1 / slope
                current_phase_phenotypes[CurvePhasePhenotypes.LinearModelSlope] = slope
                current_phase_phenotypes[CurvePhasePhenotypes.LinearModelIntercept] = intercept

            # C. Get duration
            current_phase_phenotypes[CurvePhasePhenotypes.Duration] = time_right - time_left

            # D. Get fraction of doublings
            current_phase_phenotypes[CurvePhasePhenotypes.FractionYield] = \
                (np.log2(curve[right - 1]) - np.log2(curve[left])) / doublings

            # E. Get start of phase
            current_phase_phenotypes[CurvePhasePhenotypes.Start] = time_left

            phenotypes.append((phase, current_phase_phenotypes))

    # Phenotypes sorted on phase start rather than type of phase
    return sorted(phenotypes, key=lambda (t, p): p[CurvePhasePhenotypes.Start] if p is not None else 9999)


def phase_phenotypes(
        phenotyper_object, plate, pos, segment_alpha=0.75, f=None,
        thresholds=None,
        experiment_doublings=None):

    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    curve = phenotyper_object.smooth_growth_data[plate][pos]
    dydt = phenotyper_object.get_derivative(plate, pos)
    offset = (phenotyper_object.times.shape[0] - dydt.shape[0]) / 2
    dydt_ranks = dydt.argsort().argsort()
    ddydt = signal.convolve(dydt, [1, 0, -1], mode='valid')
    ddydt_signs = np.hstack(([0], np.sign(ddydt), [0]))
    phases = np.ones_like(curve).astype(np.int) * 0
    filt = _get_filter(size=dydt.size)

    _segment(dydt, dydt_ranks, ddydt_signs, phases, filt=filt, offset=offset, thresholds=thresholds)

    if experiment_doublings is None:
        experiment_doublings = (np.log2(phenotyper_object.get_phenotype(
            growth_phenotypes.Phenotypes.ExperimentEndAverage)[plate][pos]) -
                                np.log2(phenotyper_object.get_phenotype(
                                    growth_phenotypes.Phenotypes.ExperimentBaseLine)[plate][pos]))

    return phases,\
        _phenotype_phases(curve, dydt, phases, phenotyper_object.times, experiment_doublings),\
        None if f is False else plot_segments(phenotyper_object.times, curve, phases, segment_alpha=segment_alpha, f=f)


def phase_selector_critera_filter(phases, criteria, func=max):

    val = func(phase[criteria] for phase in phases)
    return tuple(phase for phase in phases if phase[criteria] == val)[0]


def filter_plate_custom_filter(
        plate,
        phase=CurvePhases.Acceleration,
        measure=CurvePhasePhenotypes.AsymptoteIntersection,
        phases_requirement=lambda phases: len(phases) == 1,
        phase_selector=lambda phases: phases[0]):

    def f(v):
        phases = tuple(d for t, d in v if t == phase)
        if phases_requirement(phases):
            return phase_selector(phases)[measure]
        return np.nan

    return np.ma.masked_invalid(np.frompyfunc(f, 1, 1)(plate).astype(np.float))


def _impulse_counter(phase_vector):
    return sum(1 for phase in phase_vector if phase[0] == CurvePhases.Impulse)


class CurvePhaseMetaPhenotypes(Enum):

    MajorImpulseYieldContribution = 0
    FirstMinorImpulseYieldContribution = 1
    MajorImpulseAveragePopulationDoublingTime = 5
    FirstMinorImpulseAveragePopulationDoublingTime = 6

    InitialAccelerationAsymptoteAngle = 10
    FinalRetardationAsymptoteAngle = 11
    InitialAccelerationAsymptoteIntersect = 15
    FinalRetardationAsymptoteIntersect = 16

    InitialLag = 20
    ExperimentDoublings = 21
    Modalities = 25

    ResidualGrowth = 30


def filter_plate(plate, meta_phenotype):

    if meta_phenotype == CurvePhaseMetaPhenotypes.MajorImpulseYieldContribution:

        selector = partial(phase_selector_critera_filter, criteria=CurvePhasePhenotypes.FractionYield)
        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Impulse,
            measure=CurvePhasePhenotypes.FractionYield,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=selector)

    elif meta_phenotype == CurvePhaseMetaPhenotypes.FirstMinorImpulseYieldContribution:

        selector = partial(phase_selector_critera_filter, criteria=CurvePhasePhenotypes.FractionYield,
                           func=lambda x: x[np.argsort(x)[-2]])
        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Impulse,
            measure=CurvePhasePhenotypes.FractionYield,
            phases_requirement=lambda phases: len(phases) > 1,
            phase_selector=selector)

    elif meta_phenotype == CurvePhaseMetaPhenotypes.MajorImpulseAveragePopulationDoublingTime:

        selector = partial(phase_selector_critera_filter, criteria=CurvePhasePhenotypes.FractionYield)
        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Impulse,
            measure=CurvePhasePhenotypes.PopulationDoublingTime,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=selector)

    elif meta_phenotype == CurvePhaseMetaPhenotypes.FirstMinorImpulseAveragePopulationDoublingTime:

        selector = partial(phase_selector_critera_filter, criteria=CurvePhasePhenotypes.FractionYield,
                           func=lambda x: x[np.argsort(x)[-2]])

        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Impulse,
            measure=CurvePhasePhenotypes.PopulationDoublingTime,
            phases_requirement=lambda phases: len(phases) > 1,
            phase_selector=selector)

    elif meta_phenotype == CurvePhaseMetaPhenotypes.InitialLag:

        lag_slope = filter_plate_custom_filter(
            plate, phase=CurvePhases.Flat, measure=CurvePhasePhenotypes.LinearModelSlope,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[0])

        lag_intercept = filter_plate_custom_filter(
            plate, phase=CurvePhases.Flat, measure=CurvePhasePhenotypes.LinearModelIntercept,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[0])

        impulse_slope = filter_plate_custom_filter(
            plate, phase=CurvePhases.Impulse, measure=CurvePhasePhenotypes.LinearModelSlope,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[0])

        impulse_intercept = filter_plate_custom_filter(
            plate, phase=CurvePhases.Impulse, measure=CurvePhasePhenotypes.LinearModelIntercept,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[0])

        return (impulse_intercept - lag_intercept) / (lag_slope - impulse_slope)

    elif meta_phenotype == CurvePhaseMetaPhenotypes.InitialAccelerationAsymptoteAngle:

        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Acceleration,
            measure=CurvePhasePhenotypes.AsymptoteAngle,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[0]
        )

    elif meta_phenotype == CurvePhaseMetaPhenotypes.FinalRetardationAsymptoteAngle:

        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Retardation,
            measure=CurvePhasePhenotypes.AsymptoteAngle,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[-1]
        )

    elif meta_phenotype == CurvePhaseMetaPhenotypes.InitialAccelerationAsymptoteIntersect:

        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Acceleration,
            measure=CurvePhasePhenotypes.AsymptoteIntersection,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[0]
        )

    elif meta_phenotype == CurvePhaseMetaPhenotypes.FinalRetardationAsymptoteIntersect:

        return filter_plate_custom_filter(
            plate,
            phase=CurvePhases.Retardation,
            measure=CurvePhasePhenotypes.AsymptoteIntersection,
            phases_requirement=lambda phases: len(phases) > 0,
            phase_selector=lambda phases: phases[-1]
        )

    elif meta_phenotype == CurvePhaseMetaPhenotypes.Modalities:

        return np.ma.masked_invalid(np.frompyfunc(_impulse_counter, 1, 1))

    else:

        return np.ma.masked_invalid(np.ones_like(plate.shape) * np.nan)
