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
        layer_filepath = filepath.replace("METRICS", "LAYERS.METRICS")

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

def get_center_layers_metrics(D, T, N, outfile, code, timepoints=[], seeds=[]):
    """Analyze results for metrics across time for center layer only"""

    # Filter dataframe for center layer.
    d = D[D.z == 0]

    cycles = get_temporal_cycles(d, T, N)
    save_center_layers_metrics(cycles, T, f"{outfile}{code}", ".LAYERS.METRICS.CYCLES")

    index = T.index(2.0)
    growth = get_temporal_growths(d, T[index:], N)
    nan_growth = [np.nan] * (index + 2)
    save_center_layers_metrics([nan_growth + grow for grow in growth], T, f"{outfile}{code}", ".LAYERS.METRICS.GROWTH")

    symmetry = get_temporal_symmetries(d, T, N)
    save_center_layers_metrics(symmetry, T, f"{outfile}{code}", ".LAYERS.METRICS.SYMMETRY")

def save_center_layers_metrics(data, T, filename, extension):
    """Save analysis from metrics analysis excluding nans."""
    out = calculate_nan_statistics(data)
    out['_X'] = T
    save_json(filename, out, extension)

def get_center_layer_seeds(D, T, N, outfile, code, timepoints=[], seeds=[]):
    """Analyze results for metrics grouped by seed for center layer only."""

    # Filter dataframe for center layer.
    d = D[D.z == 0]

    cycles = get_temporal_cycles(d, timepoints, N)
    save_center_layer_seeds(cycles, timepoints, f"{outfile}{code}", ".LAYERS.SEEDS.CYCLES")

    index = T.index(2.0)
    growth = get_temporal_growths(d, T[index:], N)
    growth = [[np.nan] * (index + 2) + grow for grow in growth]
    indices = [T.index(t) for t in timepoints]
    growth = np.array(growth)[:,indices]
    save_center_layer_seeds(growth, timepoints, outfile + code, ".LAYERS.SEEDS.GROWTH")

    symmetry = get_temporal_symmetries(d, timepoints, N)
    save_center_layer_seeds(symmetry, timepoints, f"{outfile}{code}", ".LAYERS.SEEDS.SYMMETRY")

def save_center_layer_seeds(data, T, filename, extension):
    """Save analysis from seeds analysis."""
    out = [{ "_": [x[i] for x in data], "time": t } for i, t in enumerate(T)]
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

# FEATURE QUANTILES ============================================================

def get_feature_quantiles(tar, timepoints, keys, outfile, code):
    """Gets volume and age features across seeds."""
    features = []

    for member in tar.getmembers():
        json = load_json(member, tar=tar)

        for timepoint in json["timepoints"]:
            if timepoint["time"] in timepoints:
                cells = [cell for tp, cells in timepoint["cells"] for cell in cells]
                cells_excluded = [cell for cell in cells if cell[1] == 0]

                features = features + [[timepoint["time"], cell[4], cell[5]] for cell in cells_excluded]

    header = "time,volume,age\n"
    save_csv(f"{outfile}{code}", header, list(zip(*features)), f".QUANTILES")

def merge_feature_quantiles(file, out, keys, extension, code, tar=None):
    """Merge volume and age features across conditions."""
    code = code.replace("_CHX_", "_CH_")
    filepath = f"{file}{code}{extension}.csv"

    if tar:
        D = load_csv(filepath.split("/")[-1], tar=tar)
    else:
        D = load_csv(filepath)

    rows = [[keys["context"], keys["age"], keys["volume"]] + d for d in D[1:]]
    out['data'] = out["data"] + rows

def save_feature_quantiles(file, extension, out):
    """Calculate quantiles and save merged quantiles file."""
    columns = ["context", "age_code", "volume_code", "time", "volume", "age"]
    df = pd.DataFrame(out["data"], columns=columns)

    out = { "AGE": [], "VOLUME": [] }

    for name, group in df.groupby(["context", "volume_code", "time"]):
        context, volume_code, time = name
        volume = group["volume"].astype("float")

        out["VOLUME"].append({
            "context": context,
            "volume": volume_code,
            "time": float(time),
            "quantiles": [volume.quantile(q) for q in [0, 0.25, 0.5, 0.75, 1.0]],
        })

    for name, group in df.groupby(["context", "age_code", "time"]):
        context, age_code, time = name
        age = group["age"].astype("float")/60./24.

        out["AGE"].append({
            "context": context,
            "age": age_code,
            "time": float(time),
            "quantiles": [age.quantile(q) for q in [0, 0.25, 0.5, 0.75, 1.0]],
        })

    save_json(file, out, extension)

# CONCENTRATION PROFILES =======================================================

def make_concentration_profiles(tar, timepoints, keys, outfile, code):
    """Get average concentration at center of environment."""
    out = {}

    all_glucose = []
    for member in tar.getmembers():
        json = load_json(member, tar=tar)
        glucose = [[tp["time"], tp["molecules"]["glucose"][0][0]] for tp in json["timepoints"]]
        all_glucose = all_glucose + glucose
        break

    df = pd.DataFrame(all_glucose, columns=["time", "concentrations"])
    means = df.groupby("time").mean()

    header = "time,conc\n"
    out = means.to_records()
    save_csv(f"{outfile}{code}", header, list(zip(*out)), f".PROFILES")

def merge_concentration_profiles(file, out, keys, extension, code, tar=None):
    """Merge center concentrations across conditions."""
    code = code.replace("_CHX_", "_CH_")
    filepath = f"{file}{code}{extension}.csv"

    if tar:
        D = load_csv(filepath.split("/")[-1], tar=tar)
    else:
        D = load_csv(filepath)

    rows = [[keys["context"], keys["level"], keys["profile"]] + r for r in D[1:]]
    out["data"] = out["data"] + rows
    out["header"] = ["context", "level", "profile"] + D[0]

def save_concentration_profiles(file, extension, out):
    """Save merged concentrations files."""
    header = ",".join(out["header"]) + "\n"
    save_csv(file, header, list(zip(*out["data"])), extension)
