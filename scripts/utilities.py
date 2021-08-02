import json
import csv
import re
import lzma
import numpy as np
import pandas as pd

DTYPES = {
    "i": "uint8",
    "t": "float16",
    "u": "int16",
    "v": "int16",
    "w": "int16",
    "x": "int16",
    "y": "int16",
    "z": "int16",
    "pop": "uint8",
    "state": "uint8",
    "volume": "uint16",
    "cycle": "int16",
}

CHUNKSIZE = 1000000

def load(filename, exclude=[]):
    """Load contents of compressed results file."""
    with lzma.open(filename, 'r') as file:
        df = pd.DataFrame()

        for chunk in pd.read_csv(file, chunksize=CHUNKSIZE, dtype=DTYPES):
            print(chunk.iloc[0,:])
            chunk = chunk[~chunk['pop'].isin(exclude)]
            df = pd.concat([df, chunk])

    T = df.t.unique().tolist()
    N = df.i.unique().tolist()

    # Make sure ticks starts with zero.
    if T[0] != 0:
        t1 = T[0]
        t2 = T[1]
        delta = t2 - t1
        T0 = list(np.arange(0, t1, delta))
        T = T0 + T

    return df, T, N


def load_json(json_file, tar=None):
    """Load .json file."""
    if tar:
        file = tar.extractfile(json_file)
        contents = [line.decode("utf-8") for line in file.readlines()]
        return json.loads("".join(contents))
    else:
        return json.load(open(json_file, "r"))

def save_json(filename, out, extension):
    """Save contents as json."""
    with open(filename + extension + ".json", "w") as f:
        jn = json.dumps(out, indent = 4, separators = (',', ':'), sort_keys=True)
        f.write(format_json(jn).replace("NaN", '"nan"'))

def save_csv(filename, header, elements, extension):
    """Save contents as csv."""
    with open(filename + extension + ".csv", 'w') as f:
        f.write(header)

        wr = csv.writer(f)
        [wr.writerow(e) for e in zip(*elements)]

def format_json(jn):
    """Format json contents."""
    jn = jn.replace(":", ": ")
    for arr in re.findall('\[\n\s+[A-z0-9$",\-\.\n\s]*\]', jn):
        jn = jn.replace(arr, re.sub(r',\n\s+', r',', arr))
    jn = re.sub(r'\[\n\s+([A-Za-z0-9,"$\.\-]+)\n\s+\]', r'[\1]', jn)
    jn = jn.replace("],[", "],\n            [")
    return jn

def format_time(time):
    """Format time as string."""
    return str(time).replace(".", "").zfill(3)

def is_tar(file):
    """Check if file has .tar.xz extension."""
    return file[-7:] == ".tar.xz"

