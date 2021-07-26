from .utilities import load

class CELL_STOCHASTICITY():
    NAME = "CELL_STOCHASTICITY"

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
