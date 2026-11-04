# ui_theme.py  (v2)
# Modul TAMPILAN saja. Tidak ada akses Supabase / data / logika bisnis di sini.
from urllib.parse import quote

import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------
# Palet warna
# ------------------------------------------------------------------
LIGHT = {
    "bg": "#F2F6F7",
    "glow1": "rgba(20,184,166,.14)",
    "glow2": "rgba(99,102,241,.10)",
    "surface": "#FFFFFF",
    "surface2": "#E9F0F1",
    "border": "#DCE5E7",
    "text": "#0F1F29",
    "text2": "#374B57",
    "muted": "#647A86",
    "accent": "#0F766E",
    "accent2": "#14B8A6",
    "accent_soft": "rgba(15,118,110,.10)",
    "btn_text": "#FFFFFF",
    "btn_grad": "linear-gradient(135deg,#0D9488,#0F766E)",
    "btn_hover": "linear-gradient(135deg,#0F766E,#115E59)",
    "hero": "linear-gradient(120deg,#0A4F4A 0%,#0F766E 50%,#0E9F8E 100%)",
    "sidebar": "#0B1F23",
    "shadow": "0 1px 2px rgba(15,31,41,.05), 0 8px 24px rgba(15,31,41,.06)",
    "shadow_lg": "0 2px 4px rgba(15,31,41,.06), 0 16px 36px rgba(15,31,41,.10)",
}
DARK = {
    "bg": "#081214",
    "glow1": "rgba(45,212,191,.12)",
    "glow2": "rgba(99,102,241,.16)",
    "surface": "#0F2024",
    "surface2": "#15292E",
    "border": "#21393F",
    "text": "#E8F1F2",
    "text2": "#BCCED2",
    "muted": "#86A0A7",
    "accent": "#2DD4BF",
    "accent2": "#5EEAD4",
    "accent_soft": "rgba(45,212,191,.14)",
    "btn_text": "#042F2E",
    "btn_grad": "linear-gradient(135deg,#5EEAD4,#2DD4BF)",
    "btn_hover": "linear-gradient(135deg,#99F6E4,#5EEAD4)",
    "hero": "linear-gradient(120deg,#0A3433 0%,#0E5C56 55%,#12806F 100%)",
    "sidebar": "#060E10",
    "shadow": "0 1px 2px rgba(0,0,0,.35), 0 8px 24px rgba(0,0,0,.30)",
    "shadow_lg": "0 2px 4px rgba(0,0,0,.4), 0 16px 36px rgba(0,0,0,.4)",
}

# ------------------------------------------------------------------
# Ikon (gaya garis)
# ------------------------------------------------------------------
_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
    "stroke='{c}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{p}</svg>"
)
_NAV_ICONS = [
    "<path d='m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/><polyline points='9 22 9 12 15 12 15 22'/>",
    "<path d='M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8'/><path d='M3 3v5h5'/>",
    "<line x1='8' y1='6' x2='21' y2='6'/><line x1='8' y1='12' x2='21' y2='12'/><line x1='8' y1='18' x2='21' y2='18'/>"
    "<line x1='3' y1='6' x2='3.01' y2='6'/><line x1='3' y1='12' x2='3.01' y2='12'/><line x1='3' y1='18' x2='3.01' y2='18'/>",
    "<path d='m7.5 4.27 9 5.15'/><path d='M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z'/>"
    "<path d='m3.3 7 8.7 5 8.7-5'/><path d='M12 22V12'/>",
    "<circle cx='8' cy='21' r='1'/><circle cx='19' cy='21' r='1'/>"
    "<path d='M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12'/>",
    "<path d='M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2'/><path d='M15 18H9'/>"
    "<path d='M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14'/>"
    "<circle cx='17' cy='18' r='2'/><circle cx='7' cy='18' r='2'/>",
    "<line x1='12' y1='20' x2='12' y2='10'/><line x1='18' y1='20' x2='18' y2='4'/><line x1='6' y1='20' x2='6' y2='16'/>",
    "<line x1='4' y1='21' x2='4' y2='14'/><line x1='4' y1='10' x2='4' y2='3'/><line x1='12' y1='21' x2='12' y2='12'/>"
    "<line x1='12' y1='8' x2='12' y2='3'/><line x1='20' y1='21' x2='20' y2='16'/><line x1='20' y1='12' x2='20' y2='3'/>"
    "<line x1='2' y1='14' x2='6' y2='14'/><line x1='10' y1='8' x2='14' y2='8'/><line x1='18' y1='16' x2='22' y2='16'/>",
]
# ikon kartu metrik: retur, tagihan (kartu), keranjang
_CARD_ICONS = [
    _NAV_ICONS[1],
    "<rect x='2' y='5' width='20' height='14' rx='2'/><line x1='2' y1='10' x2='22' y2='10'/>",
    _NAV_ICONS[4],
]
_CARD_COLORS = [("#14B8A6", "#0F766E"), ("#F59E0B", "#D97706"), ("#818CF8", "#4F46E5")]


def _uri(body: str, color: str) -> str:
    return "data:image/svg+xml," + quote(_SVG.format(c=color, p=body), safe="")


def _nav_icon_css() -> str:
    n = len(_NAV_ICONS)
    base = f'[data-testid="stSidebar"] div[role="radiogroup"] > label:first-child:nth-last-child({n})'
    out = [
        f'{base}::before, {base} ~ label::before {{content:"";width:18px;height:18px;flex:none;'
        "background:currentColor;-webkit-mask-size:contain;mask-size:contain;"
        "-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;"
        "-webkit-mask-position:center;mask-position:center;}"
    ]
    for k, body in enumerate(_NAV_ICONS, start=1):
        u = _uri(body, "black")
        sel = f"{base}::before" if k == 1 else f"{base} ~ label:nth-child({k})::before"
        out.append(f'{sel}{{-webkit-mask-image:url("{u}");mask-image:url("{u}");}}')
    return "\n".join(out)


def _card_icon_css() -> str:
    out = []
    for k, (body, (c1, c2)) in enumerate(zip(_CARD_ICONS, _CARD_COLORS), start=1):
        col = f'[data-testid="stColumn"]:nth-child({k})'
        out.append(f"{col} {{--c1:{c1};--c2:{c2};}}")
        out.append(
            f'{col} .metric-card::after {{background:url("{_uri(body, "white")}") center/22px no-repeat,'
            f"linear-gradient(135deg,{c1},{c2});}}"
        )
    return "\n".join(out)


# ------------------------------------------------------------------
# CSS statis
# ------------------------------------------------------------------
_STATIC_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp textarea,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-testid="stMarkdownContainer"] {
  font-family: 'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp {
  background: radial-gradient(900px 520px at 100% -8%, var(--glow1), transparent 60%),
              radial-gradient(760px 460px at -8% 0%, var(--glow2), transparent 58%), var(--bg);
  background-attachment: fixed; color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"], .block-container { padding-top: 1.6rem; max-width: 1320px; animation: tn-in .5s ease both; }
@keyframes tn-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--text); letter-spacing: -.02em; font-weight: 800; }
.stApp [data-testid="stMarkdownContainer"] p { color: var(--text2); }
.stApp [data-testid="stWidgetLabel"] p, .stApp label p { color: var(--text2); font-weight: 600; font-size: 13px; }
hr { border-color: var(--border) !important; opacity: 1; margin: 1.2rem 0 !important; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; border: 2px solid transparent; background-clip: padding-box; }

/* ---------- Banner header ---------- */
[data-testid="stHorizontalBlock"]:has(.app-header) {
  position: relative; overflow: hidden; align-items: center; gap: 1rem; padding: 26px 30px; border-radius: 22px;
  background: radial-gradient(520px 220px at 88% -30%, rgba(255,255,255,.26), transparent 62%),
              radial-gradient(380px 200px at 6% 130%, rgba(245,158,11,.30), transparent 62%), var(--hero);
  box-shadow: var(--shadow_lg); }
[data-testid="stHorizontalBlock"]:has(.app-header) > [data-testid="stColumn"]:last-child {
  flex: 0 0 auto !important; width: auto !important; min-width: 150px; }
.app-header { display: flex; align-items: center; gap: 14px; }
.app-title { font-size: 28px !important; font-weight: 800 !important; letter-spacing: -.03em; margin: 0 !important; padding: 0 !important;
  color: #FFFFFF !important; line-height: 1.12; }
.app-sub { margin: 6px 0 0 0; color: rgba(255,255,255,.82); font-size: 14px; font-weight: 500; }
[data-testid="stHorizontalBlock"]:has(.app-header) .stButton > button {
  background: rgba(255,255,255,.16); color: #fff; border: 1px solid rgba(255,255,255,.34); white-space: nowrap;
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); box-shadow: none; }
[data-testid="stHorizontalBlock"]:has(.app-header) .stButton > button:hover {
  background: rgba(255,255,255,.28); color: #fff; border-color: rgba(255,255,255,.6); }

/* ---------- Judul bagian (otomatis untuk st.markdown teks biasa) ---------- */
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] > p:not([class]) {
  font-size: 17px; font-weight: 800; letter-spacing: -.015em; color: var(--text); margin: .4rem 0 .2rem 0;
  display: flex; align-items: center; gap: 10px; }
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] > p:not([class])::before {
  content: ""; width: 5px; height: 18px; border-radius: 3px; background: linear-gradient(180deg, var(--accent2), var(--accent)); flex: none; }
[data-testid="stForm"] [data-testid="stMarkdownContainer"] > p:not([class]) { font-size: 14px; font-weight: 700; }
[data-testid="stForm"] [data-testid="stMarkdownContainer"] > p:not([class])::before { display: none; }
.section-title { font-size: 17px; font-weight: 800; letter-spacing: -.015em; color: var(--text); margin: .4rem 0 .2rem 0; display: flex; align-items: center; gap: 10px; }
.section-title::before { content: ""; width: 5px; height: 18px; border-radius: 3px; background: linear-gradient(180deg, var(--accent2), var(--accent)); }

/* ---------- Kartu metrik ---------- */
[data-testid="stColumn"] { --c1: #14B8A6; --c2: #0F766E; }
.metric-card { position: relative; overflow: hidden; background: var(--surface); border: 1px solid var(--border);
  border-radius: 18px; padding: 20px 84px 18px 22px; box-shadow: var(--shadow); transition: transform .2s ease, box-shadow .2s ease; }
.metric-card:hover { transform: translateY(-3px); box-shadow: var(--shadow_lg); }
.metric-card::before { content: ""; position: absolute; right: -40px; top: -40px; width: 150px; height: 150px; border-radius: 50%;
  background: radial-gradient(circle, var(--c1), transparent 68%); opacity: .20; pointer-events: none; }
.metric-card::after { content: ""; position: absolute; right: 18px; top: 18px; width: 46px; height: 46px; border-radius: 14px;
  background: linear-gradient(135deg, var(--c1), var(--c2)); box-shadow: 0 8px 18px rgba(0,0,0,.14); }
.metric-card .card-title, .card-title { font-size: 12.5px; font-weight: 600; color: var(--muted); margin-bottom: 8px; }
.metric-card div[style*="font-size:18px"] { font-size: 26px !important; font-weight: 800 !important; letter-spacing: -.03em;
  color: var(--text); font-variant-numeric: tabular-nums; line-height: 1.15; }
.small-muted { color: var(--muted) !important; font-size: 12.5px !important; }
.metric-card .small-muted { margin-top: 8px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background: radial-gradient(320px 240px at 0% 0%, rgba(20,184,166,.20), transparent 70%), var(--sidebar);
  border-right: 1px solid rgba(255,255,255,.06); }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] li { color: #CFE0E3; }
[data-testid="stSidebar"] .small-muted { color: #7F9AA1 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08) !important; }
[data-testid="stSidebar"] div[style*="background:#2563EB"] {
  background: linear-gradient(135deg, #2DD4BF, #0F766E) !important; border-radius: 14px !important;
  box-shadow: 0 8px 20px rgba(20,184,166,.40); letter-spacing: .02em; }
[data-testid="stSidebar"] div[style*="color:#94A3B8"] { color: #7F9AA1 !important; }
[data-testid="stSidebar"] div[style*="font-weight:700"] { color: #F2FAFA; }
[data-testid="stSidebar"] div[role="radiogroup"] { gap: 3px; }
[data-testid="stSidebar"] div[role="radiogroup"] > label {
  display: flex; align-items: center; gap: 12px; width: 100%; padding: 11px 14px; margin: 0;
  border-radius: 12px; cursor: pointer; transition: background .15s ease, color .15s ease, transform .15s ease; }
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:nth-of-type(1) { display: none; }
[data-testid="stSidebar"] div[role="radiogroup"] > label p { margin: 0; font-size: 14px; font-weight: 500; color: inherit; }
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: rgba(255,255,255,.07); transform: translateX(2px); }
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: linear-gradient(90deg, rgba(45,212,191,.28), rgba(45,212,191,.06)); color: #7CF0DE; box-shadow: inset 3px 0 0 #2DD4BF; }
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: #7CF0DE; font-weight: 700; }
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) {
  flex-direction: row; gap: 4px; padding: 4px; background: rgba(255,255,255,.07); border-radius: 14px; }
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) > label {
  flex: 1; justify-content: center; padding: 8px; }
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) > label:hover { transform: none; }
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) > label:has(input:checked) {
  background: linear-gradient(135deg, #2DD4BF, #0F766E); box-shadow: 0 4px 12px rgba(20,184,166,.4); }
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) > label:has(input:checked) p { color: #fff; }

/* ---------- Tombol ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 12px; font-weight: 700; padding: .6rem 1.1rem; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); transition: all .18s ease; box-shadow: 0 1px 2px rgba(15,31,41,.06); }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
  border-color: var(--accent); color: var(--accent); transform: translateY(-2px); box-shadow: 0 8px 18px rgba(15,31,41,.10); }
.stButton > button:active, .stDownloadButton > button:active, [data-testid="stFormSubmitButton"] > button:active { transform: translateY(0); }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"],
.stDownloadButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[data-testid="stBaseButton-primary"] {
  background: var(--btn_grad); color: var(--btn_text); border: none; box-shadow: 0 8px 20px rgba(15,118,110,.30); }
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button[data-testid="stBaseButton-primary"]:hover {
  background: var(--btn_hover); color: var(--btn_text); box-shadow: 0 12px 26px rgba(15,118,110,.38); }
.stButton > button p, .stDownloadButton > button p, [data-testid="stFormSubmitButton"] > button p { color: inherit; font-weight: 700; }
[data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.07); border-color: rgba(255,255,255,.14); color: #E3EEF0; box-shadow: none; }
[data-testid="stSidebar"] .stButton > button:hover { background: rgba(45,212,191,.18); border-color: #2DD4BF; color: #7CF0DE; box-shadow: none; }

/* ---------- Input ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  background: var(--surface) !important; border-color: var(--border) !important; border-radius: 12px !important; transition: box-shadow .15s ease, border-color .15s ease; }
[data-baseweb="base-input"] { background: transparent !important; }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] div { color: var(--text) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important; box-shadow: 0 0 0 4px var(--accent_soft) !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--surface) !important; border-radius: 12px; }
[data-baseweb="popover"] li { color: var(--text) !important; }
[data-baseweb="popover"] li:hover { background: var(--accent_soft) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--surface); border: 1.5px dashed var(--border); border-radius: 14px; transition: all .15s ease; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent); background: var(--accent_soft); }
[data-testid="stForm"] { background: linear-gradient(180deg, var(--accent_soft), transparent 110px), var(--surface);
  border: 1px solid var(--border); border-radius: 20px; padding: 24px; box-shadow: var(--shadow); }

/* ---------- Tab pil ---------- */
[data-baseweb="tab-list"] { gap: 4px; padding: 5px; background: var(--surface2); border-radius: 14px; width: fit-content; border: none; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
[data-baseweb="tab"] { border-radius: 10px; padding: 9px 18px; height: auto; background: transparent; transition: all .15s ease; }
[data-baseweb="tab"] p { font-weight: 700; color: var(--muted); font-size: 14px; }
[data-baseweb="tab"][aria-selected="true"] { background: var(--surface); box-shadow: 0 2px 8px rgba(15,31,41,.10); }
[data-baseweb="tab"][aria-selected="true"] p { color: var(--accent); }

/* ---------- Tabel, grafik, notifikasi, dialog ---------- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border: 1px solid var(--border); border-radius: 16px; overflow: hidden; box-shadow: var(--shadow); }
[data-testid="stPlotlyChart"] { background: var(--surface); border: 1px solid var(--border); border-radius: 18px; padding: 12px; box-shadow: var(--shadow); }
[data-testid="stAlert"] { border-radius: 14px; border: 1px solid var(--border); }
div[role="dialog"] { border-radius: 22px !important; background: var(--surface) !important; border: 1px solid var(--border); box-shadow: var(--shadow_lg); }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }
.js-plotly-plot .main-svg { background: transparent !important; }
.js-plotly-plot .plot-container .bg { fill: transparent !important; }

/* ---------- Loading: bar progres ---------- */
[data-testid="stStatusWidget"] { display: none !important; }
.stApp[data-teststate="running"]::after {
  content: ""; position: fixed; top: 0; left: 0; height: 4px; width: 38%; z-index: 999999; border-radius: 0 4px 4px 0;
  background: linear-gradient(90deg, transparent, #818CF8, var(--accent2), #F59E0B, transparent);
  box-shadow: 0 0 14px var(--accent2); animation: tn-run 1.05s cubic-bezier(.4,0,.2,1) infinite; }
@keyframes tn-run { 0% { transform: translateX(-100%); } 100% { transform: translateX(300%); } }

/* ---------- Loading: spinner ---------- */
[data-testid="stSpinner"] { display: flex; align-items: center; gap: 12px; padding: 12px 18px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 14px; width: fit-content; box-shadow: var(--shadow); }
[data-testid="stSpinner"] svg, [data-testid="stSpinner"] i { display: none !important; }
[data-testid="stSpinner"]::before { content: ""; flex: none; width: 20px; height: 20px; border-radius: 50%;
  border: 3px solid var(--accent_soft); border-top-color: var(--accent); border-right-color: var(--accent2); animation: tn-spin .75s linear infinite; }
[data-testid="stSpinner"] p, [data-testid="stSpinner"] div { color: var(--text2); font-weight: 600; margin: 0; }
@keyframes tn-spin { to { transform: rotate(360deg); } }

/* ---------- Loading: layar pembuka ---------- */
.tn-splash { position: fixed; inset: 0; z-index: 9999999; display: grid; place-items: center;
  background: radial-gradient(700px 460px at 80% 0%, var(--glow1), transparent 60%),
              radial-gradient(600px 400px at 0% 100%, var(--glow2), transparent 60%), var(--bg);
  animation: tn-splash-out .55s ease 1.6s forwards; }
.tn-splash-inner { display: flex; flex-direction: column; align-items: center; gap: 16px; text-align: center; }
.tn-ring { position: relative; width: 96px; height: 96px; display: grid; place-items: center; }
.tn-ring::before { content: ""; position: absolute; inset: 0; border-radius: 50%; border: 3px solid var(--accent_soft);
  border-top-color: var(--accent); border-right-color: var(--accent2); animation: tn-spin 1s linear infinite; }
.tn-ring::after { content: ""; position: absolute; inset: -14px; border-radius: 50%; border: 2px solid transparent;
  border-bottom-color: #F59E0B; border-left-color: #818CF8; opacity: .8; animation: tn-spin 1.8s linear infinite reverse; }
.tn-logo { width: 62px; height: 62px; border-radius: 18px; display: grid; place-items: center; color: #fff; font-weight: 800; font-size: 21px;
  letter-spacing: .03em; background: linear-gradient(135deg, #2DD4BF, #0F766E); box-shadow: 0 10px 26px rgba(20,184,166,.45); }
.tn-splash-title { font-size: 22px; font-weight: 800; letter-spacing: -.025em; color: var(--text); margin-top: 8px; }
.tn-splash-sub { font-size: 13.5px; color: var(--muted); }
.tn-bar { width: 200px; height: 5px; border-radius: 5px; background: var(--accent_soft); overflow: hidden; }
.tn-bar span { display: block; height: 100%; width: 40%; border-radius: 5px; background: linear-gradient(90deg, var(--accent2), var(--accent));
  animation: tn-bar 1.1s ease-in-out infinite; }
@keyframes tn-bar { 0% { transform: translateX(-110%); } 100% { transform: translateX(280%); } }
@keyframes tn-splash-out { to { opacity: 0; visibility: hidden; pointer-events: none; } }

@media (prefers-reduced-motion: reduce) {
  .tn-splash { animation-duration: .01ms; animation-delay: .4s; }
  [data-testid="stMainBlockContainer"], .block-container { animation: none; }
  .tn-ring::before, .tn-ring::after, .tn-bar span, [data-testid="stSpinner"]::before { animation-duration: 2.4s; }
}
@media (max-width: 640px) {
  .app-title { font-size: 21px !important; }
  [data-testid="stHorizontalBlock"]:has(.app-header) { padding: 18px; border-radius: 18px; }
  [data-testid="stMainBlockContainer"], .block-container { padding-left: 1rem; padding-right: 1rem; }
}
"""


def _compact(css: str) -> str:
    # Hapus baris kosong & indentasi agar markdown Streamlit tidak memecah blok <style>
    lines = [ln.strip() for ln in css.splitlines()]
    return "\n".join(ln for ln in lines if ln)


# ------------------------------------------------------------------
# API publik
# ------------------------------------------------------------------
def inject_theme(theme: str = "Terang") -> str:
    """Pasang seluruh CSS. Mengembalikan nama template plotly yang cocok."""
    pal = DARK if theme == "Gelap" else LIGHT
    root = ":root{" + "".join(f"--{k}:{v};" for k, v in pal.items()) + "}"
    css = root + "\n" + _STATIC_CSS + "\n" + _nav_icon_css() + "\n" + _card_icon_css()
    st.markdown(f"<style>\n{_compact(css)}\n</style>", unsafe_allow_html=True)

    # Palet grafik Plotly (hanya warna, tidak mengubah data)
    px.defaults.color_discrete_sequence = [
        "#0F766E", "#F59E0B", "#6366F1", "#E11D48", "#0EA5E9", "#84CC16", "#64748B",
    ]
    return "plotly_dark" if theme == "Gelap" else "plotly"


def show_splash() -> None:
    """Layar pembuka modern. Hanya tampil sekali per sesi."""
    if st.session_state.get("_tn_splash_done"):
        return
    st.session_state["_tn_splash_done"] = True
    st.markdown(
        "<div class='tn-splash'><div class='tn-splash-inner'>"
        "<div class='tn-ring'><div class='tn-logo'>TN</div></div>"
        "<div class='tn-splash-title'>Toserba Nurja Berkah</div>"
        "<div class='tn-splash-sub'>Menyiapkan data retur dan supplier</div>"
        "<div class='tn-bar'><span></span></div>"
        "</div></div>",
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    """Judul bagian (opsional). Teks st.markdown biasa sudah otomatis bergaya sama."""
    import html as _html

    st.markdown(f"<div class='section-title'>{_html.escape(text)}</div>", unsafe_allow_html=True)
