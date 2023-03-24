## Setup files

The `setups` directory contains all the setup files used for running simulations.
Simulations were run using **[ARCADE v2.4](https://github.com/bagherilab/ARCADE/releases/tag/v2.4)**.

## Pipeline notebooks

#### Parse simulation outputs

The **[`parse_simulation_outputs`](parse_simulation_outputs.ipynb)** notebook provides the functions and scripts for parsing simulation files (`.json`) into compressed csvs (`.csv.xz`).
These parsed results are included with the raw simulation data.

#### Analyze data & results

The **[`analyze_data_results`](analyze_data_results.ipynb)** notebook provides functions and scripts for running basic analysis on simulation data and parsed results.
All resulting `.json` and `.csv` files are provided in the `analysis` directory.

#### Generate figure inputs

The **[`generate_figure_inputs`](generate_figure_inputs.ipynb)** notebook walks through all the steps necessary to generate figure input files from raw data, parsed files, and basic analysis files.
All resulting files are provided in the `analysis` directory.
Refer to figure section in notebook for more details.

To view figures, start a local HTTP server from the root folder, which can be done using Python or PHP:

```bash
$ python3 -m http.server
$ php -S 127.0.0.1:8000
```

Note that the links in the notebook to figures assume the local port 8000; if your server is running on a different port, the links to the figures from the notebook will not work.
Instead, you can navigate to `http://localhost:XXXX/` where `XXXX` is the port number and follow links to the figures.

#### Run ANOVA tests

The **[`run_anova_tests`](run_anova_tests.ipynb)** notebook works through the process of running ANOVA for each of the simulation sets.
ANOVA results are compiled into three files (included in the `analysis` directory) and used to generate the `anova_summary` figures.
