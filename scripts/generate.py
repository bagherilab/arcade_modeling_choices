from .analyze import *
from .utilities import *

# GENERAL ANALYSIS FUNCTIONS ===================================================

def merge_metrics(file, out, keys, extension, code, tar=None):
    """Merge metrics across conditions."""
    filepath = f"{file}{code}{extension}.json"

    if tar:
        D = load_json(filepath.split("/")[-1], tar=tar)
    else:
        D = load_json(filepath)

    keys["_Y"] = D['mean']
    keys.pop('time', None)
    out['data'].append(keys)
    out['_X'] = D['_X']

    # Check for special case of 3D simulations.
    if "dimension" in keys and keys["dimension"] == "3D":
        layer_tar = load_tar(file, ".LAYERS")
        layer_filepath = filepath.replace("METRICS", "LAYERS")

        if tar:
            D = load_json(layer_filepath.split("/")[-1], tar=layer_tar)
        else:
            D = load_json(layer_filepath)

        layer_keys = dict(keys)
        layer_keys["_Y"] = D['mean']
        layer_keys["dimension"] = "3DC"
        out['data'].append(layer_keys)

# ------------------------------------------------------------------------------

def save_metrics(file, extension, out):
    """Save merged metrics files."""
    save_json(file, out, extension)

# CENTER LAYERS ================================================================

def get_center_layers(D, T, N, outfile, code, timepoints=[], seeds=[]):
    """Analyze results for metrics across time for center layer only"""

    # Filter dataframe for center layer.
    d = D[D.z == 0]

    cycles = get_temporal_cycles(d, T, N)
    save_center_layers(cycles, T, f"{outfile}{code}", ".LAYERS.CYCLES")

    index = T.index(2.0)
    growth = get_temporal_growths(d, T[index:], N)
    nan_growth = [np.nan] * (index + 2)
    save_center_layers([nan_growth + grow for grow in growth], T, f"{outfile}{code}", ".LAYERS.GROWTH")

    symmetry = get_temporal_symmetries(d, T, N)
    save_center_layers(symmetry, T, f"{outfile}{code}", ".LAYERS.SYMMETRY")

def save_center_layers(data, T, filename, extension):
    """Save analysis from metrics analysis excluding nans."""
    out = calculate_nan_statistics(data)
    out['_X'] = T
    save_json(filename, out, extension)

# COLONY BORDERS ===============================================================

def get_colony_borders(D, T, N, outfile, code, timepoints=[], seeds=[]):
    """Extracts colony borders for specified seed and timepoint."""

    d = add_coordinates(D, timepoints)
    d = d[d.i == seeds]

    outlines = get_spatial_outlines(d)
    out = [list(r[-1]) + [r[2]] for r in outlines.to_records(index=False)]

    header = "x,y,z,DIRECTION\n"
    save_csv(f"{outfile}{code}", header, list(zip(*out)), f".BORDERS")
