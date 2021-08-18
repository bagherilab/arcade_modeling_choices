from .utilities import load, load_tar
import tarfile

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

                    loaded = load(infile, exclude)
                    func(*loaded, outfile, code, timepoints=timepoints, seeds=seeds)

    @staticmethod
    def load(output_path, input_path, func, extension="", name=NAME,
             contexts=CONTEXTS, dimensions=DIMENSIONS, geometries=GEOMETRIES,
             timepoints=[], seeds=[]):
        outfile = f"{output_path}{name}/{name}"

        for context, _, exclude in contexts:
            for dim in dimensions:
                for geom in geometries:
                    code = f"_{context}_{dim}_{geom}"
                    infile = f"{input_path}{name}{extension}/{name}_{context}_{dim}_{geom}{extension}.tar.xz"

                    print(f"{name} : {code}")

                    tar = tarfile.open(infile)
                    key = { "context": context, "dimension": dim, "geometry": geom }
                    func(tar, timepoints, key, outfile, code)

    @staticmethod
    def loop(output_path, func1, func2, extension, name=NAME,
             contexts=CONTEXTS, dimensions=DIMENSIONS, geometries=GEOMETRIES,
             timepoints=[]):
        outfile = f"{output_path}{name}/{name}"
        out = { "data": [] }
        tar = load_tar(outfile, extension)

        for context, suffix, exclude in contexts:
            for t in timepoints:
                for dim in dimensions:
                    for geom in geometries:
                        code = f"_{context}{suffix}_{dim}_{geom}"
                        key = { "time": t, "context": context, "dimension": dim, "geometry": geom }
                        func1(outfile, out, key, extension, code, tar=tar)

        func2(outfile, extension, out)

    @staticmethod
    def get(output_path, func1, func2, extension, name=NAME,
             contexts=CONTEXTS, dimensions=DIMENSIONS, geometries=GEOMETRIES,
             timepoint=0):
        outfile = f"{output_path}{name}/{name}"
        out = []
        tar = load_tar(outfile, extension)

        for context, suffix, exclude in contexts:
            for dim in dimensions:
                for geom in geometries:
                    code = f"_{context}{suffix}_{dim}_{geom}"
                    key = { "time": timepoint, "context": context, "dimension": dim, "geometry": geom }
                    func1(outfile, out, key, extension, code, tar=tar)

        return func2(out)
