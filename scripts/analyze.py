import numpy as np
from functools import reduce
from .utilities import *

# ANALYSIS UTILITY FUNCTIONS ===================================================


def convert_coordinates(c):
    """Convert coordinates to rectangular."""
    if len(c) == 4:
        R = 34
        offx = R - 1
        offy = 2*R - 2
        u, v, w, z = c
        x = u + R - 1 - offx
        y = (w - v) + 2*R - 2 - offy
        return [x, y, z]
    else:
        return list(c)

def calculate_statistics(data):
    """Calculate statistics for data."""
    return {
        "mean": np.mean(data, axis=0).tolist(),
        "max": np.max(data, axis=0).tolist(),
        "min": np.min(data, axis=0).tolist(),
        "std": np.std(data, axis=0, ddof=1).tolist()
    }

def calculate_nan_statistics(data):
    """Calculate statistic for data excluding nans."""
    D = np.swapaxes(data, 0, 1)
    unnan = [[e for e in d if not np.isnan(e)] for d in D]
    return {
        "mean": [np.mean(d) if d else np.nan for d in unnan],
        "max": [np.max(d) if d else np.nan for d in unnan],
        "min": [np.min(d) if d else np.nan for d in unnan],
        "std": [np.std(d, ddof=1) if d else np.nan for d in unnan]
    }

def add_coordinates(D, t):
    """Adds column to dataframe with coordinates as tuple."""
    d = D[D.t == t].copy()
    coords = d[d.columns.intersection(["u", "v", "w", "x", "y", "z"])].to_records(index=False)
    coords = [tuple(c) for c in coords]
    d["c"] = coords
    return d

# GENERAL METRICS ==============================================================

def get_count(D, t, i):
    """Get number of cells."""
    return len(D[(D.t == t) & (D.i == i)])

def get_volume(D, t, i):
    """Get total volume of cells."""
    volumes = D[(D.t == t) & (D.i == i)]["volume"]
    return int(volumes.sum())

def get_diameter(D, t, i):
    """Get diameter of colony."""
    diameters = []
    slice = D[(D.t == t) & (D.i == i)]

    for _, group in slice.groupby("z"):
        delta =  group.max() - group.min()
        delta = delta[delta.index.intersection(["u", "v", "w", "x", "y"])]
        diameters.append(np.mean([np.max(d + 1, 0) for d in delta]))

    return np.max(diameters) if diameters else 0

def get_cycle(D, t, i):
    """Get average cell cycle length."""
    cycles = D[(D.t == t) & (D.i == i)]["cycle"]
    cycles = list(filter(lambda x : x != -1, cycles))
    return np.mean(cycles) if len(cycles) > 0 else np.nan

def get_state(D, t, i, state):
    """Get cell state."""
    states = D[(D.t == t) & (D.i == i) & (D.state == state)]
    return len(states)

def get_symmetry(D, t, i):
    """Get symmetry of colony."""
    symmetries = []
    slice = D[(D.t == t) & (D.i == i)]

    for _, group in slice.groupby("z"):
        coords = group[group.columns.intersection(["u", "v", "w", "x", "y"])]
        coords_list = [tuple(c) for c in coords.to_records(index=False)]
        coords_set = set(coords_list)

        # Find unique coordinate sets.
        unique_coords = set()
        for coord in coords_set:
            sym_coords = get_symmetric(coord)
            if len(unique_coords - sym_coords) < len(unique_coords):
                continue
            unique_coords.add(coord)

        # Calculate symmetry.
        deltas = []

        for unique in unique_coords:
            sym_coords = get_symmetric(unique) # set of symmetric coordinates
            delta_set = sym_coords - set(coords_set) # symmetric coordinates not in full set

            if len(sym_coords) == 1:
                deltas.append(len(delta_set))
            else:
                deltas.append(len(delta_set)/(len(sym_coords) - 1))

        numer = np.sum(deltas)
        denom = len(unique_coords)
        symmetries.append(1 - numer/denom)

    return np.mean(symmetries) if symmetries else np.nan

def get_symmetric(coord):
    """Get list of symmetric coordinates."""
    if len(coord) == 3:
        u, v, w = coord
        return {(u, v, w), (-w, -u, -v), (v, w, u), (-u, -v, -w), (w, u, v), (-v, -w, -u)}
    elif len(coord) == 2:
        x, y = coord
        return {(x, y), (-y, x), (-x, -y), (y, -x), (x, -y), (y, x), (-x, y), (-y, -x)}

# TEMPORAL METRICS =============================================================

def get_temporal_counts(D, T, N):
    """Get cell counts over time."""
    return [[get_count(D, t, i) for t in T] for i in N]

def get_temporal_volumes(D, T, N):
    """Get cell volumes over time."""
    return [[get_volume(D, t, i) for t in T] for i in N]

def get_temporal_diameters(D, T, N):
    """Get colony diameter over time."""
    return [[get_diameter(D, t, i) for t in T] for i in N]

def get_temporal_cycles(D, T, N):
    """Get cell cycles over time."""
    return [[get_cycle(D, t, i) for t in T] for i in N]

def get_temporal_states(D, T, N):
    """Get cell states over time."""
    states = [i for i in range(0,7)]
    return [[[get_state(D, t, i, state) for t in T] for i in N] for state in states]

def get_temporal_growths(D, T, N):
    """Get growth metric over time."""
    diameters = get_temporal_diameters(D, T, N)
    return [[np.polyfit(T[:t], diameters[i][:t], 1)[0] for t in range(2, len(T))] for i in N]

def get_temporal_symmetries(D, T, N):
    """Get symmetry metric over time."""
    return [[get_symmetry(D, t, i) for t in T] for i in N]

def get_temporal_activity(D, T, N):
    """Get activity metric over time."""
    states = get_temporal_states(D, T, N)

    active_states = [state for i, state in enumerate(states) if i in [3, 4]]
    inactive_states = [state for i, state in enumerate(states) if i in [1, 6]]

    active = np.sum(np.array(active_states), axis=0)
    inactive = np.sum(np.array(inactive_states), axis=0)

    total = np.add(active, inactive)
    total[total == 0] = -1 # set total to -1 to avoid divide by zero error
    activity = np.subtract(np.multiply(np.divide(active, total), 2), 1)
    activity[total == -1] = np.nan # set activity to nan for the case of no active or inactive cells

    return activity

# SPATIAL METRICS ==============================================================

def get_spatial_counts(D):
    """Get cell counts by coordinate."""
    counts = D.groupby("c")["i"].count()
    return counts

def get_spatial_volumes(D):
    """Get cell volumes by coordinate."""
    volumes = D.groupby("c")["volume"].sum()
    return volumes

def get_spatial_states(D):
    """Get cell states by coordinate."""
    state_columns = [f"STATE_{state}" for state in range(7)]

    # Create dummy columns for each state.
    d = pd.get_dummies(D.state, prefix='STATE')
    D = pd.concat([D, d], axis=1)

    # Add missing columns.
    for col in state_columns:
        if col not in D.columns:
            D[col] = 0

    states = D.groupby("c").sum()
    return states[state_columns]

# GENERAL ANALYSIS =============================================================

def analyze_metrics(D, T, N, outfile, code, timepoints=[], seeds=[]):
    """Analyze results for metrics across time."""

    counts = get_temporal_counts(D, T, N)
    _analyze_metrics(counts, T, f"{outfile}{code}", ".METRICS.COUNTS")

    volumes = get_temporal_volumes(D, T, N)
    _analyze_metrics(volumes, T, f"{outfile}{code}", ".METRICS.VOLUMES")

    diameters = get_temporal_diameters(D, T, N)
    _analyze_metrics(diameters, T, f"{outfile}{code}", ".METRICS.DIAMETERS")

    states = get_temporal_states(D, T, N)
    _analyze_metrics_list(states, T, f"{outfile}{code}", ".METRICS.STATES")

    cycles = get_temporal_cycles(D, T, N)
    _analyze_metrics_nan(cycles, T, f"{outfile}{code}", ".METRICS.CYCLES")

    index = T.index(2.0)
    growth = get_temporal_growths(D, T[index:], N)
    nan_growth = [np.nan] * (index + 2)
    _analyze_metrics_nan([nan_growth + grow for grow in growth], T, f"{outfile}{code}", ".METRICS.GROWTH")

    symmetry = get_temporal_symmetries(D, T, N)
    _analyze_metrics_nan(symmetry, T, f"{outfile}{code}", ".METRICS.SYMMETRY")

    activity = get_temporal_activity(D, T, N)
    _analyze_metrics_nan(activity, T, f"{outfile}{code}", ".METRICS.ACTIVITY")

def analyze_seeds(D, T, N, outfile, code, timepoints=[], seeds=[]):
    """Analyze results for metrics grouped by seed."""

    counts = get_temporal_counts(D, timepoints, N)
    _analyze_seeds(counts, timepoints, f"{outfile}{code}", ".SEEDS.COUNTS")

    volumes = get_temporal_volumes(D, timepoints, N)
    _analyze_seeds(volumes, timepoints, f"{outfile}{code}", ".SEEDS.VOLUMES")

    diameters = get_temporal_diameters(D, timepoints, N)
    _analyze_seeds(diameters, timepoints, f"{outfile}{code}", ".SEEDS.DIAMETERS")

    states = get_temporal_states(D, timepoints, N)
    _analyze_seeds_list(states, timepoints, f"{outfile}{code}", ".SEEDS.STATES")

    cycles = get_temporal_cycles(D, timepoints, N)
    _analyze_seeds(cycles, timepoints, f"{outfile}{code}", ".SEEDS.CYCLES")

    index = T.index(2.0)
    growth = get_temporal_growths(D, T[index:], N)
    growth = [[np.nan] * (index + 2) + grow for grow in growth]
    indices = [T.index(t) for t in timepoints]
    growth = np.array(growth)[:,indices]
    _analyze_seeds(growth, timepoints, outfile + code, ".SEEDS.GROWTH")

    symmetry = get_temporal_symmetries(D, timepoints, N)
    _analyze_seeds(symmetry, timepoints, f"{outfile}{code}", ".SEEDS.SYMMETRY")

    activity = get_temporal_activity(D, timepoints, N)
    _analyze_seeds(activity, timepoints, f"{outfile}{code}", ".SEEDS.ACTIVITY")

def analyze_locations(D, T, N, outfile, code, timepoints=[], seeds=[]):
    """Analyze results for metrics per location."""

    for t in timepoints:
        d = add_coordinates(D, t)
        counts = get_spatial_counts(d)
        volumes = get_spatial_volumes(d)
        states = get_spatial_states(d)

        merged = reduce(lambda left, right: pd.merge(left, right, on='c'), [counts, volumes, states])
        merged = merged/len(N)

        out = [list(r) for r in merged.to_records()]
        out = [convert_coordinates(row[0]) + row[1:] for row in out]

        header = "x,y,z,COUNT,VOLUME," + ",".join([f"STATE_{state}" for state in range(7)]) + "\n"
        save_csv(f"{outfile}{code}", header, list(zip(*out)), f".LOCATIONS.{format_time(t)}")

# ------------------------------------------------------------------------------

def _analyze_metrics(data, T, filename, extension):
    """Save analysis from metrics analysis."""
    out = calculate_statistics(data)
    out['_X'] = T
    save_json(filename, out, extension)

def _analyze_metrics_list(data, T, filename, extension):
    """Save analysis from metrics analysis for lists."""
    out = [calculate_statistics(d) for d in data]
    _out = { "data": out, "_X": T }
    save_json(filename, _out, extension)

def _analyze_metrics_nan(data, T, filename, extension):
    """Save analysis from metrics analysis excluding nans."""
    out = calculate_nan_statistics(data)
    out['_X'] = T
    save_json(filename, out, extension)

def _analyze_seeds(data, T, filename, extension):
    """Save analysis from seeds analysis."""
    out = [{ "_": [x[i] for x in data], "time": t } for i, t in enumerate(T)]
    save_json(filename, out, extension)

def _analyze_seeds_list(data, T, filename, extension):
    """Save analysis from seeds analysis for lists."""
    out = [[{ "_": [x[i] for x in d], "time": t } for i, t in enumerate(T)] for d in data]
    save_json(filename, out, extension)
