"""Real Estate Investment Advisor: entry point.

Run with:  streamlit run app.py
Draws the shared sidebar filters once, then hands off to the selected page.
"""
from pathlib import Path

import streamlit as st

from utils.data import AVAILABILITY, DEFAULT_FILTERS, PROPERTY_TYPES, filter_key, load_data, view_for
from utils.theme import inject_css

ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Real Estate Investment Advisor",
    page_icon=str(ROOT / "assets" / "favicon.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
st.logo(str(ROOT / "assets" / "logo.svg"), icon_image=str(ROOT / "assets" / "icon.svg"), size="large")

pg = st.navigation(
    [
        st.Page("pages/overview.py", title="Market overview", icon=":material/space_dashboard:", default=True),
        st.Page("pages/location.py", title="Location", icon=":material/location_on:"),
        st.Page("pages/features.py", title="Features and amenities", icon=":material/tune:"),
        st.Page("pages/screener.py", title="Value screener", icon=":material/search_insights:"),
        st.Page("pages/insights.py", title="Insights and limitations", icon=":material/fact_check:"),
    ]
)

df = load_data()
for k, v in DEFAULT_FILTERS.items():
    st.session_state.setdefault(k, v)


@st.cache_resource(show_spinner=False)
def cities_by_state() -> dict:
    return {s: sorted(g["City"].unique().tolist()) for s, g in df.groupby("State", observed=True)}


# keep the city list consistent with the selected states
cmap = cities_by_state()
states_sel = st.session_state["f_state"]
city_options = sorted({c for s in (states_sel or cmap.keys()) for c in cmap[s]})
st.session_state["f_city"] = [c for c in st.session_state["f_city"] if c in city_options]


def reset_filters() -> None:
    for k, v in DEFAULT_FILTERS.items():
        st.session_state[k] = v


with st.sidebar:
    st.markdown('<div class="sb-head">Filters</div>', unsafe_allow_html=True)
    st.multiselect("State", sorted(cmap), key="f_state", placeholder="All states")
    st.multiselect("City", city_options, key="f_city", placeholder="All cities")
    st.multiselect("Property type", PROPERTY_TYPES, key="f_type", placeholder="All types")
    st.multiselect("BHK", [1, 2, 3, 4, 5], key="f_bhk", placeholder="All", format_func=lambda b: f"{b} BHK")
    st.multiselect("Availability", AVAILABILITY, key="f_avail", placeholder="All", format_func=lambda a: a.replace("_", " "))
    st.slider("Price (lakhs)", 10.0, 500.0, step=5.0, key="f_price")
    st.slider("Size (sq ft)", 500, 5000, step=50, key="f_size")

key = filter_key(st.session_state)
st.session_state["fkey"] = key
view = view_for(key)

with st.sidebar:
    st.markdown(
        f'<div class="sb-count"><b>{len(view):,}</b> of {len(df):,} listings in view</div>',
        unsafe_allow_html=True,
    )
    st.button("Reset filters", on_click=reset_filters, width="stretch")
    st.download_button(
        "Download filtered data",
        data=lambda: view.drop(columns=["Value_Index"]).to_csv(index=False).encode("utf-8"),
        file_name="housing_filtered.csv",
        mime="text/csv",
        width="stretch",
    )
    st.markdown(
        '<div class="sb-note">Filters apply to every page except Insights and limitations, '
        "which always reads the full dataset so its conclusions do not shift with a filter.</div>",
        unsafe_allow_html=True,
    )

if view.empty:
    st.warning("No listings match the current filters. Widen the ranges or reset the filters in the sidebar.")
    st.stop()

pg.run()
