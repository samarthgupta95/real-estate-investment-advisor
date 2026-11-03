"""Visual theme and small UI components (KPI cards, cards, callouts, signal chips)."""
import re

import streamlit as st

C = {
    "bg": "#0B1220",
    "surface": "#111A2B",
    "surface2": "#16223A",
    "border": "#22314D",
    "grid": "#1C2A44",
    "text": "#E6EBF4",
    "muted": "#8E9CB6",
    "blue": "#4EA8FF",
    "amber": "#F5B84B",
    "green": "#3DD6A0",
    "violet": "#9B8CFF",
    "coral": "#F2706B",
    "slate": "#5C6B8A",
}

FONT = "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
.stMarkdown, .stSelectbox, .stMultiSelect, .stSlider, .stRadio, .stToggle, .stCheckbox,
.stButton button, .stDownloadButton button, .stDataFrame, .stCaption, label, p, li, td, th {{
    font-family: {FONT} !important;
}}
.stApp {{ background: {C['bg']}; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: {C['surface']}; border-right: 1px solid {C['border']}; }}
.sb-head {{ font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: {C['muted']}; font-weight: 600; margin: .2rem 0 .6rem; }}
.sb-count {{ background: {C['surface2']}; border: 1px solid {C['border']}; border-radius: 10px; padding: .6rem .8rem; margin: .4rem 0 .6rem; font-size: .85rem; color: {C['muted']}; }}
.sb-count b {{ color: {C['text']}; font-size: 1.05rem; font-variant-numeric: tabular-nums; }}
.sb-note {{ font-size: .74rem; color: {C['muted']}; line-height: 1.45; margin-top: .6rem; }}

/* page header */
.ph {{ margin-bottom: 1.3rem; }}
.ph h1 {{ font-size: 1.85rem; font-weight: 700; letter-spacing: -.01em; margin: 0 0 .3rem; padding: 0; color: {C['text']}; }}
.ph p {{ color: {C['muted']}; font-size: .98rem; margin: 0 0 .8rem; max-width: 62rem; line-height: 1.5; }}
.pill {{ display: inline-block; background: {C['surface2']}; border: 1px solid {C['border']}; border-radius: 999px;
         padding: .22rem .75rem; font-size: .78rem; color: {C['muted']}; margin-right: .45rem; }}
.pill b {{ color: {C['text']}; font-weight: 600; }}
.ph-rule {{ height: 1px; background: linear-gradient(90deg, {C['blue']} 0%, {C['border']} 22%, {C['border']} 100%); margin: 1rem 0 1.4rem; }}

/* section heading */
.sec {{ margin: 1.7rem 0 .8rem; }}
.sec h3 {{ font-size: 1.15rem; font-weight: 650; margin: 0; padding: 0; color: {C['text']}; }}
.sec p {{ color: {C['muted']}; font-size: .88rem; margin: .2rem 0 0; }}

/* KPI card: value scales with card width and never wraps */
.kpi {{ container-type: inline-size; position: relative; overflow: hidden; background: {C['surface']};
        border: 1px solid {C['border']}; border-radius: 12px; padding: .95rem 1rem .85rem; }}
.kpi:before {{ content: ""; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--accent); }}
.kpi .kl {{ font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; color: {C['muted']}; font-weight: 600;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.kpi .kv {{ font-size: clamp(1rem, 9.5cqw, 1.7rem); font-weight: 650; color: {C['text']}; line-height: 1.2; margin: .35rem 0 .2rem;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }}
.kpi .ks {{ font-size: .76rem; color: {C['muted']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

/* cards (bordered containers created with a key starting with card_) */
[class*="st-key-card_"] {{ background: {C['surface']} !important; border: 1px solid {C['border']} !important;
                           border-radius: 14px !important; padding: .35rem .5rem .5rem !important; }}
.ct {{ font-size: 1rem; font-weight: 650; color: {C['text']}; margin: .15rem 0 .1rem; }}
.cs {{ font-size: .82rem; color: {C['muted']}; margin: 0 0 .5rem; line-height: 1.45; }}

/* callouts */
.callout {{ background: {C['surface']}; border: 1px solid {C['border']}; border-left: 3px solid {C['blue']};
            border-radius: 10px; padding: .85rem 1.1rem; font-size: .93rem; line-height: 1.6; color: {C['text']}; margin: 1rem 0; }}
.callout.warn {{ border-left-color: {C['amber']}; }}
.callout b {{ color: #fff; }}

/* signal chips */
.chip {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 12px; padding: .8rem .95rem; height: 100%; }}
.chip .cn {{ font-size: .76rem; color: {C['muted']}; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }}
.chip .cv {{ display: inline-block; margin: .4rem 0 .35rem; padding: .15rem .6rem; border-radius: 999px; font-size: .8rem; font-weight: 600; }}
.chip .cv.good {{ background: rgba(61,214,160,.14); color: {C['green']}; }}
.chip .cv.warn {{ background: rgba(245,184,75,.14); color: {C['amber']}; }}
.chip .cv.muted {{ background: rgba(142,156,182,.14); color: {C['muted']}; }}
.chip .cd {{ font-size: .78rem; color: {C['muted']}; line-height: 1.45; }}
.chip-note {{ font-size: .82rem; color: {C['muted']}; margin: 0 0 .6rem; }}

/* insight and recommendation cards */
.ic {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 14px; padding: 1.05rem 1.2rem; height: 100%; }}
.ic .tag {{ font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
.ic h4 {{ font-size: 1.05rem; font-weight: 650; margin: .4rem 0 .5rem; padding: 0; color: {C['text']}; line-height: 1.35; }}
.ic p {{ font-size: .9rem; color: #C5CEDF; line-height: 1.6; margin: 0 0 .6rem; }}
.ic .ev {{ border-top: 1px solid {C['border']}; padding-top: .55rem; margin-top: .4rem; font-size: .8rem; color: {C['muted']}; line-height: 1.5; }}
.ic .ev b {{ color: {C['text']}; }}

.lim li {{ margin-bottom: .55rem; line-height: 1.6; color: #C5CEDF; }}
.lim b {{ color: {C['text']}; }}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str, n_rows: int | None = None, total: int | None = None) -> None:
    pills = ""
    if n_rows is not None:
        if total and n_rows != total:
            pills = f'<span class="pill"><b>{n_rows:,}</b> of {total:,} listings in view</span>'
        else:
            pills = f'<span class="pill"><b>{n_rows:,}</b> listings in view</span>'
    st.markdown(f'<div class="ph"><h1>{title}</h1><p>{subtitle}</p>{pills}</div><div class="ph-rule"></div>', unsafe_allow_html=True)


def section(title: str, sub: str = "") -> None:
    sub_html = f"<p>{sub}</p>" if sub else ""
    st.markdown(f'<div class="sec"><h3>{title}</h3>{sub_html}</div>', unsafe_allow_html=True)


def kpi(label: str, value: str, sub: str = "", accent: str | None = None) -> None:
    accent = accent or C["blue"]
    st.markdown(
        f'<div class="kpi" style="--accent:{accent}" title="{label}: {value}">'
        f'<div class="kl">{label}</div><div class="kv">{value}</div><div class="ks" title="{sub}">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def kpi_row(items: list[tuple]) -> None:
    cols = st.columns(len(items), gap="small")
    for col, item in zip(cols, items):
        with col:
            kpi(*item)
    st.markdown('<div style="height:.9rem"></div>', unsafe_allow_html=True)


def card(title: str, sub: str = ""):
    key = "card_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:60]
    box = st.container(border=True, key=key)
    with box:
        st.markdown(f'<div class="ct">{title}</div>' + (f'<div class="cs">{sub}</div>' if sub else ""), unsafe_allow_html=True)
    return box


def callout(text: str, tone: str = "info") -> None:
    cls = "callout warn" if tone == "warn" else "callout"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)


def signal_chips(chips: list[tuple], note: str = "") -> None:
    """chips: (name, verdict label, tone, detail)"""
    if note:
        st.markdown(f'<div class="chip-note">{note}</div>', unsafe_allow_html=True)
    cols = st.columns(len(chips), gap="small")
    for col, (name, label, tone, detail) in zip(cols, chips):
        with col:
            st.markdown(
                f'<div class="chip"><div class="cn">{name}</div><span class="cv {tone}">{label}</span><div class="cd">{detail}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('<div style="height:.9rem"></div>', unsafe_allow_html=True)


def info_card(tag: str, tag_color: str, title: str, body: str, evidence: str = "") -> None:
    ev = f'<div class="ev">{evidence}</div>' if evidence else ""
    st.markdown(
        f'<div class="ic"><div class="tag" style="color:{tag_color}">{tag}</div><h4>{title}</h4><p>{body}</p>{ev}</div>',
        unsafe_allow_html=True,
    )
