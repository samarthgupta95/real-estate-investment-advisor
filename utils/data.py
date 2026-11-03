"""Data loading, shared filters and number formatting."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "housing_clean.csv.gz"

PROPERTY_TYPES = ["Apartment", "Independent House", "Villa"]
AVAILABILITY = ["Ready_to_Move", "Under_Construction"]
SIZE_ORDER = ["Up to 1,500", "1,500-2,500", "2,500-3,500", "3,500+"]
AGE_ORDER = ["0-10 yrs", "11-20 yrs", "21-30 yrs", "31-35 yrs"]
TRANSPORT_ORDER = ["Low", "Medium", "High"]
FURNISHED_ORDER = ["Unfurnished", "Semi-furnished", "Furnished"]
AMENITIES = ["Clubhouse", "Garden", "Gym", "Playground", "Pool"]

DEFAULT_FILTERS = {
    "f_state": [],
    "f_city": [],
    "f_type": [],
    "f_bhk": [],
    "f_avail": [],
    "f_price": (10.0, 500.0),
    "f_size": (500, 5000),
}

# bands of 300 sq ft used to compare a listing with similar-sized peers
SIZE_BAND_WIDTH = 300


@st.cache_resource(show_spinner="Loading listings")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    for col in ["State", "City", "Locality", "Property_Type", "Furnished_Status", "Public_Transport_Accessibility",
                "Parking_Space", "Security", "Facing", "Owner_Type", "Availability_Status"]:
        df[col] = df[col].astype("category")
    df["Age_Group"] = pd.Categorical(df["Age_Group"], categories=AGE_ORDER, ordered=True)
    df["Size_Category"] = pd.Categorical(df["Size_Category"], categories=SIZE_ORDER, ordered=True)
    df["Price_Segment"] = pd.Categorical(df["Price_Segment"], categories=["Budget", "Mid-range", "Premium"], ordered=True)

    # Value index: price per sq ft relative to the median of the same city and the same 300 sq ft size band.
    # Below 1.0 means cheaper than comparable listings; 0.80 means 20% cheaper.
    band = ((df["Size_in_SqFt"] - 500) // SIZE_BAND_WIDTH).astype(int)
    peer_median = df.groupby([df["City"], band], observed=True)["Price_per_SqFt_Rs"].transform("median")
    df["Value_Index"] = (df["Price_per_SqFt_Rs"] / peer_median).round(4)
    return df


def filter_key(ss) -> tuple:
    return (
        tuple(sorted(ss["f_state"])),
        tuple(sorted(ss["f_city"])),
        tuple(sorted(ss["f_type"])),
        tuple(sorted(ss["f_bhk"])),
        tuple(sorted(ss["f_avail"])),
        tuple(ss["f_price"]),
        tuple(ss["f_size"]),
    )


@st.cache_resource(max_entries=32, show_spinner=False)
def view_for(key: tuple | None) -> pd.DataFrame:
    df = load_data()
    if key is None:
        return df
    states, cities, types, bhks, avail, price, size = key
    mask = pd.Series(True, index=df.index)
    if states:
        mask &= df["State"].isin(states)
    if cities:
        mask &= df["City"].isin(cities)
    if types:
        mask &= df["Property_Type"].isin(types)
    if bhks:
        mask &= df["BHK"].isin(bhks)
    if avail:
        mask &= df["Availability_Status"].isin(avail)
    mask &= df["Price_in_Lakhs"].between(price[0], price[1])
    mask &= df["Size_in_SqFt"].between(size[0], size[1])
    return df if mask.all() else df[mask]


def get_key():
    return st.session_state.get("fkey")


def get_view() -> pd.DataFrame:
    return view_for(get_key())


def get_full() -> pd.DataFrame:
    return load_data()


# ------------------------------------------------------------------ formatting
def lakh(v: float, d: int = 1) -> str:
    return f"Rs {v:,.{d}f} L"


def rupee(v: float) -> str:
    return f"Rs {v:,.0f}"


def sqft(v: float) -> str:
    return f"{v:,.0f} sq ft"


def pct(v: float, d: int = 1) -> str:
    return f"{v:.{d}f}%"
