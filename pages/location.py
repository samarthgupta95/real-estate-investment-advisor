"""Page 2: Location. State and city comparisons for price and price per sq ft."""
import streamlit as st

from utils.charts import bar_ci, deviation_chart, show
from utils.data import get_full, get_view, lakh, rupee
from utils.stats import anova, group_stats, p_text, verdict
from utils.theme import C, callout, card, kpi_row, page_header, section, signal_chips

df = get_view()
n, total = len(df), len(get_full())

page_header(
    "Location",
    "Whether where a property sits changes what it costs, by state and by city.",
    n,
    total,
)

# ---------------------------------------------------------------- statistics
gs_state_pps = group_stats(df, "State", "Price_per_SqFt_Rs")
gs_state_price = group_stats(df, "State", "Price_in_Lakhs")
gs_city_price = group_stats(df, "City", "Price_in_Lakhs")
t_state = anova(df, "State", "Price_per_SqFt_Rs", log=True)
t_city = anova(df, "City", "Price_in_Lakhs")
v_state, tone_state = verdict(t_state, gs_state_pps)
v_city, tone_city = verdict(t_city, gs_city_price)

def gap(gs):
    if len(gs) < 2:
        return None, "", ""
    hi, lo = gs.loc[gs["mean"].idxmax()], gs.loc[gs["mean"].idxmin()]
    return hi["mean"] / lo["mean"] - 1, hi["group"], lo["group"]

g_state, hi_s, lo_s = gap(gs_state_pps)
g_city, hi_c, lo_c = gap(gs_city_price)

kpi_row([
    ("States in view", f"{df['State'].nunique()}", f"{n:,} listings", C["blue"]),
    ("Cities in view", f"{df['City'].nunique()}", "Cities nest inside states", C["violet"]),
    ("State gap, price per sq ft", f"{g_state:.1%}" if g_state is not None else "n/a", f"{hi_s} vs {lo_s}" if g_state is not None else "Need two states", C["amber"]),
    ("City gap, average price", f"{g_city:.1%}" if g_city is not None else "n/a", f"{hi_c} vs {lo_c}" if g_city is not None else "Need two cities", C["green"]),
])

signal_chips(
    [
        ("State and price per sq ft", v_state, tone_state, f"{p_text(t_state['p'])}. State explains {t_state['eta2'] * 100:.3f}% of the variation." if t_state["k"] > 1 else "Only one state in view."),
        ("City and price", v_city, tone_city, f"{p_text(t_city['p'])}. City explains {t_city['eta2'] * 100:.3f}% of the variation." if t_city["k"] > 1 else "Only one city in view."),
    ],
    "Signal check. A real difference needs a significant overall test and at least one group that still stands out after correcting for the number of groups compared.",
)

# ---------------------------------------------------------------- state bars
section("By state", "Bars start at zero so the size of each gap is shown honestly. Whiskers are 95% confidence intervals.")
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Average price per sq ft", "Rupees per sq ft, highest state first. Dashed line is the average across all listings in view.")
    with box:
        g = gs_state_pps.sort_values("mean", ascending=False)
        show(bar_ci(g, df["Price_per_SqFt_Rs"].mean(), "Rs per sq ft", color=C["violet"], prefix="Rs "), key="loc_state_pps")
with c2:
    box = card("Average listing price", "Lakhs, highest state first. Same ordering rule, same zero-based scale.")
    with box:
        g = gs_state_price.sort_values("mean", ascending=False)
        show(bar_ci(g, df["Price_in_Lakhs"].mean(), "Price (lakhs)", fmt=",.1f", color=C["blue"], suffix=" L"), key="loc_state_price")

# ---------------------------------------------------------------- explorer
section("Explorer", "Pick a level and a measure. Each dot compares one place with every other listing, zoomed in on the gap itself.")
box = card("Difference from all other listings", "Amber dots survive correction for the number of places compared. Grey dots are within normal variation.")
with box:
    a, b = st.columns(2, gap="small")
    level = a.selectbox("Compare by", ["State", "City"], key="loc_level")
    metric_name = b.selectbox("Measure", ["Price per sq ft", "Listing price"], key="loc_metric")
    metric = "Price_per_SqFt_Rs" if metric_name == "Price per sq ft" else "Price_in_Lakhs"
    gs = group_stats(df, level, metric).sort_values("diff_pct", ascending=False)
    t = anova(df, level, metric, log=(metric == "Price_per_SqFt_Rs"))
    label, _ = verdict(t, gs)
    show(deviation_chart(gs), key="loc_dev")
    if t["k"] > 1:
        st.caption(f"{metric_name} by {level.lower()}: {label.lower()} ({p_text(t['p'])}). Largest gap is {gs['diff_pct'].abs().max():.2f}% from the rest of the listings.")

with st.expander("City summary table"):
    tbl = (df.groupby(["City", "State"], observed=True)
             .agg(listings=("ID", "size"), avg_price=("Price_in_Lakhs", "mean"), avg_ppsf=("Price_per_SqFt_Rs", "mean"))
             .reset_index().sort_values("avg_price", ascending=False))
    tbl["vs_all"] = (tbl["avg_price"] / df["Price_in_Lakhs"].mean() - 1) * 100
    st.dataframe(
        tbl, hide_index=True, width="stretch",
        column_config={
            "City": "City", "State": "State",
            "listings": st.column_config.NumberColumn("Listings", format="%d"),
            "avg_price": st.column_config.NumberColumn("Average price (lakhs)", format="%.1f"),
            "avg_ppsf": st.column_config.NumberColumn("Average price per sq ft (Rs)", format="%d"),
            "vs_all": st.column_config.NumberColumn("Price vs all listings", format="%+.1f%%"),
        },
    )

# ---------------------------------------------------------------- takeaway
if v_state == "Within normal variation" and v_city == "Within normal variation":
    msg = (f"Location does not separate prices here. The highest and lowest state differ by {g_state:.1%} in price per sq ft and the highest and lowest "
           f"city by {g_city:.1%} in average price, and neither gap is distinguishable from chance." if g_state is not None and g_city is not None
           else "Location does not separate prices in the current view.")
    msg += " A ranking of cities or states from this data would be noise, so it should not drive an investment decision."
else:
    msg = f"State reads as <b>{v_state.lower()}</b> and city as <b>{v_city.lower()}</b>. Check the amber dots above to see where."
callout(f"<b>Takeaway.</b> {msg}")
