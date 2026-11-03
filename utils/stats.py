"""Group comparisons built from sums, so they stay fast on 250,000 rows.

Each group is compared with all other listings (Welch z-test) and p-values are Bonferroni
corrected for the number of groups. The overall test is a one-way ANOVA with eta squared.
"""
import numpy as np
import pandas as pd
from scipy import stats as sps


def _prep(df: pd.DataFrame, by: str, value: str, log: bool = False) -> pd.DataFrame:
    x = df[value].astype(float)
    if log:
        x = np.log10(x.clip(lower=1e-9))
    tmp = pd.DataFrame({"g": df[by].astype(str).values, "x": x.values})
    tmp["x2"] = tmp["x"] ** 2
    return tmp


def group_stats(df: pd.DataFrame, by: str, value: str) -> pd.DataFrame:
    """Per-group mean, 95% CI and difference against all other listings."""
    tmp = _prep(df, by, value)
    agg = tmp.groupby("g", sort=False).agg(n=("x", "size"), s=("x", "sum"), s2=("x2", "sum"))
    n_all, s_all, s2_all = agg["n"].sum(), agg["s"].sum(), agg["s2"].sum()
    k = len(agg)

    n, s, s2 = agg["n"].astype(float), agg["s"], agg["s2"]
    mean = s / n
    var = ((s2 - n * mean**2) / (n - 1)).where(n > 1)
    n_r = n_all - n
    s_r, s2_r = s_all - s, s2_all - s2
    mean_r = (s_r / n_r).where(n_r > 0)
    var_r = ((s2_r - n_r * mean_r**2) / (n_r - 1)).where(n_r > 1)

    diff = mean - mean_r
    se = np.sqrt(var / n + var_r / n_r)
    z = diff / se
    p = pd.Series(2 * sps.norm.sf(np.abs(z)), index=agg.index).where(se > 0)
    p_adj = (p * k).clip(upper=1.0)

    out = pd.DataFrame({
        "group": agg.index,
        "n": agg["n"].values,
        "mean": mean.values,
        "se_mean": np.sqrt(var / n).values,
        "diff": diff.values,
        "diff_pct": (diff / mean_r * 100).values,
        "ci_pct": (1.96 * se / mean_r * 100).values,
        "p": p.values,
        "p_adj": p_adj.values,
    })
    out["ci"] = 1.96 * out["se_mean"]
    out["sig"] = out["p_adj"] < 0.05
    return out


def anova(df: pd.DataFrame, by: str, value: str, log: bool = False) -> dict:
    """One-way ANOVA with eta squared (share of variation explained by the grouping)."""
    tmp = _prep(df, by, value, log)
    agg = tmp.groupby("g", sort=False).agg(n=("x", "size"), s=("x", "sum"), s2=("x2", "sum"))
    agg = agg[agg["n"] > 0]
    k, n_all = len(agg), int(agg["n"].sum())
    if k < 2 or n_all - k < 1:
        return {"F": np.nan, "p": np.nan, "eta2": np.nan, "k": k, "n": n_all}
    grand = agg["s"].sum() / n_all
    mean = agg["s"] / agg["n"]
    ssb = float((agg["n"] * (mean - grand) ** 2).sum())
    ssw = float((agg["s2"] - agg["n"] * mean**2).sum())
    if ssw <= 0:
        return {"F": np.nan, "p": np.nan, "eta2": np.nan, "k": k, "n": n_all}
    f = (ssb / (k - 1)) / (ssw / (n_all - k))
    return {"F": f, "p": float(sps.f.sf(f, k - 1, n_all - k)), "eta2": ssb / (ssb + ssw), "k": k, "n": n_all}


def verdict(test: dict, gs: pd.DataFrame) -> tuple[str, str]:
    if np.isnan(test["p"]):
        return "Not enough data", "muted"
    if test["p"] < 0.05 and gs["sig"].any():
        return "Real difference", "good"
    if test["p"] < 0.05:
        return "Weak signal", "warn"
    return "Within normal variation", "muted"


def p_text(p: float) -> str:
    if np.isnan(p):
        return "p not available"
    return "p < 0.001" if p < 0.001 else f"p = {p:.2f}"


def flag_effects(df: pd.DataFrame, flags: dict[str, str], value: str) -> pd.DataFrame:
    """For each 0/1 column: difference between listings with the feature and without it."""
    rows = []
    k = len(flags)
    for label, col in flags.items():
        gs = group_stats(df, col, value)
        gs = gs[gs["group"] == "1"]
        if gs.empty:
            continue
        r = gs.iloc[0]
        p_adj = min(1.0, r["p"] * k) if not np.isnan(r["p"]) else np.nan
        rows.append({"group": label, "n": r["n"], "mean": r["mean"], "diff_pct": r["diff_pct"], "ci_pct": r["ci_pct"],
                     "p": r["p"], "p_adj": p_adj, "sig": bool(p_adj < 0.05) if not np.isnan(p_adj) else False})
    return pd.DataFrame(rows)
