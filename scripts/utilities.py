import json
import csv

def load_json(json_file, tar=None):
    """Load .json file."""
    if tar:
        file = tar.extractfile(json_file)
        contents = [line.decode("utf-8") for line in file.readlines()]
        return json.loads("".join(contents))
    else:
        return json.load(open(json_file, "r"))

def save_csv(filename, header, elements, extension):
    """Save contents as csv."""
    with open(filename + extension + ".csv", 'w') as f:
        f.write(header)

        wr = csv.writer(f)
        [wr.writerow(e) for e in zip(*elements)]

