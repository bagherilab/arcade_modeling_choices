from math import sqrt
from scipy.stats import norm, shapiro, levene, f
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from .utilities import *

# DATA LOADING =================================================================

def load_anova_data(file, out, keys, extension, code, tar=None):
    """Load data for ANOVA."""
    filepath = f"{file}{code}{extension}.json"

    if tar:
        D = load_json(filepath.split("/")[-1], tar=tar)
    else:
        D = load_json(filepath)

    d = next(d["_"] for d in D if d["time"] == keys["time"])
    out.append(convert_to_dataframe(d, keys))

    # Check for special case of 3D simulations.
    if "dimension" in keys and keys["dimension"] == "3D":
        layer_tar = load_tar(file, ".LAYERS")
        layer_filepath = filepath.replace("SEEDS", "LAYERS.SEEDS")

        if tar:
            D = load_json(layer_filepath.split("/")[-1], tar=layer_tar)
        else:
            D = load_json(layer_filepath)

        d = next(d["_"] for d in D if d["time"] == keys["time"])
        keys["dimension"] = "3DC"
        out.append(convert_to_dataframe(d, keys))

def convert_to_dataframe(data, keys):
    """Convert list of values and keys into dataframe."""
    features = list(keys.keys())
    rows = [[row] + [keys[f] for f in features] for row in data if row != "nan"]
    df = pd.DataFrame(rows, columns=["metric"] + features)
    df = df.drop(["time"], axis=1)
    df = df.astype({"metric": "float64"})
    return df

# UTILITY FUNCTIONS ============================================================

def get_levels(df):
    """Get unique factor levels."""
    levels_a = list(df.X1.unique())
    levels_b = list(df.X2.unique())
    return levels_a, levels_b

def get_subsets(df):
    """Get subsets of data for each level and factor."""
    levels_a, levels_b = get_levels(df)
    subsets = [(a, b, df[(df.X1 == a) & (df.X2 == b)].Y)
        for a in levels_a
        for b in levels_b]
    return subsets

def get_sum_within(df, a, b):
    """Calculate sum within."""
    Y = df[(df.X1 == a) & (df.X2 == b)].Y
    mean = Y.mean()
    return sum([(y - mean)**2 for y in Y])

def get_sum_interact(df, a, b):
    """Calculate interaction sum."""
    Y12 = df[(df.X1 == a) & (df.X2 == b)].Y.mean()
    Y1 = df[df.X1 == a].Y.mean()
    Y2 = df[df.X2 == b].Y.mean()
    return (Y12 - Y1 - Y2 + df.Y.mean())**2

# ASSUMPTION TESTING ===========================================================

def calculate_skewness(df):
    """Calculated standardized skewness."""
    n = len(df)
    coeff = sqrt(n*(n - 1))/(n - 2)
    mean = df.mean()
    numerator = (1/n)*sum([(y - mean)**3 for y in df])
    denominator = ((1/n)*sum([(y - mean)**2 for y in df]))**(3/2)

    skew = coeff*numerator/denominator
    se = sqrt((6*n*(n - 1))/((n - 2)*(n + 1)*(n + 3)))

    return coeff*numerator/denominator/se

def test_skewness(df, alpha=0.01):
    """Test for normality using standardized skewness."""
    # Get data subsets
    subsets = get_subsets(df)

    # Calculate skewness
    skewness = [calculate_skewness(df_ab) for a, b, df_ab in subsets]

    # Critical values
    interval = norm().interval(1 - alpha)

    # Check skewness against interval
    test = [s > interval[0] and s < interval[1] for s in skewness]

    # Save results
    results = {
        'factor_a': [a for (a, b, df_ab) in subsets],
        'factor_b': [b for (a, b, df_ab) in subsets],
        'skewness': skewness,
        'is_normal': test
    }

    columns = ['factor_a', 'factor_b', 'skewness', 'is_normal']
    table = pd.DataFrame(results, columns=columns)
    return table

def test_shapiro(df, alpha=0.01):
    """Test for normality using Shapiro-Wilks."""

    # Get data subsets
    subsets = get_subsets(df)

    # Run shapiro-wilk
    shapirowilk = [shapiro(df_ab) for a, b, df_ab in subsets]

    # Check p value against alpha
    test = [p >= alpha for t, p in shapirowilk]

    # Save results
    results = {
        'factor_a': [a for (a, b, df_ab) in subsets],
        'factor_b': [b for (a, b, df_ab) in subsets],
        'test_statistic': [t for t, p in shapirowilk],
        'p_value': [p for t, p in shapirowilk],
        'is_normal': test
    }

    columns = ['factor_a', 'factor_b', 'test_statistic', 'p_value', 'is_normal']
    table = pd.DataFrame(results, columns=columns)
    return table

def test_levene(df, alpha=0.01):
    """Test for homogeneity of variance using Levene's."""

    # Get data subsets
    subsets = get_subsets(df)

    # Calculate variances for each subset
    variances = [np.var(df_ab) for a, b, df_ab in subsets]

    # Run test
    lev = levene(*[df_ab for a, b, df_ab in subsets], center="median")

    # Save results
    results = {
        'factor_a': [a for (a, b, df_ab) in subsets],
        'factor_b': [b for (a, b, df_ab) in subsets],
        'variance': variances
    }

    print(f"F({len(subsets) - 1},{len(df) - len(subsets)}) = {lev[0]:.4f} | p = {lev[1]:.4f}")
    print(f"is_homoscedastic = {lev[1] > alpha}")
    print(f"largest fold difference in variance  = {np.max(variances)/np.min(variances):.2f}")

    columns = ['factor_a', 'factor_b', 'variance']
    table = pd.DataFrame(results, columns=columns)
    return table

# SUMMARY MEANS ================================================================

def calculate_cell_means(df):
    """Calculate means for each level combination.."""

    # Get data subsets
    subsets = get_subsets(df)

    # Make results table
    columns = ['factor_a', 'factor_b', 'mean', 'std', 'num']
    table = pd.DataFrame(columns=columns)

    i = 0

    # Get cell means and standard deviations
    for a, b, df_ab in subsets:
        mean = np.mean(df_ab)
        std = np.std(df_ab, ddof=1)
        num = len(df_ab.index)

        table.loc[i] = [a, b, mean, std, num]
        i = i + 1

    return table

def calculate_effect_means(df):
    """Calculate means for each effect."""

    # Get data levels
    levels_a, levels_b = get_levels(df)

    # Make results table
    columns = ['factor', 'level', 'mean', 'std', 'num']
    table = pd.DataFrame(columns=columns)

    i = 0

    # Get effect means and standard deviations
    for a in levels_a:
        df_a = df[df.X1 == a].Y
        table.loc[i] = ["A", a, np.mean(df_a), np.std(df_a, ddof=1), len(df_a.index)]
        i = i + 1

    for b in levels_b:
        df_b = df[df.X2 == b].Y
        table.loc[i] = ["B", b, np.mean(df_b), np.std(df_b, ddof=1), len(df_b.index)]
        i = i + 1

    return table

# ANOVA ========================================================================

def run_two_way_anova_with_interaction(df, alpha=0.01):
    """Run two-way ANOVA with interaction."""

    # Get data levels
    levels_a, levels_b = get_levels(df)

    # Calculate degrees of freedom
    a = len(levels_a)
    b = len(levels_b)
    r = int(len(df.Y)/(a*b))
    dof_a = a - 1
    dof_b = b - 1
    dof_w = a*b*(r - 1)
    dof_axb = dof_a*dof_b
    dof_t = len(df.Y) - 1

    # Calculate sum of squares
    grand_mean = df.Y.mean()
    ss_a = r*b*sum([(df[df.X1 == a].Y.mean() - grand_mean)**2 for a in levels_a])
    ss_b = r*a*sum([(df[df.X2 == b].Y.mean() - grand_mean)**2 for b in levels_b])
    ss_w = sum([get_sum_within(df, a, b) for a in levels_a for b in levels_b])
    ss_axb = r*sum([get_sum_interact(df, a, b) for a in levels_a for b in levels_b])
    ss_t = sum((df.Y - grand_mean)**2)

    # Calculate mean squared error
    ms_a = ss_a/dof_a
    ms_b = ss_b/dof_b
    ms_w = ss_w/dof_w
    ms_axb = ss_axb/dof_axb

    # Calculate F statistic
    f_a = ms_a/ms_w
    f_b = ms_b/ms_w
    f_axb = ms_axb/ms_w

    # Calculate p values
    p_a = f.sf(f_a, dof_a, dof_w)
    p_b = f.sf(f_b, dof_b, dof_w)
    p_axb = f.sf(f_axb, dof_axb, dof_w)

    results = {
        'sum_sq': [ss_a, ss_b, ss_axb, ss_w, ss_t],
        'dof': [dof_a, dof_b, dof_axb, dof_w, dof_t],
        'mse': [ms_a, ms_b, ms_axb, ms_w, np.nan],
        'F': [f_a, f_b, f_axb, np.nan, np.nan],
        'PR(>F)': [p_a, p_b, p_axb, np.nan, np.nan],
        'is_significant': [(p_a < alpha), (p_b < alpha), (p_axb < alpha), np.nan, np.nan],
    }

    columns = ['sum_sq', 'dof', 'mse', 'F', 'PR(>F)', 'is_significant']
    table = pd.DataFrame(results, columns=columns, index=['X1', 'X2', 'X1:X2', 'Residual', 'Total'])

    return table

def run_two_way_anova_without_interaction(df, alpha=0.01):
    """Run two-way ANOVA without interaction."""

    # Get data levels
    levels_a, levels_b = get_levels(df)

    # Calculate degrees of freedom
    a = len(levels_a)
    b = len(levels_b)
    r = int(len(df.Y)/(a*b))
    dof_a = a - 1
    dof_b = b - 1
    dof_w = a*b*(r - 1)
    dof_axb = dof_a*dof_b
    dof_pooled = dof_w + dof_axb
    dof_t = len(df.Y) - 1

    # Calculate sum of squares
    grand_mean = df.Y.mean()
    ss_a = r*b*sum([(df[df.X1 == a].Y.mean() - grand_mean)**2 for a in levels_a])
    ss_b = r*a*sum([(df[df.X2 == b].Y.mean() - grand_mean)**2 for b in levels_b])
    ss_w = sum([get_sum_within(df, a, b) for a in levels_a for b in levels_b])
    ss_axb = r*sum([get_sum_interact(df, a, b) for a in levels_a for b in levels_b])
    ss_pooled = ss_w + ss_axb
    ss_t = sum((df.Y - grand_mean)**2)

    # Calculate mean squared error
    ms_a = ss_a/dof_a
    ms_b = ss_b/dof_b
    ms_pooled = ss_pooled/dof_pooled

    # Calculate F statistic
    f_a = ms_a/ms_pooled
    f_b = ms_b/ms_pooled

    # Calculate p values
    p_a = f.sf(f_a, dof_a, dof_pooled)
    p_b = f.sf(f_b, dof_b, dof_pooled)

    results = {
        'sum_sq': [ss_a, ss_b, ss_pooled, ss_t],
        'dof': [dof_a, dof_b, dof_pooled, dof_t],
        'mse': [ms_a, ms_b, ms_pooled, np.nan],
        'F': [f_a, f_b, np.nan, np.nan],
        'PR(>F)': [p_a, p_b, np.nan, np.nan],
        'is_significant': [(p_a < alpha), (p_b < alpha), np.nan, np.nan],
    }

    columns = ['sum_sq', 'dof', 'mse', 'F', 'PR(>F)', 'is_significant']
    table = pd.DataFrame(results, columns=columns, index=['X1', 'X2', 'Residual', 'Total'])

    return table

def run_simple_main_effects(df, factor, alpha=0.01):
    """Run simple main effects testing."""

    # Get data levels
    levels_a, levels_b = get_levels(df)

    # Get item counts
    a = len(levels_a)
    b = len(levels_b)
    r = int(len(df.Y)/(a*b))

    # Calculate overall terms
    dof_w = a*b*(r - 1)
    ss_w = sum([get_sum_within(df, a, b) for a in levels_a for b in levels_b])
    ms_w = ss_w/dof_w

    # Select which factor is being analyzed.
    if factor == "X1":
        factor_subset = "X2"
        levels_subset = levels_b
        levels_factor = levels_a
        n = b
    elif factor == "X2":
        factor_subset = "X1"
        levels_subset = levels_a
        levels_factor = levels_b
        n = a
    else:
        return

    # Simple main effects for factor
    alpha_bonferroni = alpha/n
    results = []

    for subset in levels_subset:
        # Get subset of the data
        df_subset = df[df[factor_subset] == subset]

        # Calculate degrees of freedom
        dof_factor = len(levels_factor) - 1

        # Calculate sum of squares
        grand_mean = df_subset.Y.mean()
        ss_factor = r*sum([(df_subset[df_subset[factor] == level].Y.mean() - grand_mean)**2
            for level in levels_factor])

        # Calculate mean squared error, F statistic, and p value
        ms_factor = ss_factor/dof_factor
        f_factor = ms_factor/ms_w
        p_factor = f.sf(f_factor, dof_factor, dof_w)

        # Save results to array
        results.append([ss_factor, dof_factor, ms_factor, f_factor, p_factor, (p_factor < alpha_bonferroni)])

    columns = ['sum_sq', 'dof', 'mse', 'F', 'PR(>F)', 'is_significant']
    table = pd.DataFrame(results, columns=columns, index=levels_subset)

    return table

def run_tukey_tests(df, factor, interaction, alpha=0.01):
    """Run pairwise Tukey tests."""

    # Get data levels
    levels_a, levels_b = get_levels(df)

    if factor == "X1":
        factor_subset = "X2"
        levels_subset = levels_b
        levels_factor = levels_a
    elif factor == "X2":
        factor_subset = "X1"
        levels_subset = levels_a
        levels_factor = levels_b
    else:
        return

    # Do not run Tukey if only 2 levels.
    if len(levels_factor) < 3:
        return

    if interaction:
        columns = ['level', 'group1', 'group2', 'meandiff', 'p-adj', 'lower', 'upper', 'is_significant']
        results = []

        for subset in levels_subset:
            # Get subset of the data
            df_subset = df[df[factor_subset] == subset]

            # Get results
            results_summary = pairwise_tukeyhsd(df_subset.Y, df_subset[factor], alpha=alpha).summary()
            results_as_csv = results_summary.as_csv().replace(" ", "").split("\n")[2:]
            [results.append([subset] + row.split(",")) for row in results_as_csv]

        df = pd.DataFrame(results, columns=columns)
    else:
        columns = ['group1', 'group2', 'meandiff', 'p-adj', 'lower', 'upper', 'is_significant']
        results_summary = pairwise_tukeyhsd(df.Y, df[factor], alpha=alpha).summary()
        results_as_csv = results_summary.as_csv().replace(" ", "").split("\n")[2:]
        results = [row.split(",") for row in results_as_csv]
        df = pd.DataFrame(results, columns=columns)

    df[["meandiff", "p-adj", "lower", "upper"]] = df[["meandiff", "p-adj", "lower", "upper"]].apply(pd.to_numeric)
    return df
