"""Visual theme — bold cream/coral/black-border 'dossier' aesthetic, matched
to a reference design. Targets stable Streamlit hooks (h1-h3, .stButton,
.stTextInput, etc.) rather than internal emotion-cache class names, which
change across Streamlit versions and would silently stop applying.
"""

import streamlit as st

CSS = """
<style>
:root {
    --bg: #F2EEE3;
    --ink: #111111;
    --accent: #E1503A;
    --accent-dark: #B23A28;
}

.stApp { background-color: var(--bg); }

h1, h2, h3 {
    text-transform: uppercase;
    font-weight: 800;
    letter-spacing: -0.01em;
    color: var(--ink);
}

h1 { text-shadow: 4px 4px 0px var(--accent); }

/* Buttons: hard black border, offset drop shadow, press-down on click */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
    background-color: var(--accent);
    color: #fff;
    border: 3px solid var(--ink) !important;
    border-radius: 0px !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    box-shadow: 5px 5px 0px var(--ink);
    transition: transform 0.05s ease, box-shadow 0.05s ease;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stDownloadButton > button:hover {
    color: #fff;
    border-color: var(--ink) !important;
    transform: translate(2px, 2px);
    box-shadow: 3px 3px 0px var(--ink);
}
.stButton > button:active,
.stFormSubmitButton > button:active,
.stDownloadButton > button:active {
    transform: translate(5px, 5px);
    box-shadow: 0px 0px 0px var(--ink);
}

/* Inputs: square corners, visible black border */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    border: 2px solid var(--ink) !important;
    border-radius: 0px !important;
    background-color: #fff !important;
}

/* File uploader box */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed var(--ink) !important;
    border-radius: 0px !important;
    background-color: #fff !important;
}

/* Expanders — used for lesson sections and quiz questions */
[data-testid="stExpander"] {
    border: 2px solid var(--ink) !important;
    border-radius: 0px !important;
    background-color: #fff !important;
    margin-bottom: 0.5rem;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.03em;
}

/* Custom ticker bar (own markup, fully controlled) */
.ml-ticker {
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
}

/* Tag chips — grounded/ungrounded, objective, difficulty */
.ml-chip {
    display: inline-block;
    padding: 2px 10px;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.04em;
    border: 2px solid var(--ink);
    margin-right: 6px;
    margin-bottom: 4px;
}
.ml-chip.ink { background: var(--ink); color: var(--accent); }
.ml-chip.accent { background: var(--accent); color: #fff; }
.ml-chip.outline { background: #fff; color: var(--ink); }

/* Step label — small black-boxed all-caps tag, echoes reference design */
.ml-step {
    display: inline-block;
    background: var(--ink);
    color: #fff;
    padding: 4px 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.8rem;
    margin-bottom: 0.75rem;
}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def ticker(*items: str) -> None:
    st.markdown(f'<div class="ml-ticker">{"&nbsp;&nbsp;/// &nbsp;&nbsp;".join(items)}</div>', unsafe_allow_html=True)


def step_label(text: str) -> None:
    st.markdown(f'<span class="ml-step">{text}</span>', unsafe_allow_html=True)


def chip(text: str, style: str = "outline") -> str:
    return f'<span class="ml-chip {style}">{text}</span>'


def chips(*parts: str) -> None:
    st.markdown("".join(parts), unsafe_allow_html=True)
