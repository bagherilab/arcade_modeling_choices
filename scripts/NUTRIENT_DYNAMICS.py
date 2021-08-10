from .utilities import load, load_tar
import tarfile

class NUTRIENT_DYNAMICS():
    NAME = "NUTRIENT_DYNAMICS"

    CONTEXTS = [
        ('C', '', []),
        ('CH', 'X', [1])
    ]

    LEVELS = ["BASAL", "HIGH", "LOW"]

    PROFILES = ["cycle", "pulse", "constant"]

    @staticmethod
    def run(output_path, input_path, func, name=NAME,
            contexts=CONTEXTS, levels=LEVELS, profiles=PROFILES,
            timepoints=[], seeds=[]):
        outfile = f"{output_path}{name}/{name}"

        for context, suffix, exclude in contexts:
            for level in levels:
                for profile in profiles:
                    code = f"_{context}{suffix}_{level}_{profile}"
                    infile = f"{input_path}{name}/{name}_{context}_{level}_{profile}.csv.xz"

                    print(f"{name} : {code}")

                    loaded = load(infile, exclude)
                    func(*loaded, outfile, code, timepoints=timepoints, seeds=seeds)

    @staticmethod
    def load(output_path, input_path, func, extension="", name=NAME,
             contexts=CONTEXTS, levels=LEVELS, profiles=PROFILES,
             timepoints=[], seeds=[]):
        outfile = f"{output_path}{name}/{name}"

        for context, _, exclude in contexts:
            for level in levels:
                for profile in profiles:
                    code = f"_{context}_{level}_{profile}"
                    infile = f"{input_path}{name}{extension}/{name}_{context}_{level}_{profile}{extension}.tar.xz"

                    print(f"{name} : {code}")

                    tar = tarfile.open(infile)
                    key = { "context": context, "level": level, "profile": profile }
                    func(tar, timepoints, key, outfile, code)

    @staticmethod
    def loop(output_path, func1, func2, extension, name=NAME,
             contexts=CONTEXTS, levels=LEVELS, profiles=PROFILES,
             timepoints=[]):
        outfile = f"{output_path}{name}/{name}"
        out = { "data": [] }
        tar = load_tar(outfile, extension)

        for context, suffix, exclude in contexts:
            for t in timepoints:
                for level in levels:
                    for profile in profiles:
                        code = f"_{context}{suffix}_{level}_{profile}"
                        key = { "time": t, "context": context, "level": level, "profile": profile }
                        func1(outfile, out, key, extension, code, tar=tar)

        func2(outfile, extension, out)
