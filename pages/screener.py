"""Page 4: Value screener. Listings priced below comparable peers, with optional feature requirements."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from utils.charts import histogram, show, style
from utils.data import get_full, get_view, lakh, rupee
from utils.theme import C, callout, card, kpi_row, page_header, section

df = get_view()
n, total = len(df), len(get_full())

page_header(
    "Value screener",
    "Listings priced below comparable listings: same city and similar size. A shortlist for closer inspection, not a forecast of returns.",
    n,
    total,
)

# ---------------------------------------------------------------- criteria
box = card("Screening criteria", "The value index is a listing's price per sq ft divided by the median for its city and 300 sq ft size band. 0.80 means 20% cheaper than comparable listings.")
with box:
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    disc = c1.slider("Minimum discount to peers (%)", 0, 90, 75, step=5, key="sc_disc")
    min_am = c2.slider("Minimum amenities", 1, 5, 1, key="sc_am")
    trans = c3.selectbox("Public transport access", ["Any", "Medium or better", "High only"], key="sc_tr")
    parking = c4.toggle("Parking space required", key="sc_park")

threshold = 1 - disc / 100
mask = df["Value_Index"] <= threshold
mask &= df["Amenity_Count"] >= min_am
mask &= df["Transport_Score"] >= {"Any": 1, "Medium or better": 2, "High only": 3}[trans]
if parking:
    mask &= df["Parking_Flag"] == 1
hits = df[mask]

if hits.empty:
    st.info("No listings meet these criteria. Lower the minimum discount or relax a requirement.")
    st.stop()

kpi_row([
    ("Listings matching", f"{len(hits):,}", f"{len(hits) / n:.1%} of listings in view", C["blue"]),
    ("Median discount to peers", f"{(1 - hits['Value_Index'].median()) * 100:.1f}%", "Price per sq ft vs comparable listings", C["green"]),
    ("Median price", lakh(hits["Price_in_Lakhs"].median()), f"All listings in view: {lakh(df['Price_in_Lakhs'].median())}", C["amber"]),
    ("Median size", f"{hits['Size_in_SqFt'].median():,.0f} sq ft", f"All listings in view: {df['Size_in_SqFt'].median():,.0f}", C["violet"]),
    ("Ready to move", f"{(hits['Availability_Status'] == 'Ready_to_Move').mean():.1%}", f"All listings in view: {(df['Availability_Status'] == 'Ready_to_Move').mean():.1%}", C["coral"]),
])

# ---------------------------------------------------------------- charts
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Value index across listings in view", "Shaded area is what the current discount setting selects, before the other requirements.")
    with box:
        fig = histogram(df["Value_Index"], bins=40, color=C["slate"], x_title="Value index (1.0 = similar peers)", fmt=".2f")
        fig.add_vrect(x0=float(df["Value_Index"].min()), x1=threshold, fillcolor=C["green"], opacity=0.18, line_width=0)
        fig.add_vline(x=threshold, line_dash="dash", line_color=C["green"], line_width=1.6)
        show(fig, key="sc_hist")
with c2:
    box = card("Where the matches sit", "Price against size for a random sample of listings. Matches are spread across sizes because they are compared with similar-sized peers.")
    with box:
        rng = np.random.default_rng(5)
        rest = df[~mask]
        rest_s = rest.iloc[rng.choice(len(rest), size=min(3500, len(rest)), replace=False)] if len(rest) else rest
        hit_s = hits.iloc[rng.choice(len(hits), size=min(1800, len(hits)), replace=False)]
        fig = go.Figure()
        fig.add_trace(go.Scattergl(x=rest_s["Size_in_SqFt"], y=rest_s["Price_in_Lakhs"], mode="markers", name="Other listings",
                                   marker=dict(size=4, color=C["slate"], opacity=0.35), hovertemplate="%{x:,.0f} sq ft, %{y:,.0f} L<extra></extra>"))
        fig.add_trace(go.Scattergl(x=hit_s["Size_in_SqFt"], y=hit_s["Price_in_Lakhs"], mode="markers", name="Matches",
                                   marker=dict(size=5, color=C["green"], opacity=0.8), hovertemplate="%{x:,.0f} sq ft, %{y:,.0f} L<extra></extra>"))
        fig.update_xaxes(title="Size (sq ft)", tickformat=",")
        fig.update_yaxes(title="Price (lakhs)", tickformat=",")
        show(style(fig, 330, legend=True, t=28), key="sc_scatter")

# ---------------------------------------------------------------- table
section("Shortlist", "The 100 most discounted matches. Click a column header to sort, or download every match.")
top = hits.nsmallest(100, "Value_Index").copy()
top["below_peers"] = (1 - top["Value_Index"]) * 100
cols = ["ID", "City", "State", "Property_Type", "BHK", "Size_in_SqFt", "Price_in_Lakhs", "Price_per_SqFt_Rs", "below_peers",
        "Availability_Status", "Public_Transport_Accessibility", "Amenity_Count", "Parking_Space"]
st.dataframe(
    top[cols].astype({"City": str, "State": str, "Property_Type": str, "Availability_Status": str, "Public_Transport_Accessibility": str, "Parking_Space": str}),
    hide_index=True, width="stretch", height=420,
    column_config={
        "ID": st.column_config.NumberColumn("ID", format="%d"),
        "Property_Type": "Type",
        "BHK": st.column_config.NumberColumn("BHK", format="%d"),
        "Size_in_SqFt": st.column_config.NumberColumn("Size (sq ft)", format="%d"),
        "Price_in_Lakhs": st.column_config.NumberColumn("Price (lakhs)", format="%.1f"),
        "Price_per_SqFt_Rs": st.column_config.NumberColumn("Price per sq ft (Rs)", format="%d"),
        "below_peers": st.column_config.NumberColumn("Below peers", format="%.1f%%"),
        "Availability_Status": "Availability",
        "Public_Transport_Accessibility": "Transport",
        "Amenity_Count": st.column_config.NumberColumn("Amenities", format="%d"),
        "Parking_Space": "Parking",
    },
)
st.download_button(
    "Download all matches (CSV)",
    data=lambda: hits.drop(columns=["Value_Index"]).assign(Discount_to_Peers_Pct=((1 - hits["Value_Index"]) * 100).round(1)).to_csv(index=False).encode("utf-8"),
    file_name="value_screener_matches.csv", mime="text/csv",
)

# ---------------------------------------------------------------- takeaway
raw = df.nsmallest(len(hits), "Price_per_SqFt_Rs")
big_hits = (hits["Size_Category"] == "3,500+").mean()
big_raw = (raw["Size_Category"] == "3,500+").mean()
callout(
    f"<b>Why peers instead of raw price per sq ft.</b> Ranking the {len(hits):,} cheapest listings on raw price per sq ft would pick "
    f"{big_raw:.0%} from the largest size band (3,500+ sq ft), against {big_hits:.0%} here, because big properties are cheap per sq ft by arithmetic. "
    "Comparing each listing with same-city, similar-size listings removes most of that bias. "
    "<b>Keep in mind:</b> a low value index means cheap for what it is, not a better investment. Prices within a city and size band vary very widely in this data, "
    "which is why deep discounts are common. The data has no rents, no listing dates and no price history, so it cannot show returns.",
    "warn",
)
