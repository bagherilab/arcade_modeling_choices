from .utilities import load

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
