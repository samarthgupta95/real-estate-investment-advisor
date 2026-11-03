"""Page 1: Market overview. Price and size distributions, and why price per sq ft behaves the way it does."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils.charts import density_heatmap, histogram, show, style
from utils.data import SIZE_ORDER, get_full, get_view, lakh, rupee
from utils.theme import C, callout, card, hero, kpi_row, section

df = get_view()
n, total = len(df), len(get_full())

hero(
    "Real estate investment analytics",
    "How 250,000 Indian property listings are priced, where price per sq ft misleads, and which listings look cheap against comparable ones.",
    n,
    total,
)

# ---------------------------------------------------------------- KPIs
ready = (df["Availability_Status"] == "Ready_to_Move").mean()
kpi_row([
    ("Listings", f"{n:,}", f"{n / total:.0%} of the dataset", C["blue"]),
    ("Median price", lakh(df["Price_in_Lakhs"].median()), f"Mean {lakh(df['Price_in_Lakhs'].mean())}", C["green"]),
    ("Median price per sq ft", rupee(df["Price_per_SqFt_Rs"].median()), f"Mean {rupee(df['Price_per_SqFt_Rs'].mean())}", C["amber"]),
    ("Median size", f"{df['Size_in_SqFt'].median():,.0f} sq ft", f"{df['Size_in_SqFt'].min():,} to {df['Size_in_SqFt'].max():,} sq ft", C["violet"]),
    ("Ready to move", f"{ready:.1%}", f"{1 - ready:.1%} under construction", C["coral"]),
])

# ---------------------------------------------------------------- distributions
section("Price and price per sq ft", "Listing price is spread evenly. Price per sq ft is not, because it is price divided by size.")
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Listing price", "Number of listings in each price band, in lakhs.")
    with box:
        show(histogram(df["Price_in_Lakhs"], bins=40, color=C["blue"], mean=df["Price_in_Lakhs"].mean(),
                       median=df["Price_in_Lakhs"].median(), x_title="Price (lakhs)", fmt=",.0f"), key="ov_price")
with c2:
    box = card("Price per sq ft", "Log scale on the horizontal axis. A long tail of small, expensive listings pulls the mean above the median.")
    with box:
        show(histogram(df["Price_per_SqFt_Rs"], bins=45, color=C["violet"], log=True, mean=df["Price_per_SqFt_Rs"].mean(),
                       median=df["Price_per_SqFt_Rs"].median(), x_title="Rs per sq ft (log scale)", fmt=",.0f",
                       tick_vals=[500, 1000, 2000, 5000, 10000, 20000, 50000, 100000],
                       tick_text=["500", "1K", "2K", "5K", "10K", "20K", "50K", "100K"]), key="ov_ppsf")

# ---------------------------------------------------------------- size relationship
r = df["Size_in_SqFt"].corr(df["Price_in_Lakhs"]) if n > 2 else float("nan")
section("Size and price", "The most important relationship to check before judging value.")
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Size against price", f"Colour shows how many listings fall in each cell. Correlation between size and price: {r:+.3f}.")
    with box:
        show(density_heatmap(df["Size_in_SqFt"], df["Price_in_Lakhs"], x_title="Size (sq ft)", y_title="Price (lakhs)"), key="ov_density")
with c2:
    box = card("Same listings, two views by size band", "Median price stays flat as size grows, so median price per sq ft falls.")
    with box:
        bands = df.groupby("Size_Category", observed=True).agg(price=("Price_in_Lakhs", "median"), ppsf=("Price_per_SqFt_Rs", "median"), n=("ID", "size"))
        bands = bands.reindex([b for b in SIZE_ORDER if b in bands.index])
        fig = make_subplots(rows=1, cols=2, subplot_titles=["Median price (lakhs)", "Median price per sq ft (Rs)"], horizontal_spacing=0.12)
        for i, (col, color, fmt) in enumerate([("price", C["blue"], ",.0f"), ("ppsf", C["violet"], ",.0f")], start=1):
            fig.add_trace(go.Bar(
                x=bands.index.astype(str), y=bands[col], marker=dict(color=color, cornerradius=3),
                text=[f"{v:{fmt}}" for v in bands[col]], textposition="inside", insidetextanchor="end", textfont=dict(color="#0B1220", size=11),
                customdata=np.column_stack([bands["n"]]),
                hovertemplate="<b>%{x} sq ft</b><br>Median: %{y:,.0f}<br>Listings: %{customdata[0]:,}<extra></extra>", showlegend=False),
                row=1, col=i)
            fig.update_yaxes(rangemode="tozero", tickformat=",", row=1, col=i)
            fig.update_xaxes(tickangle=-25, showgrid=False, tickfont=dict(size=10), row=1, col=i)
        for a in fig.layout.annotations:
            a.font = dict(size=12, color=C["muted"])
        show(style(fig, 340, t=28), key="ov_bands")

# ---------------------------------------------------------------- takeaway
if len(bands) >= 2:
    small, large = bands.iloc[0], bands.iloc[-1]
    drop = f"Median price per sq ft is {rupee(small['ppsf'])} for the smallest size band in view and {rupee(large['ppsf'])} for the largest."
else:
    drop = "Select a wider size range to compare size bands."
callout(
    f"<b>Takeaway.</b> Listing prices are spread evenly across the range, with no sign that bigger properties cost more "
    f"(correlation {r:+.3f}). {drop} That fall is arithmetic, not a market effect: a similar price spread over more area. "
    "Any value ranking on raw price per sq ft will therefore favour large properties, which is why the Value screener compares each listing "
    "with peers of similar size in the same city."
)
