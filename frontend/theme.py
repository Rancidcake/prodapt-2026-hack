"""Visual theme — bold cream/coral/black-border 'dossier' aesthetic, matched
to a reference design. Targets stable Streamlit hooks (h1-h3, .stButton,
.stTextInput, etc.) rather than internal emotion-cache class names, which
change across Streamlit versions and would silently stop applying.

Accessibility is not a separate cosmetic layer bolted on top — the base
theme always ships visible keyboard-focus outlines and text-plus-color
status badges (never color alone). `inject()` additionally accepts three
opt-in toggles for large text, high contrast, and reduced motion, since
those are genuine trade-offs (e.g. high contrast drops the accent color
entirely) rather than things it's safe to force on everyone by default.
"""

import streamlit as st

_BASE = """
<style>
:root {{
    --bg: {bg};
    --ink: {ink};
    --accent: {accent};
    --font-scale: {font_scale};
}}

html, body, [class*="css"] {{ font-size: calc(1rem * var(--font-scale)); }}

.stApp {{ background-color: var(--bg); }}

h1, h2, h3 {{
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: -0.01em;
    color: var(--ink);
}}

h1 {{ text-shadow: 4px 4px 0px var(--accent); }}

/* Buttons: hard black border, offset drop shadow, press-down on click */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {{
    background-color: var(--accent);
    color: #fff;
    border: 3px solid var(--ink) !important;
    border-radius: 0px !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    box-shadow: 5px 5px 0px var(--ink);
    transition: {transition};
}}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stDownloadButton > button:hover {{
    color: #fff;
    border-color: var(--ink) !important;
    transform: {hover_transform};
    box-shadow: {hover_shadow};
}}
.stButton > button:active,
.stFormSubmitButton > button:active,
.stDownloadButton > button:active {{
    transform: {active_transform};
    box-shadow: {active_shadow};
}}

/* Keyboard focus must always be visible — never suppressed, regardless of
   which accessibility toggles are on. This is the one non-optional part. */
.stButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
.stTextInput input:focus-visible,
.stNumberInput input:focus-visible,
a:focus-visible {{
    outline: 3px solid var(--ink) !important;
    outline-offset: 2px !important;
}}

/* Inputs: square corners, visible black border */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {{
    border: 2px solid var(--ink) !important;
    border-radius: 0px !important;
    background-color: #fff !important;
    color: var(--ink) !important;
}}

/* File uploader box */
[data-testid="stFileUploaderDropzone"] {{
    border: 2px dashed var(--ink) !important;
    border-radius: 0px !important;
    background-color: #fff !important;
}}

/* Expanders — used for lesson sections and quiz questions */
[data-testid="stExpander"] {{
    border: 2px solid var(--ink) !important;
    border-radius: 0px !important;
    background-color: #fff !important;
    margin-bottom: 0.5rem;
}}

/* Tabs */
.stTabs [data-baseweb="tab"] {{
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.03em;
}}

/* Captions — kept dark enough to pass contrast checks even outside high-contrast mode */
[data-testid="stCaptionContainer"], .stCaption {{ color: {caption_color} !important; }}

/* Custom ticker bar (own markup, fully controlled) */
.ml-ticker {{
    background-color: var(--ink);
    color: var(--accent);
    padding: 10px 16px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-size: 0.85rem;
    border-top: 4px solid var(--ink);
    border-bottom: 4px solid var(--ink);
    margin: 0.5rem 0 1.5rem 0;
}}

/* Tag chips — grounded/ungrounded, objective, difficulty. Text-based, never
   color-only, so meaning survives for colorblind users and screen readers. */
.ml-chip {{
    display: inline-block;
    padding: 2px 10px;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.04em;
    border: 2px solid var(--ink);
    margin-right: 6px;
    margin-bottom: 4px;
}}
.ml-chip.ink {{ background: var(--ink); color: var(--accent); }}
.ml-chip.accent {{ background: var(--accent); color: #fff; }}
.ml-chip.outline {{ background: #fff; color: var(--ink); }}

/* Step label — small black-boxed all-caps tag, echoes reference design */
.ml-step {{
    display: inline-block;
    background: var(--ink);
    color: #fff;
    padding: 4px 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.8rem;
    margin-bottom: 0.75rem;
}}
</style>
"""


def inject(*, large_text: bool = False, high_contrast: bool = False, reduce_motion: bool = False) -> None:
    if high_contrast:
        # Pure black/white/accent only — drops the cream background and any
        # low-contrast gray, since high-contrast users are explicitly opting
        # out of the softer palette in exchange for maximum legibility.
        bg, ink, accent, caption_color = "#FFFFFF", "#000000", "#B23A28", "#000000"
    else:
        bg, ink, accent, caption_color = "#F2EEE3", "#111111", "#E1503A", "#3d3d3d"

    if reduce_motion:
        transition = "none"
        hover_transform = "none"
        hover_shadow = "5px 5px 0px var(--ink)"
        active_transform = "none"
        active_shadow = "5px 5px 0px var(--ink)"
    else:
        transition = "transform 0.05s ease, box-shadow 0.05s ease"
        hover_transform = "translate(2px, 2px)"
        hover_shadow = "3px 3px 0px var(--ink)"
        active_transform = "translate(5px, 5px)"
        active_shadow = "0px 0px 0px var(--ink)"

    st.markdown(
        _BASE.format(
            bg=bg,
            ink=ink,
            accent=accent,
            caption_color=caption_color,
            font_scale=1.25 if large_text else 1.0,
            transition=transition,
            hover_transform=hover_transform,
            hover_shadow=hover_shadow,
            active_transform=active_transform,
            active_shadow=active_shadow,
        ),
        unsafe_allow_html=True,
    )


def ticker(*items: str) -> None:
    st.markdown(f'<div class="ml-ticker">{"&nbsp;&nbsp;/// &nbsp;&nbsp;".join(items)}</div>', unsafe_allow_html=True)


def step_label(text: str) -> None:
    st.markdown(f'<span class="ml-step">{text}</span>', unsafe_allow_html=True)


def chip(text: str, style: str = "outline") -> str:
    return f'<span class="ml-chip {style}">{text}</span>'


def chips(*parts: str) -> None:
    st.markdown("".join(parts), unsafe_allow_html=True)
