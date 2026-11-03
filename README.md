# Real Estate Investment Advisor

An exploratory analysis and interactive Streamlit dashboard on 250,000 Indian property listings, built to ask a practical question: which listings look like good or bad investments, and what in the data supports that call?

The short version of the answer is honest rather than flattering. In this dataset, nothing about a listing (size, city, state, furnishing, amenities, transport access) explains its price. The project documents that finding properly, builds a size-adjusted value screener on top of it, and is explicit about what the data cannot tell you.

## What is in the repo

| Part | What it does |
|---|---|
| `notebooks/real_estate_eda.ipynb` | Data preprocessing, feature engineering and 8 focused EDA questions, with statistical tests and effect sizes. Writes the clean dataset the dashboard reads. |
| `app.py` and `pages/` | Five-page Streamlit dashboard with shared sidebar filters. |
| `utils/` | Data loading, statistics, chart helpers and theme. |
| `data/` | `housing_clean.csv.gz` (cleaned, used by the app) and `raw/india_housing_prices.csv.gz` (source file, compressed). |

## Dashboard pages

1. **Market overview.** Price and price per sq ft distributions, and why price per sq ft falls with size.
2. **Location.** State and city comparisons with confidence intervals, plus an explorer.
3. **Features and amenities.** Correlation heatmap, amenity effects and a feature explorer.
4. **Value screener.** Listings priced below comparable peers (same city, similar size), with optional requirements for amenities, transport access and parking.
5. **Insights and limitations.** Key findings, recommendations with evidence labels, data quality checks, data gaps and limitations. Always reads the full dataset.

Sidebar filters (state, city, property type, BHK, availability, price, size) apply to pages 1 to 4.

## Key findings

- Price and size are unrelated (correlation about -0.003). Listing price is spread evenly from 10 to 500 lakhs.
- Price per sq ft falls with size purely because it is price divided by size. Ranking on it favours large properties.
- State and city gaps are about 2 to 3% and not statistically distinguishable from chance.
- Furnishing, amenities, parking, security and transport access carry no price premium.
- The dataset looks simulated: flat distributions, near-zero correlations, bedrooms unrelated to size, the same 500 locality names in all 42 cities, and floor numbers above total floors in 46.5% of rows.

Conclusions are about this dataset, not about the Indian housing market.

## The value index

Raw price per sq ft is a poor value measure here because of the size effect above. The screener uses a value index instead:

```
value index = price per sq ft / median price per sq ft of listings in the same city and the same 300 sq ft size band
```

0.80 means a listing is 20% cheaper than comparable listings. It is a screening rule for listings worth a closer look. It is not a forecast of returns, because the data has no rents, dates or price history.

## Run locally

```bash
git clone https://github.com/<your-username>/real-estate-investment-advisor.git
cd real-estate-investment-advisor
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The clean data is already in `data/`, so the app runs straight away.

To rebuild the clean data from the raw file, run the notebook from the `notebooks/` folder (it needs `jupyter`, `matplotlib` and `seaborn` in addition to the app requirements):

```bash
pip install jupyter matplotlib seaborn
cd notebooks
jupyter nbconvert --to notebook --execute --inplace real_estate_eda.ipynb
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Choose **Create app**, pick the repository and branch, and set the main file path to `app.py`.
4. Deploy. The first load reads the 250,000-row dataset and takes a few seconds; later interactions are cached.

`requirements.txt` needs Streamlit 1.50 or newer. If the app fails at start-up on an older runtime, open the app's advanced settings and choose Python 3.11 or 3.12.

## Project structure

```
.
├── app.py                     entry point, navigation and shared filters
├── pages/
│   ├── overview.py
│   ├── location.py
│   ├── features.py
│   ├── screener.py
│   └── insights.py
├── utils/
│   ├── data.py                loading, filters, value index, formatting
│   ├── stats.py               group comparisons, ANOVA, effect sizes
│   ├── charts.py              Plotly chart helpers
│   └── theme.py               palette, CSS and UI components
├── notebooks/
│   └── real_estate_eda.ipynb
├── data/
│   ├── housing_clean.csv.gz
│   └── raw/india_housing_prices.csv.gz
├── assets/                    logo, icon, favicon
├── .streamlit/config.toml     dark theme
└── requirements.txt
```

## Method notes

- **Price per sq ft** is rebuilt in rupees from price and size. The raw column is lakhs per sq ft rounded to two decimals, which collapses thousands of rows to 0.00.
- **Group comparisons** test each group against all other listings (Welch z-test) with Bonferroni correction for the number of groups, and show 95% confidence intervals.
- **Overall test** is a one-way ANOVA, with price per sq ft log-transformed. Effect size is eta squared, because with 250,000 rows even trivial differences can be statistically significant.
- **Inconsistent rows** (floor above total floors, old listings marked under construction) are flagged and kept out of conclusions instead of being deleted.

## Data

Source file: `india_housing_prices.csv`, 250,000 listings, 22 columns, 20 states, 42 cities. See the Insights and limitations page for the full list of caveats and the data fields that would be needed to judge actual investment returns.
