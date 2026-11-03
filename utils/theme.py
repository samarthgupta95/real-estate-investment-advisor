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

/* page header, hero and stripe */
.ph {{ display: flex; align-items: center; gap: 1rem; margin-bottom: .6rem; }}
.ph .mark {{ flex: none; }}
.ph h1 {{ font-size: 2rem; font-weight: 800; letter-spacing: -.02em; margin: 0; padding: 0; color: {C['text']}; line-height: 1.15; }}
.ph-sub {{ color: {C['muted']}; font-size: .98rem; margin: 0 0 .9rem; max-width: 62rem; line-height: 1.55; }}
.pill {{ display: inline-block; background: {C['surface2']}; border: 1px solid {C['border']}; border-radius: 999px;
         padding: .25rem .8rem; font-size: .8rem; color: {C['muted']}; margin-right: .45rem; }}
.pill b {{ color: {C['text']}; font-weight: 600; }}
.stripe {{ display: flex; gap: 5px; height: 4px; margin: 1.1rem 0 1.6rem; }}
.stripe span {{ border-radius: 4px; }}
.hero {{ position: relative; overflow: hidden; border: 1px solid {C['border']}; border-radius: 22px; padding: 2.2rem 2.4rem 2rem;
         background: radial-gradient(900px 340px at 92% -10%, rgba(78,168,255,.30), transparent 60%),
                     radial-gradient(700px 300px at 70% 120%, rgba(155,140,255,.22), transparent 60%), {C['surface']}; }}
.hero-top {{ display: flex; align-items: center; gap: .8rem; margin-bottom: 1.4rem; }}
.hero-brand {{ font-size: .8rem; letter-spacing: .2em; font-weight: 600; color: {C['muted']}; text-transform: uppercase; }}
.hero-brand b {{ color: {C['text']}; font-weight: 700; }}
.hero h1 {{ font-size: clamp(2rem, 4.2vw, 3.2rem); font-weight: 800; letter-spacing: -.03em; line-height: 1.08; margin: 0 0 .9rem; padding: 0;
            color: #fff; max-width: 40rem; }}
.hero p {{ color: #B4C0D6; font-size: 1.05rem; line-height: 1.6; margin: 0 0 1.3rem; max-width: 40rem; }}

/* section heading */
.sec {{ margin: 1.9rem 0 .9rem; }}
.sec h3 {{ font-size: 1.3rem; font-weight: 750; letter-spacing: -.01em; margin: 0; padding: 0; color: {C['text']}; }}
.sec p {{ color: {C['muted']}; font-size: .9rem; margin: .25rem 0 0; }}

/* KPI card: value scales with card width and never wraps */
.kpi {{ container-type: inline-size; position: relative; overflow: hidden; background: linear-gradient(160deg, {C['surface2']} 0%, {C['surface']} 70%);
        border: 1px solid {C['border']}; border-radius: 14px; padding: 1.15rem 1.2rem 1.05rem 1.35rem; }}
.kpi:before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--accent); }}
.kpi .kl {{ font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; color: {C['muted']}; font-weight: 600;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.kpi .kv {{ font-size: clamp(1.15rem, 12.5cqw, 2.25rem); font-weight: 800; letter-spacing: -.02em; color: #fff; line-height: 1.15; margin: .5rem 0 .35rem;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }}
.kpi .ks {{ font-size: .78rem; color: {C['muted']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

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


MARK = ('<svg class="mark" width="{w}" height="{w}" viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="#4EA8FF"/>'
        '<rect x="11" y="27" width="7" height="13" rx="1.5" fill="#0B1220"/><rect x="21" y="19" width="7" height="21" rx="1.5" fill="#0B1220"/>'
        '<rect x="31" y="10" width="7" height="30" rx="1.5" fill="#0B1220"/></svg>')
STRIPE = ('<div class="stripe"><span style="flex:5;background:#4EA8FF"></span><span style="flex:2;background:#3DD6A0"></span>'
          '<span style="flex:2;background:#F5B84B"></span><span style="flex:2;background:#F2706B"></span>'
          '<span style="flex:2;background:#9B8CFF"></span><span style="flex:2;background:#5C6B8A"></span></div>')


def _pills(n_rows, total) -> str:
    if n_rows is None:
        return ""
    if total and n_rows != total:
        return f'<span class="pill"><b>{n_rows:,}</b> of {total:,} listings in view</span>'
    return f'<span class="pill"><b>{n_rows:,}</b> listings in view</span>'


def page_header(title: str, subtitle: str, n_rows: int | None = None, total: int | None = None) -> None:
    st.markdown(
        f'<div class="ph">{MARK.format(w=46)}<h1>{title}</h1></div><div class="ph-sub">{subtitle}</div>{_pills(n_rows, total)}{STRIPE}',
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, n_rows: int | None = None, total: int | None = None) -> None:
    st.markdown(
        f'<div class="hero"><div class="hero-top">{MARK.format(w=44)}<span class="hero-brand">Real Estate <b>Investment Advisor</b></span></div>'
        f'<h1>{title}</h1><p>{subtitle}</p>{_pills(n_rows, total)}</div>{STRIPE}',
        unsafe_allow_html=True,
    )


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
