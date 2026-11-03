"""Plotly chart helpers. Every chart uses the same dark style and zero-based bars."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import C, FONT


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=key)


def style(fig: go.Figure, height: int = 320, legend: bool = False, l: int = 8, r: int = 8, t: int = 10, b: int = 8) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=l, r=r, t=t, b=b),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=C["text"], size=12),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color=C["muted"])),
        hoverlabel=dict(bgcolor=C["surface2"], bordercolor=C["border"], font=dict(family=FONT, color=C["text"], size=12)),
    )
    fig.update_xaxes(gridcolor=C["grid"], zerolinecolor=C["grid"], linecolor=C["border"], tickfont=dict(color=C["muted"]),
                     title_font=dict(color=C["muted"], size=12))
    fig.update_yaxes(gridcolor=C["grid"], zerolinecolor=C["grid"], linecolor=C["border"], tickfont=dict(color=C["muted"]),
                     title_font=dict(color=C["muted"], size=12))
    return fig


def _pad_range(lo: float, hi: float, include_zero: bool = True) -> list[float]:
    if include_zero:
        lo, hi = min(lo, 0), max(hi, 0)
    pad = (hi - lo) * 0.08 or 1
    return [lo - pad, hi + pad]


# ------------------------------------------------------------------ distributions
def histogram(values: pd.Series, bins: int = 40, color: str = C["blue"], log: bool = False, mean: float | None = None,
              median: float | None = None, x_title: str = "", y_title: str = "Listings", fmt: str = ",.0f",
              tick_vals: list | None = None, tick_text: list | None = None, height: int = 330) -> go.Figure:
    v = values.to_numpy(dtype=float)
    x = np.log10(v) if log else v
    counts, edges = np.histogram(x, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    widths = np.diff(edges)
    real = 10**centers if log else centers
    lo = 10 ** edges[:-1] if log else edges[:-1]
    hi = 10 ** edges[1:] if log else edges[1:]
    fig = go.Figure(go.Bar(
        x=centers, y=counts, width=widths * 0.94, marker=dict(color=color, cornerradius=2),
        customdata=np.column_stack([lo, hi]),
        hovertemplate="%{customdata[0]:,.0f} to %{customdata[1]:,.0f}<br>Listings: %{y:,}<extra></extra>",
    ))
    for val, name, dash, col, pos in [(mean, "Mean", "dash", C["amber"], "top right"), (median, "Median", "dot", C["green"], "top left")]:
        if val is not None and np.isfinite(val):
            xv = np.log10(val) if log else val
            fig.add_vline(x=xv, line_dash=dash, line_color=col, line_width=1.6,
                          annotation_text=f"{name} {val:{fmt}}", annotation_position=pos, annotation_font=dict(color=col, size=11))
    if log and tick_vals:
        fig.update_xaxes(tickvals=np.log10(tick_vals), ticktext=tick_text)
    fig.update_xaxes(title=x_title)
    fig.update_yaxes(title=y_title, tickformat=",")
    fig.update_layout(bargap=0.04)
    return style(fig, height, t=28)


def density_heatmap(x: pd.Series, y: pd.Series, nx: int = 36, ny: int = 36, x_title: str = "", y_title: str = "", height: int = 340) -> go.Figure:
    counts, xe, ye = np.histogram2d(x.to_numpy(float), y.to_numpy(float), bins=[nx, ny])
    xc, yc = (xe[:-1] + xe[1:]) / 2, (ye[:-1] + ye[1:]) / 2
    fig = go.Figure(go.Heatmap(
        x=xc, y=yc, z=counts.T, colorscale=[[0, C["surface"]], [0.5, "#1F4B7A"], [1, C["blue"]]],
        colorbar=dict(title=dict(text="Listings", font=dict(color=C["muted"], size=11)), tickfont=dict(color=C["muted"]), thickness=10),
        hovertemplate=f"{x_title}: %{{x:,.0f}}<br>{y_title}: %{{y:,.0f}}<br>Listings: %{{z:,}}<extra></extra>",
    ))
    fig.update_xaxes(title=x_title, tickformat=",")
    fig.update_yaxes(title=y_title, tickformat=",")
    return style(fig, height)


# ------------------------------------------------------------------ group comparisons
def bar_ci(gs: pd.DataFrame, overall: float, x_title: str, fmt: str = ",.0f", color: str = C["blue"], horizontal: bool = True,
           height: int | None = None, prefix: str = "", suffix: str = "") -> go.Figure:
    """Zero-based bars with 95% confidence whiskers and an all-listings reference line."""
    k = len(gs)
    labels = gs["group"].tolist()
    text = [f"{prefix}{v:{fmt}}{suffix}" for v in gs["mean"]]
    if horizontal:
        fig = go.Figure(go.Bar(
            y=labels, x=gs["mean"], orientation="h", marker=dict(color=color, cornerradius=3),
            error_x=dict(type="data", array=gs["ci"], color=C["text"], thickness=1.1, width=3),
            text=text, textposition="inside", insidetextanchor="start", textfont=dict(color="#0B1220", size=11),
            customdata=np.column_stack([gs["n"]]),
            hovertemplate="<b>%{y}</b><br>" + x_title + f": {prefix}%{{x:{fmt}}}{suffix}<br>Listings: %{{customdata[0]:,}}<extra></extra>",
        ))
        fig.add_vline(x=overall, line_dash="dash", line_color=C["amber"], line_width=1.4,
                      annotation_text=f"All listings {prefix}{overall:{fmt}}{suffix}", annotation_position="top",
                      annotation_font=dict(color=C["amber"], size=11))
        fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=C["text"]))
        fig.update_xaxes(title=x_title, rangemode="tozero", tickformat=",")
        h = height or max(260, 24 * k + 70)
    else:
        fig = go.Figure(go.Bar(
            x=labels, y=gs["mean"], marker=dict(color=color, cornerradius=3),
            error_y=dict(type="data", array=gs["ci"], color=C["text"], thickness=1.1, width=3),
            text=text, textposition="inside", insidetextanchor="end", textfont=dict(color="#0B1220", size=11),
            customdata=np.column_stack([gs["n"]]),
            hovertemplate="<b>%{x}</b><br>" + x_title + f": {prefix}%{{y:{fmt}}}{suffix}<br>Listings: %{{customdata[0]:,}}<extra></extra>",
        ))
        fig.add_hline(y=overall, line_dash="dash", line_color=C["amber"], line_width=1.4)
        fig.update_yaxes(title=x_title, rangemode="tozero", tickformat=",")
        fig.update_xaxes(showgrid=False, type="category")
        h = height or 320
    return style(fig, h, t=28 if horizontal else 10)


def deviation_chart(gs: pd.DataFrame, x_title: str = "Difference from all other listings (%)", horizontal: bool = True,
                    height: int | None = None) -> go.Figure:
    """Each group's difference from everything else, with 95% intervals.

    Amber dots are differences that survive correction for the number of groups; grey dots are within normal variation.
    """
    k = len(gs)
    colors = [C["amber"] if s else C["slate"] for s in gs["sig"]]
    lo = float((gs["diff_pct"] - gs["ci_pct"]).min())
    hi = float((gs["diff_pct"] + gs["ci_pct"]).max())
    rng = _pad_range(lo, hi)
    hover = ("<b>%{customdata[0]}</b><br>Difference: %{customdata[1]:+.2f}%<br>95% interval: +/- %{customdata[2]:.2f}%"
             "<br>Adjusted p: %{customdata[3]:.3f}<br>Listings: %{customdata[4]:,}<extra></extra>")
    cd = np.column_stack([gs["group"], gs["diff_pct"], gs["ci_pct"], gs["p_adj"].fillna(1.0), gs["n"]])
    if horizontal:
        fig = go.Figure(go.Scatter(
            x=gs["diff_pct"], y=gs["group"], mode="markers", marker=dict(size=9, color=colors, line=dict(color=C["bg"], width=1.5)),
            error_x=dict(type="data", array=gs["ci_pct"], color=C["border"], thickness=2.2, width=0), customdata=cd, hovertemplate=hover))
        fig.add_vline(x=0, line_color=C["muted"], line_width=1, line_dash="dash")
        fig.update_xaxes(title=x_title, ticksuffix="%", range=rng)
        fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=C["text"]), type="category")
        h = height or max(240, 22 * k + 80)
    else:
        fig = go.Figure(go.Scatter(
            x=gs["group"], y=gs["diff_pct"], mode="markers", marker=dict(size=9, color=colors, line=dict(color=C["bg"], width=1.5)),
            error_y=dict(type="data", array=gs["ci_pct"], color=C["border"], thickness=2.2, width=0), customdata=cd, hovertemplate=hover))
        fig.add_hline(y=0, line_color=C["muted"], line_width=1, line_dash="dash")
        fig.update_yaxes(title=x_title, ticksuffix="%", range=rng)
        fig.update_xaxes(showgrid=False, type="category")
        h = height or 320
    return style(fig, h)


def correlation_heatmap(corr: pd.DataFrame, labels: dict[str, str], height: int = 420) -> go.Figure:
    cols = list(corr.columns)
    names = [labels.get(c, c) for c in cols]
    z = corr.to_numpy(dtype=float).copy()
    mask = np.triu(np.ones_like(z, dtype=bool), k=1)
    z[mask] = np.nan
    text = np.where(np.isnan(z), "", np.char.mod("%.2f", np.nan_to_num(z)))
    fig = go.Figure(go.Heatmap(
        z=z, x=names, y=names, zmin=-1, zmax=1, text=text, texttemplate="%{text}", textfont=dict(size=10),
        colorscale=[[0, C["coral"]], [0.5, C["surface"]], [1, C["blue"]]], xgap=2, ygap=2,
        colorbar=dict(title=dict(text="Spearman", font=dict(color=C["muted"], size=11)), tickfont=dict(color=C["muted"]), thickness=10),
        hovertemplate="%{y} and %{x}: %{z:.3f}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=C["text"]))
    fig.update_xaxes(showgrid=False, tickangle=-40, tickfont=dict(size=11, color=C["text"]))
    return style(fig, height, l=4, b=4)
