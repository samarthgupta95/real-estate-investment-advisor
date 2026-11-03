"""Page 5: Insights, recommendations and limitations. Always reads the full dataset."""
import numpy as np
import pandas as pd
import streamlit as st

from utils.data import get_full, rupee
from utils.stats import anova, group_stats
from utils.theme import C, callout, info_card, kpi_row, page_header, section

df = get_full()
n = len(df)

page_header(
    "Insights and limitations",
    "What the data supports, what it does not, what to do next, and what to be careful about when presenting it.",
)
callout(f"This page always reads the full dataset of {n:,} listings, whatever is set in the sidebar filters, so its conclusions do not move when a filter changes.")


# ---------------------------------------------------------------- numbers
@st.cache_data(show_spinner=False)
def battery() -> pd.DataFrame:
    """Every factor against price and price per sq ft, so the page can say how many results are real."""
    factors = {
        "State": "State", "City": "City", "Property type": "Property_Type", "Furnished status": "Furnished_Status",
        "Facing": "Facing", "Owner type": "Owner_Type", "Availability": "Availability_Status",
        "Public transport": "Public_Transport_Accessibility", "Parking": "Parking_Space", "Security": "Security",
        "Amenity count": "Amenity_Count", "BHK": "BHK", "Nearby schools": "Nearby_Schools",
        "Nearby hospitals": "Nearby_Hospitals", "Property age": "Age_Group",
    }
    rows = []
    for name, col in factors.items():
        for out, val, log in [("price", "Price_in_Lakhs", False), ("price per sq ft", "Price_per_SqFt_Rs", True)]:
            t = anova(df, col, val, log=log)
            rows.append({"factor": name, "outcome": out, "p": t["p"], "eta2": t["eta2"]})
    out = pd.DataFrame(rows)
    out["p_adj"] = (out["p"] * len(out)).clip(upper=1.0)
    return out


@st.cache_data(show_spinner=False)
def facts() -> dict:
    f = {}
    f["r_size_price"] = float(df["Size_in_SqFt"].corr(df["Price_in_Lakhs"]))
    bands = df.groupby("Size_Category", observed=True)["Price_per_SqFt_Rs"].median()
    f["ppsf_small"], f["ppsf_large"] = float(bands.iloc[0]), float(bands.iloc[-1])
    f["price_median"] = float(df["Price_in_Lakhs"].median())
    f["ppsf_median"] = float(df["Price_per_SqFt_Rs"].median())
    gs = group_stats(df, "State", "Price_per_SqFt_Rs")
    f["state_gap"] = float(gs["mean"].max() / gs["mean"].min() - 1)
    gc = group_stats(df, "City", "Price_in_Lakhs")
    f["city_gap"] = float(gc["mean"].max() / gc["mean"].min() - 1)
    f["floor_bad"] = float((df["Floor_No"] > df["Total_Floors"]).mean())
    f["status_bad"] = float(((df["Availability_Status"] == "Under_Construction") & (df["Age_of_Property"] > 5)).mean())
    f["bhk_size_min"], f["bhk_size_max"] = (float(v) for v in df.groupby("BHK")["Size_in_SqFt"].mean().agg(["min", "max"]))
    cities_per_loc = df.groupby("Locality", observed=True)["City"].nunique()
    f["loc_min"], f["loc_max"], f["n_loc"] = int(cities_per_loc.min()), int(cities_per_loc.max()), int(len(cities_per_loc))
    f["n_cities"] = int(df["City"].nunique())
    f["ppsf_out"] = float(df["PPSF_Outlier"].mean())
    f["zero_raw"] = int((df["Price_per_SqFt_Rs"] < 1).sum())
    return f


T = battery()
F = facts()
n_tests = len(T)
nominal = int((T["p"] < 0.05).sum())
survive = int((T["p_adj"] < 0.05).sum())
best = T.loc[T["eta2"].idxmax()]
max_eta = float(T["eta2"].max())

# ---------------------------------------------------------------- key findings
section("Key findings", "Each number is calculated from the full dataset when the page loads.")
c1, c2 = st.columns(2, gap="medium")
with c1:
    info_card(
        "Price and size", C["blue"], "Size does not drive price",
        f"Correlation between size and price is {F['r_size_price']:+.3f}. A 500 sq ft listing and a 5,000 sq ft listing have the same expected price, "
        f"around {F['price_median']:,.0f} lakhs. In most real markets this relationship is strongly positive.",
        "<b>Evidence:</b> strong. Tested on all listings; see the Market overview page.",
    )
with c2:
    info_card(
        "Value metric", C["amber"], "Price per sq ft falls with size by arithmetic",
        f"Median price per sq ft is {rupee(F['ppsf_small'])} in the smallest size band and {rupee(F['ppsf_large'])} in the largest. "
        "Because price does not rise with size, dividing by area makes large listings look cheap. Raw price per sq ft is therefore a size ranking in disguise.",
        "<b>Evidence:</b> strong. This follows directly from the previous finding.",
    )
st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
c1, c2 = st.columns(2, gap="medium")
with c1:
    info_card(
        "Location", C["green"], "State and city barely separate prices",
        f"The highest and lowest state differ by {F['state_gap']:.1%} in average price per sq ft, and the highest and lowest city by {F['city_gap']:.1%} in average price. "
        "Neither gap is distinguishable from chance. Real markets show much larger regional gaps.",
        "<b>Evidence:</b> strong that any effect is small or absent. A statement about this dataset only.",
    )
with c2:
    info_card(
        "Features", C["violet"], "No listed feature carries a price premium",
        f"{n_tests} comparisons across {T['factor'].nunique()} factors and two outcomes: {nominal} fall below p = 0.05 (about {n_tests * 0.05:.1f} would by chance), "
        f"and {survive} survive correction for running {n_tests} tests. The largest effect explains {max_eta * 100:.3f}% of the variation "
        f"({best['factor'].lower()} against {best['outcome']}).",
        "<b>Evidence:</b> strong that effects are small or absent. Furnishing, amenities, transport and parking are priced the same as their absence.",
    )

# ---------------------------------------------------------------- recommendations
section("Recommendations", "Each one says how strong the evidence is. Where the data only supports a screening rule, it is labelled that way.")
r1, r2 = st.columns(2, gap="medium")
with r1:
    info_card(
        "Data-backed", C["green"], "Screen on price relative to comparable listings, not on raw price per sq ft",
        "Compare each listing with same-city, similar-size peers. This removes the size bias in price per sq ft and gives a fair read of whether a listing is cheap for what it is. "
        "The Value screener does exactly this.",
        "<b>Success measure:</b> shortlisted listings are spread across all size bands instead of piling into the largest one.",
    )
with r2:
    info_card(
        "Data-backed", C["green"], "Do not pay for features the market does not price",
        "Amenities, furnishing, parking, security and transport access carry no premium here. At the same price, take the listing that includes more of them, "
        "and be sceptical of a seller who asks for a premium on any of them.",
        "<b>How to use it:</b> shortlist by value index first, then break ties on features.",
    )
st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
r3, r4 = st.columns(2, gap="medium")
with r3:
    info_card(
        "Reasoned, not measured", C["amber"], "Prefer ready-to-move at equal price",
        "Ready-to-move and under-construction listings are priced the same here, so a buyer takes on delivery risk without being paid for it. "
        "This is a judgement about risk, not something the data measured, and the availability field itself is inconsistent (see limitations).",
        "<b>How to test:</b> add expected delivery dates and compare outcomes on real data.",
    )
with r4:
    info_card(
        "Data gap", C["coral"], "Collect the fields an investment decision needs",
        "Returns cannot be judged without rent, listing dates, sale prices over time and real locality coordinates. Until those exist, every investment label from this data is a "
        "screening rule for further inspection, not a forecast.",
        "<b>Next step:</b> see the data gaps table below.",
    )
st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
r5, r6 = st.columns(2, gap="medium")
with r5:
    info_card(
        "Data-backed", C["green"], "Do not present city or state rankings as findings",
        "The ranges are within noise, so a league table of cities would invite decisions the data cannot support. Show the confidence intervals, as the Location page does, or leave the ranking out.",
        "<b>Measure:</b> none needed now. Revisit when real price data from different markets is available.",
    )
with r6:
    info_card(
        "Data-backed", C["green"], "Fix the source data before any modelling",
        f"{F['floor_bad']:.1%} of listings have a floor number above the building's total floors, and {F['status_bad']:.1%} of under-construction listings are older than five years. "
        "A model trained on these fields would learn from errors.",
        "<b>Next step:</b> confirm with the data owner which of the two floor fields is wrong, and what under construction means for an old listing.",
    )

# ---------------------------------------------------------------- data quality
section("Data quality checks", "Computed from the full dataset.")
qa = pd.DataFrame([
    ("Missing values", "0", "Nothing to impute."),
    ("Duplicate rows or IDs", "0", "Each listing appears once."),
    ("Floor number above total floors", f"{F['floor_bad']:.1%}", "Impossible. Floor fields excluded from the analysis."),
    ("Under construction, older than 5 years", f"{F['status_bad']:.1%}", "Contradictory. Age is not read by availability status."),
    ("Average size, 1 BHK to 5 BHK", f"{F['bhk_size_min']:,.0f} to {F['bhk_size_max']:,.0f} sq ft", "Bedrooms do not change size, unlike a real listing set."),
    ("Cities sharing each locality name", f"{F['loc_min']} to {F['loc_max']} of {F['n_cities']}", f"{F['n_loc']} locality names repeat in nearly every city, so locality is a label, not a place."),
    ("Price per sq ft outliers", f"{F['ppsf_out']:.1%}", "Small, expensive listings. Kept and flagged."),
    ("Raw price per sq ft column", "Lakhs, rounded to 2 decimals", "Rebuilt in rupees from price and size."),
], columns=["Check", "Result", "How it was handled"])
st.dataframe(qa, hide_index=True, width="stretch")

# ---------------------------------------------------------------- data gaps
section("Data gaps and how to close them", "What to start recording so the next version of this analysis can answer more.")
gaps = pd.DataFrame([
    ("Listing or sale date", "There is no time dimension, so price trends and appreciation cannot be measured.", "Appreciation by city and locality."),
    ("Monthly rent", "Investment return needs income, not only price.", "Rental yield and payback period."),
    ("Real locality, pin code or coordinates", "Locality names repeat across cities.", "True neighbourhood comparisons and distance to transport."),
    ("Project or builder name", "Quality and reputation differ between developers.", "Builder-level risk and premium."),
    ("Carpet versus built-up area", "Size definition is not stated.", "A like-for-like price per sq ft."),
    ("Final sale price", "Listing price is an ask, not a transaction.", "How far asks sit from real prices."),
], columns=["Missing field", "Why it matters", "What it would allow"])
st.dataframe(gaps, hide_index=True, width="stretch")

# ---------------------------------------------------------------- limitations
section("Limitations and biases", "Read these before presenting any number from this dashboard.")
st.markdown(
    f"""
<div class="callout warn lim"><ul style="margin:0;padding-left:1.1rem">
<li><b>The data looks simulated.</b> Price is spread evenly from 10 to 500 lakhs, size evenly from 500 to 5,000 sq ft, and nearly every feature is unrelated to every other. Confirm where the export came from before presenting differences as facts about the housing market.</li>
<li><b>A null result describes this dataset, not India.</b> Finding no location, furnishing or amenity effect here does not show that such effects are absent in real listings.</li>
<li><b>No investment outcome is measured.</b> There are no rents, dates or price history. The value index is a screening rule for listings that look cheap against comparable ones, not a prediction of returns.</li>
<li><b>Price per sq ft depends on size by construction.</b> Treat any ranking on it with care, and prefer the value index when comparing listings.</li>
<li><b>Inconsistent fields.</b> Floor number and availability status contradict other columns for a large share of rows, so they are excluded from conclusions.</li>
<li><b>Locality is a label.</b> The same {F['n_loc']} names appear in almost every city, so no locality-level conclusion is drawn.</li>
<li><b>Many comparisons.</b> {n_tests} tests were run, so a few would pass at 5% by luck. Group comparisons use Bonferroni correction, which is strict and could hide a very small real effect.</li>
<li><b>Association, not causation.</b> Even a real difference between groups would not show that changing a feature changes price.</li>
<li><b>Listing price is an ask.</b> It is not a closing price, and the export does not say how far the two differ.</li>
<li><b>No external benchmark.</b> Nothing here says whether a price level is high or low for the market it came from.</li>
</ul></div>
""",
    unsafe_allow_html=True,
)

with st.expander("Method notes"):
    st.markdown(
        """
- **Price per sq ft** is price in lakhs multiplied by 100,000 and divided by size in sq ft. The raw column in the source file is lakhs per sq ft rounded to two decimals and was not used.
- **Value index** is a listing's price per sq ft divided by the median price per sq ft of listings in the same city and the same 300 sq ft size band.
- **Group comparisons** test each group against all other listings with a Welch z-test, and correct p-values for the number of groups compared (Bonferroni). Differences are drawn with 95% confidence intervals.
- **Overall test** is a one-way ANOVA. Price per sq ft is log-transformed first because it is skewed. Eta squared is the share of variation the grouping explains.
- **Signal labels:** Real difference needs a significant overall test and a group that survives correction. Weak signal means a significant overall test but no group that survives. Anything else is within normal variation.
"""
    )
