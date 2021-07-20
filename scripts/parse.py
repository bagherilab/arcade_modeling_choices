import tarfile
import lzma
import io
import numpy as np
from glob import glob
from tqdm import tqdm
from .utilities import *

# PARSING UTILITY FUNCTIONS ====================================================

def get_files(path, name):
    """Gets list of files from directory."""
    return glob(f"{path}**/{name}*.tar.xz") + glob(f"{path}**/{name}*.json")

def get_struct(c):
    """Convert cell features into tuple."""
    if c[-1]:
        return [c[1], c[2], np.round(c[4]), np.round(np.mean(c[-1]))]
    else:
        return [c[1], c[2], np.round(c[4]), -1]

def get_timepoints(timepoints):
    """Gets list fo cell features for each timepoint."""
    lst = [[tp["time"]] + coord + [cell[3]] + get_struct(cell)
        for tp in timepoints
        for coord, cells in tp["cells"]
        for cell in cells]
    return lst

def get_header(jsn):
    """Gets appropriate header for given geometry."""
    geometry = 0

    for timepoint in jsn["timepoints"]:
        if len(timepoint['cells']) > 0:
            geometry = len(timepoint['cells'][0][0])
            break

    return f"t,{'x,y' if geometry == 3 else 'u,v,w'},z,p,pop,state,volume,cycle\n"

# GENERAL PARSING ==============================================================

def parse_simulation_tar(tar, outfile, exclude):
    """Parse each simulation in tar archive into compressed csv."""
    with open(outfile + ".csv.xz", 'wb') as buffer:
        with lzma.open(buffer, "wb") as lzf:
            # Save header.
            member = tar.getmembers()[0]
            header = "i," + get_header(load_json(member, tar=tar))
            lzf.write(header.encode("utf-8"))

            # Iterate through all members of the tar.
            for member in tqdm(tar.getmembers()):
                seed = int(member.name.replace(".json", "").split("_")[-1])

                # Skip if seed is in exclude list.
                if seed in exclude:
                    continue

                # Extract results from each timepoint.
                jsn = load_json(member, tar=tar)
                timepoints = get_timepoints(jsn["timepoints"])

                # Format each row and compress.
                rows = [f"{seed}," + ",".join(map(str, tp)).replace(".0,", ",") for tp in timepoints]
                lzf.write("\n".join(rows).encode("utf-8"))
                lzf.write("\n".encode("utf-8"))

def parse_simulation_json(jsn, outfile, exclude):
    """Parse simulation instance into compressed csv."""
    with open(outfile + ".csv.xz", 'wb') as buffer:
        with lzma.open(buffer, "wb") as lzf:
            # Save header.
            header = get_header(jsn)
            lzf.write(header.encode("utf-8"))

            # Extract results from each timepoint.
            timepoints = get_timepoints(jsn["timepoints"])

            # Format each row and compress.
            rows = [",".join(map(str, tp)).replace(".0,", ",") for tp in timepoints]
            lzf.write("\n".join(rows).encode("utf-8"))

def parse_simulations(name, data_path, result_path, exclude):
    """Parses simulation files."""

    for file in get_files(data_path, name):
        print(file)
        outfile = file.replace(".tar.xz", "").replace(".json", "").replace(data_path, result_path)

        if is_tar(file):
            tar = tarfile.open(file, "r:xz")
            parse_simulation_tar(tar, outfile, exclude)
        else:
            jsn = load_json(file)
            parse_simulation_json(jsn, outfile, exclude)
