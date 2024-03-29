from .utilities import load, load_tar
import tarfile

class CELL_VARIABILITY():
    NAME = "CELL_VARIABILITY"

    CONTEXTS = [
        ('C', '', []),
        ('CH', 'X', [1])
    ]

    VOLUMES = ['V0', 'V1']

    AGES = ['A0', 'A1']

    @staticmethod
    def run(output_path, input_path, func, name=NAME,
            contexts=CONTEXTS, volumes=VOLUMES, ages=AGES,
            timepoints=[], seeds=[]):
        outfile = f"{output_path}{name}/{name}"

        for context, suffix, exclude in contexts:
            for volume in volumes:
                for age in ages:
                    code = f"_{context}{suffix}_{age}_{volume}"
                    infile = f"{input_path}{name}/{name}_{context}_{age}_{volume}.csv.xz"

                    print(f"{name} : {code}")

                    loaded = load(infile, exclude)
                    func(*loaded, outfile, code, timepoints=timepoints, seeds=seeds)

    @staticmethod
    def load(output_path, input_path, func, extension="", name=NAME,
             contexts=CONTEXTS, volumes=VOLUMES, ages=AGES,
             timepoints=[], seeds=[]):
        outfile = f"{output_path}{name}/{name}"

        for context, _, exclude in contexts:
            for volume in volumes:
                for age in ages:
                    code = f"_{context}_{age}_{volume}"
                    infile = f"{input_path}{name}{extension}/{name}_{context}_{age}_{volume}{extension}.tar.xz"

                    print(f"{name} : {code}")

                    tar = tarfile.open(infile)
                    key = { "context": context, "age": age, "volume": volume }
                    func(tar, timepoints, key, outfile, code)

    @staticmethod
    def loop(output_path, func1, func2, extension, name=NAME,
             contexts=CONTEXTS, volumes=VOLUMES, ages=AGES,
             timepoints=[]):
        outfile = f"{output_path}{name}/{name}"
        out = { "data": [] }
        tar = load_tar(outfile, extension)

        for context, suffix, exclude in contexts:
            for t in timepoints:
                for volume in volumes:
                    for age in ages:
                        code = f"_{context}{suffix}_{age}_{volume}"
                        key = { "time": t, "context": context, "age": age, "volume": volume }
                        func1(outfile, out, key, extension, code, tar=tar)

        func2(outfile, extension, out)

    @staticmethod
    def get(output_path, func1, func2, extension, name=NAME,
             contexts=CONTEXTS, volumes=VOLUMES, ages=AGES,
             timepoint=0):
        outfile = f"{output_path}{name}/{name}"
        out = []
        tar = load_tar(outfile, extension)

        for context, suffix, exclude in contexts:
            for volume in volumes:
                for age in ages:
                    code = f"_{context}{suffix}_{age}_{volume}"
                    key = { "time": timepoint, "context": context, "age": age, "volume": volume }
                    func1(outfile, out, key, extension, code, tar=tar)

        return func2(out)
