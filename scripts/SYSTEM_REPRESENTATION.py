from .utilities import load

class SYSTEM_REPRESENTATION():
    NAME = "SYSTEM_REPRESENTATION"

    CONTEXTS = [
        ('C', '', []),
        ('CH', 'X', [1])
    ]

    DIMENSIONS = ['2D', '3D']

    GEOMETRIES = ['hex', 'rect']

    @staticmethod
    def run(output_path, input_path, func, name=NAME,
            contexts=CONTEXTS, dimensions=DIMENSIONS, geometries=GEOMETRIES,
            timepoints=[], seeds=[]):
        outfile = f"{output_path}{name}/{name}"

        for context, suffix, exclude in contexts:
            for dim in dimensions:
                for geom in geometries:
                    code = f"_{context}{suffix}_{dim}_{geom}"
                    infile = f"{input_path}{name}/{name}_{context}_{dim}_{geom}.csv.xz"

                    print(f"{name} : {code}")

                    loaded = load(infile)
                    func(*loaded, outfile, code, exclude=exclude, timepoints=timepoints, seeds=seeds)
