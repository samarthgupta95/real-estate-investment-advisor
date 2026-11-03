"""Page 3: Features and amenities. Correlations, amenity effects and a feature explorer."""
import numpy as np
import pandas as pd
import streamlit as st

from utils.charts import correlation_heatmap, deviation_chart, show
from utils.data import AGE_ORDER, AVAILABILITY, FURNISHED_ORDER, PROPERTY_TYPES, TRANSPORT_ORDER, get_full, get_key, get_view, view_for
from utils.stats import anova, flag_effects, group_stats, p_text, verdict
from utils.theme import C, callout, card, kpi_row, page_header, section, signal_chips

df = get_view()
n, total = len(df), len(get_full())

page_header(
    "Features and amenities",
    "Whether furnishing, amenities, transport access and other listing features change price, price per sq ft or relative value.",
    n,
    total,
)

NUM_LABELS = {
    "Price_in_Lakhs": "Price", "Size_in_SqFt": "Size", "Price_per_SqFt_Rs": "Price per sq ft", "BHK": "BHK",
    "Age_of_Property": "Age", "Nearby_Schools": "Schools", "Nearby_Hospitals": "Hospitals", "Amenity_Count": "Amenities",
    "Transport_Score": "Transport", "Parking_Flag": "Parking", "Security_Flag": "Security",
}
FEATURES = {
    "Furnished status": ("Furnished_Status", FURNISHED_ORDER),
    "Property type": ("Property_Type", PROPERTY_TYPES),
    "Facing direction": ("Facing", ["East", "North", "South", "West"]),
    "Owner type": ("Owner_Type", ["Builder", "Broker", "Owner"]),
    "Availability": ("Availability_Status", AVAILABILITY),
    "Public transport access": ("Public_Transport_Accessibility", TRANSPORT_ORDER),
    "Parking space": ("Parking_Space", ["No", "Yes"]),
    "Security": ("Security", ["No", "Yes"]),
    "Number of amenities": ("Amenity_Count", [str(i) for i in range(1, 6)]),
    "BHK": ("BHK", [str(i) for i in range(1, 6)]),
    "Nearby schools": ("Nearby_Schools", [str(i) for i in range(1, 11)]),
    "Nearby hospitals": ("Nearby_Hospitals", [str(i) for i in range(1, 11)]),
    "Property age": ("Age_Group", AGE_ORDER),
}
OUTCOMES = {
    "Listing price (lakhs)": ("Price_in_Lakhs", False),
    "Price per sq ft (Rs)": ("Price_per_SqFt_Rs", True),
    "Value index (1.0 = similar peers)": ("Value_Index", False),
}


@st.cache_data(show_spinner=False, max_entries=24)
def spearman(key, cols: tuple) -> pd.DataFrame:
    d = view_for(key)
    if len(d) > 60_000:
        d = d.sample(60_000, random_state=11)
    return d[list(cols)].corr(method="spearman")


def check(col: str, value: str, log: bool, name: str):
    gs = group_stats(df, col, value)
    t = anova(df, col, value, log=log)
    label, tone = verdict(t, gs)
    detail = f"{p_text(t['p'])}. Explains {t['eta2'] * 100:.3f}% of the variation." if t["k"] > 1 else "Only one group in view."
    return name, label, tone, detail


# ---------------------------------------------------------------- numbers for KPIs and chips
corr = spearman(get_key(), tuple(NUM_LABELS)) if n > 30 else None
FLAGS = {"Gym": "Has_Gym", "Pool": "Has_Pool", "Garden": "Has_Garden", "Clubhouse": "Has_Clubhouse", "Playground": "Has_Playground",
         "Parking": "Parking_Flag", "Security": "Security_Flag"}
eff = flag_effects(df, FLAGS, "Price_per_SqFt_Rs")

if corr is not None:
    s = corr["Price_in_Lakhs"].drop(["Price_in_Lakhs", "Price_per_SqFt_Rs"]).abs()
    top_name, top_val = NUM_LABELS[s.idxmax()], float(corr["Price_in_Lakhs"][s.idxmax()])
else:
    top_name, top_val = "n/a", float("nan")
big_eff = float(eff["diff_pct"].abs().max()) if len(eff) else float("nan")

kpi_row([
    ("Features tested", f"{len(FEATURES)}", "Against price, price per sq ft and value index", C["blue"]),
    ("Strongest link to price", f"{top_val:+.3f}" if not np.isnan(top_val) else "n/a", f"{top_name} (Spearman correlation)", C["amber"]),
    ("Largest amenity effect", f"{big_eff:.2f}%" if not np.isnan(big_eff) else "n/a", "Change in price per sq ft", C["green"]),
])

chips = [
    check("Furnished_Status", "Price_in_Lakhs", False, "Furnishing and price"),
    check("Public_Transport_Accessibility", "Price_per_SqFt_Rs", True, "Transport and price per sq ft"),
    check("Amenity_Count", "Price_per_SqFt_Rs", True, "Amenity count and price per sq ft"),
    check("Parking_Space", "Price_in_Lakhs", False, "Parking and price"),
]
signal_chips(
    chips,
    "Signal check. A real difference needs a significant overall test and at least one group that still stands out after correcting for the number of groups compared.",
)

# ---------------------------------------------------------------- heatmap and amenities
c1, c2 = st.columns([1.15, 1], gap="medium")
with c1:
    box = card("How the numeric features move together", "Spearman correlation, computed on a random sample of up to 60,000 listings. Only price per sq ft against price and size stands out, and that is by construction.")
    with box:
        if corr is None:
            st.info("Widen the filters to compute correlations.")
        else:
            show(correlation_heatmap(corr, NUM_LABELS), key="ft_corr")
with c2:
    box = card("Amenities and facilities against price per sq ft", "Listings with each feature compared with listings without it. Amber would mean a real difference.")
    with box:
        if eff.empty:
            st.info("Not enough listings in view.")
        else:
            show(deviation_chart(eff.sort_values("diff_pct", ascending=False), x_title="Difference in price per sq ft (%)", height=420), key="ft_amen")

# ---------------------------------------------------------------- explorer
section("Feature explorer", "Pick a feature and an outcome. The table gives the same comparison in numbers.")
box = card("Difference from all other listings")
with box:
    a, b = st.columns(2, gap="small")
    feat = a.selectbox("Feature", list(FEATURES), index=5, key="ft_feat")
    out = b.selectbox("Outcome", list(OUTCOMES), index=1, key="ft_out")
    col, order = FEATURES[feat]
    value, use_log = OUTCOMES[out]
    gs = group_stats(df, col, value)
    gs = gs.set_index("group").reindex([o for o in order if o in set(gs["group"])]).reset_index()
    t = anova(df, col, value, log=use_log)
    label, _ = verdict(t, gs)
    left, right = st.columns([1.3, 1], gap="medium")
    with left:
        show(deviation_chart(gs, height=max(240, 38 * len(gs) + 90)), key="ft_dev")
    with right:
        tbl = gs[["group", "n", "mean", "diff_pct", "p_adj"]].copy()
        st.dataframe(
            tbl, hide_index=True, width="stretch",
            column_config={
                "group": feat, "n": st.column_config.NumberColumn("Listings", format="%d"),
                "mean": st.column_config.NumberColumn("Average", format="%.2f"),
                "diff_pct": st.column_config.NumberColumn("Vs others", format="%+.2f%%"),
                "p_adj": st.column_config.NumberColumn("Adjusted p", format="%.3f"),
            },
        )
    if t["k"] > 1:
        st.caption(f"{feat} and {out.lower()}: {label.lower()} ({p_text(t['p'])}). Explains {t['eta2'] * 100:.3f}% of the variation.")

# ---------------------------------------------------------------- takeaway
if any(c[2] == "good" for c in chips):
    callout("<b>Takeaway.</b> At least one feature shows a real difference in the current view. Check the amber dots above and the explorer below to see which one, "
            "and confirm it holds on the full dataset before relying on it.")
else:
    callout(
        "<b>Takeaway.</b> Furnishing, amenities, parking, transport access and the other listing features show no price premium in the current view, "
        "and each explains a tiny fraction of the variation in price. In practical terms the market in this dataset charges nothing extra for them, "
        "so two listings at the same price are better compared on what they include than on what they cost. "
        "That is a statement about this dataset, not a rule for the Indian housing market."
    )
