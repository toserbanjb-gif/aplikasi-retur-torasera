# app.py
import datetime
from io import BytesIO
import html
import pandas as pd
import streamlit as st
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client
import reportlab.lib.pagesizes
# ui_theme.py
# Modul TAMPILAN saja. Tidak ada akses Supabase / data / logika bisnis di sini.
from urllib.parse import quote

import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------
# Palet warna
# ------------------------------------------------------------------
LIGHT = {
    "bg": "#F4F7F7",
    "surface": "#FFFFFF",
    "surface2": "#EDF2F2",
    "border": "#DDE5E6",
    "text": "#12212B",
    "text2": "#3C4F5A",
    "muted": "#667B86",
    "accent": "#0F766E",
    "accent2": "#14B8A6",
    "accent_soft": "rgba(15,118,110,.10)",
    "btn_text": "#FFFFFF",
    "btn_hover": "#115E59",
    "sidebar": "#0E2428",
    "shadow": "0 1px 2px rgba(16,24,40,.05), 0 4px 14px rgba(16,24,40,.04)",
}
DARK = {
    "bg": "#0A1416",
    "surface": "#112125",
    "surface2": "#172B30",
    "border": "#223940",
    "text": "#E7F0F1",
    "text2": "#BBCDD1",
    "muted": "#86A0A7",
    "accent": "#2DD4BF",
    "accent2": "#5EEAD4",
    "accent_soft": "rgba(45,212,191,.12)",
    "btn_text": "#042F2E",
    "btn_hover": "#5EEAD4",
    "sidebar": "#071013",
    "shadow": "0 1px 2px rgba(0,0,0,.3), 0 6px 18px rgba(0,0,0,.25)",
}

# ------------------------------------------------------------------
# Ikon menu sidebar (gaya garis, dipakai sebagai CSS mask)
# Urutan harus sama dengan urutan menu di app.py
# ------------------------------------------------------------------
_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
    "stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{}</svg>"
)
_NAV_ICONS = [
    # Home
    "<path d='m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/><polyline points='9 22 9 12 15 12 15 22'/>",
    # Input Retur
    "<path d='M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8'/><path d='M3 3v5h5'/>",
    # List Retur
    "<line x1='8' y1='6' x2='21' y2='6'/><line x1='8' y1='12' x2='21' y2='12'/><line x1='8' y1='18' x2='21' y2='18'/>"
    "<line x1='3' y1='6' x2='3.01' y2='6'/><line x1='3' y1='12' x2='3.01' y2='12'/><line x1='3' y1='18' x2='3.01' y2='18'/>",
    # Permintaan Barang
    "<path d='m7.5 4.27 9 5.15'/><path d='M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z'/>"
    "<path d='m3.3 7 8.7 5 8.7-5'/><path d='M12 22V12'/>",
    # Input Pembelian
    "<circle cx='8' cy='21' r='1'/><circle cx='19' cy='21' r='1'/>"
    "<path d='M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12'/>",
    # Data Supplier
    "<path d='M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2'/><path d='M15 18H9'/>"
    "<path d='M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14'/>"
    "<circle cx='17' cy='18' r='2'/><circle cx='7' cy='18' r='2'/>",
    # Laporan
    "<line x1='12' y1='20' x2='12' y2='10'/><line x1='18' y1='20' x2='18' y2='4'/><line x1='6' y1='20' x2='6' y2='16'/>",
    # Pengaturan
    "<line x1='4' y1='21' x2='4' y2='14'/><line x1='4' y1='10' x2='4' y2='3'/><line x1='12' y1='21' x2='12' y2='12'/>"
    "<line x1='12' y1='8' x2='12' y2='3'/><line x1='20' y1='21' x2='20' y2='16'/><line x1='20' y1='12' x2='20' y2='3'/>"
    "<line x1='2' y1='14' x2='6' y2='14'/><line x1='10' y1='8' x2='14' y2='8'/><line x1='18' y1='16' x2='22' y2='16'/>",
]


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
        uri = "data:image/svg+xml," + quote(_SVG.format(body), safe="")
        sel = f"{base}::before" if k == 1 else f"{base} ~ label:nth-child({k})::before"
        out.append(f'{sel}{{-webkit-mask-image:url("{uri}");mask-image:url("{uri}");}}')
    return "\n".join(out)


# ------------------------------------------------------------------
# CSS statis (memakai variabel warna dari :root)
# ------------------------------------------------------------------
_STATIC_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp textarea,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-testid="stMarkdownContainer"] {
  font-family: 'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"], .block-container { padding-top: 2.2rem; max-width: 1280px; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--text); letter-spacing: -.015em; }
.stApp [data-testid="stMarkdownContainer"] p { color: var(--text2); }
.stApp [data-testid="stWidgetLabel"] p, .stApp label p { color: var(--text2); font-weight: 600; font-size: 13px; }
hr { border-color: var(--border) !important; opacity: 1; }

/* ---------- Header halaman ---------- */
.app-header { display:flex; align-items:center; gap:12px; }
.app-title { font-size: 26px !important; font-weight: 800 !important; letter-spacing: -.025em; margin: 0; padding: 0; color: var(--text); line-height: 1.15; }
.app-sub { margin: 4px 0 0 0; color: var(--muted); font-size: 13.5px; }
.section-title { font-size: 18px; font-weight: 700; letter-spacing: -.01em; color: var(--text); margin: 6px 0 4px 0; display:flex; align-items:center; gap:10px; }
.section-title::before { content:""; width:4px; height:18px; border-radius:2px; background: var(--accent); }

/* ---------- Kartu metrik ---------- */
.metric-card { position: relative; overflow: hidden; background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 16px 18px 15px 20px; box-shadow: var(--shadow); }
.metric-card::before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background: var(--accent); }
.metric-card .card-title, .card-title { font-size: 12.5px; font-weight: 600; color: var(--muted); margin-bottom: 8px; }
.metric-card div[style*="font-size:18px"] { font-size: 25px !important; font-weight: 800 !important; letter-spacing: -.025em;
  color: var(--text); font-variant-numeric: tabular-nums; }
.small-muted { color: var(--muted) !important; font-size: 12.5px !important; }

/* ---------- Sidebar (gelap) ---------- */
[data-testid="stSidebar"] { background: var(--sidebar); border-right: 1px solid rgba(255,255,255,.06); }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] li { color: #CFE0E3; }
[data-testid="stSidebar"] .small-muted { color: #7F9AA1 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08) !important; }
[data-testid="stSidebar"] div[style*="background:#2563EB"] {
  background: linear-gradient(135deg, #14B8A6, #0F766E) !important; border-radius: 12px !important;
  box-shadow: 0 4px 14px rgba(20,184,166,.35); letter-spacing: .02em; }
[data-testid="stSidebar"] div[style*="color:#94A3B8"] { color: #7F9AA1 !important; }
[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
[data-testid="stSidebar"] div[role="radiogroup"] > label {
  display:flex; align-items:center; gap:11px; width:100%; padding: 10px 12px; margin: 0;
  border-radius: 10px; cursor: pointer; transition: background .15s ease, color .15s ease; }
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:nth-of-type(1) { display: none; }
[data-testid="stSidebar"] div[role="radiogroup"] > label p { margin: 0; font-size: 14px; font-weight: 500; color: inherit; }
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: rgba(255,255,255,.06); }
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: rgba(45,212,191,.14); color: #5EEAD4; box-shadow: inset 3px 0 0 #2DD4BF; }
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: #5EEAD4; font-weight: 700; }
/* pilihan Terang/Gelap jadi segmented control */
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) {
  flex-direction: row; gap: 4px; padding: 4px; background: rgba(255,255,255,.06); border-radius: 12px; }
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) > label {
  flex: 1; justify-content: center; padding: 7px 8px; }
[data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) > label:has(input:checked) {
  background: rgba(45,212,191,.2); box-shadow: none; }

/* ---------- Tombol ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 10px; font-weight: 600; padding: .55rem 1rem; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); transition: all .15s ease; box-shadow: 0 1px 2px rgba(16,24,40,.05); }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
  border-color: var(--accent); color: var(--accent); transform: translateY(-1px); }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"],
.stDownloadButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[data-testid="stBaseButton-primary"] {
  background: var(--accent); color: var(--btn_text); border-color: var(--accent); box-shadow: 0 4px 12px rgba(15,118,110,.25); }
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button[data-testid="stBaseButton-primary"]:hover {
  background: var(--btn_hover); color: var(--btn_text); border-color: var(--btn_hover); }
.stButton > button p, .stDownloadButton > button p, [data-testid="stFormSubmitButton"] > button p { color: inherit; font-weight: 600; }
[data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.12); color: #E3EEF0; box-shadow: none; }
[data-testid="stSidebar"] .stButton > button:hover { background: rgba(45,212,191,.16); border-color: #2DD4BF; color: #5EEAD4; }

/* ---------- Input ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  background: var(--surface) !important; border-color: var(--border) !important; border-radius: 10px !important; }
[data-baseweb="base-input"] { background: transparent !important; }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] div { color: var(--text) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent_soft) !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--surface) !important; }
[data-baseweb="popover"] li { color: var(--text) !important; }
[data-baseweb="popover"] li:hover { background: var(--accent_soft) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--surface); border: 1.5px dashed var(--border); border-radius: 12px; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent); }
[data-testid="stForm"] { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; box-shadow: var(--shadow); }

/* ---------- Tab, tabel, notifikasi, dialog ---------- */
[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--border); }
[data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 10px 16px; }
[data-baseweb="tab"] p { font-weight: 600; color: var(--muted); }
[data-baseweb="tab"][aria-selected="true"] p { color: var(--accent); }
[data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 3px !important; border-radius: 3px; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); }
[data-testid="stAlert"] { border-radius: 12px; border: 1px solid var(--border); }
div[role="dialog"] { border-radius: 18px !important; background: var(--surface) !important; border: 1px solid var(--border); }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
.js-plotly-plot .main-svg { background: transparent !important; }
.js-plotly-plot .plot-container .bg { fill: transparent !important; }

/* ---------- Loading: bar progres di atas halaman ---------- */
[data-testid="stStatusWidget"] { display: none !important; }
.stApp[data-teststate="running"]::after {
  content:""; position: fixed; top: 0; left: 0; height: 3px; width: 38%; z-index: 999999; border-radius: 0 3px 3px 0;
  background: linear-gradient(90deg, transparent, var(--accent2), var(--accent), transparent);
  animation: tn-run 1.05s cubic-bezier(.4,0,.2,1) infinite; }
@keyframes tn-run { 0% { transform: translateX(-100%); } 100% { transform: translateX(300%); } }

/* ---------- Loading: spinner st.spinner ---------- */
[data-testid="stSpinner"] { display:flex; align-items:center; gap:12px; padding: 12px 16px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px; width: fit-content; box-shadow: var(--shadow); }
[data-testid="stSpinner"] svg, [data-testid="stSpinner"] i { display: none !important; }
[data-testid="stSpinner"]::before { content:""; flex:none; width:18px; height:18px; border-radius:50%;
  border: 2.5px solid var(--accent_soft); border-top-color: var(--accent); border-right-color: var(--accent2);
  animation: tn-spin .75s linear infinite; }
[data-testid="stSpinner"] p, [data-testid="stSpinner"] div { color: var(--text2); font-weight: 600; margin: 0; }
@keyframes tn-spin { to { transform: rotate(360deg); } }

/* ---------- Loading: layar pembuka ---------- */
.tn-splash { position: fixed; inset: 0; z-index: 9999999; display: grid; place-items: center; background: var(--bg);
  animation: tn-splash-out .55s ease 1.5s forwards; }
.tn-splash-inner { display:flex; flex-direction:column; align-items:center; gap: 14px; text-align:center; }
.tn-ring { position: relative; width: 88px; height: 88px; display: grid; place-items: center; }
.tn-ring::before { content:""; position:absolute; inset:0; border-radius:50%; border: 3px solid var(--accent_soft);
  border-top-color: var(--accent); border-right-color: var(--accent2); animation: tn-spin 1s linear infinite; }
.tn-logo { width: 58px; height: 58px; border-radius: 16px; display:grid; place-items:center; color:#fff; font-weight: 800; font-size: 20px;
  letter-spacing: .03em; background: linear-gradient(135deg, #14B8A6, #0F766E); box-shadow: 0 8px 22px rgba(20,184,166,.35); }
.tn-splash-title { font-size: 20px; font-weight: 800; letter-spacing: -.02em; color: var(--text); }
.tn-splash-sub { font-size: 13px; color: var(--muted); }
.tn-bar { width: 180px; height: 4px; border-radius: 4px; background: var(--accent_soft); overflow: hidden; }
.tn-bar span { display:block; height:100%; width: 40%; border-radius: 4px; background: linear-gradient(90deg, var(--accent2), var(--accent));
  animation: tn-bar 1.1s ease-in-out infinite; }
@keyframes tn-bar { 0% { transform: translateX(-110%); } 100% { transform: translateX(280%); } }
@keyframes tn-splash-out { to { opacity: 0; visibility: hidden; pointer-events: none; } }

@media (prefers-reduced-motion: reduce) {
  .tn-splash { animation-duration: .01ms; animation-delay: .4s; }
  .tn-ring::before, .tn-bar span, [data-testid="stSpinner"]::before { animation-duration: 2.4s; }
}
@media (max-width: 640px) {
  .app-title { font-size: 20px !important; }
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
    css = root + "\n" + _STATIC_CSS + "\n" + _nav_icon_css()
    st.markdown(f"<style>\n{_compact(css)}\n</style>", unsafe_allow_html=True)

    # Palet grafik Plotly (hanya warna, tidak mengubah data)
    px.defaults.color_discrete_sequence = [
        "#0F766E", "#F59E0B", "#4F46E5", "#E11D48", "#0EA5E9", "#84CC16", "#64748B",
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
    """Judul bagian bergaya baru (opsional, pengganti st.markdown("Judul"))."""
    import html as _html

    st.markdown(f"<div class='section-title'>{_html.escape(text)}</div>", unsafe_allow_html=True)
# --- CONFIG PAGE ---
st.set_page_config(
    page_title="Sistem Manajemen Retur - Toserba Nurja Berkah",
    page_icon="",
    layout="wide",
)

# --- CUSTOM STYLES (font, cards, buttons) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .app-header { display:flex; align-items:center; gap:12px; }
    .app-title { font-size:20px; font-weight:700; margin:0; }
    .app-sub { margin:0; color: #64748B; font-size:13px; }
    .metric-card { background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); padding:12px; border-radius:8px; box-shadow: 0 1px 4px rgba(2,6,23,0.04); }
    .small-muted { color:#94A3B8; font-size:12px; }
    .card-title { font-size:13px; font-weight:600; margin-bottom:6px; }
    [data-testid="stSidebar"] .css-1d391kg { padding-top: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- INISIALISASI STATE THEME ---
if "theme" not in st.session_state:
    st.session_state.theme = "Terang"

# --- HELPERS ---
def format_rp(val):
    try:
        return f"Rp {float(val):,.0f}"
    except Exception:
        return "Rp 0"

# safe extraction of public url from Supabase storage responses
def extract_public_url(res):
    try:
        if not res:
            return ""
        if isinstance(res, str):
            return res
        if isinstance(res, dict):
            # common keys used by various supabase libs
            for k in ("publicUrl", "publicURL", "public_url", "public_url"):
                if k in res and res[k]:
                    return res[k]
            # sometimes it's nested under "data"
            data = res.get("data")
            if isinstance(data, dict):
                for k in ("publicUrl", "publicURL", "public_url"):
                    if k in data and data[k]:
                        return data[k]
        return ""
    except Exception:
        return ""

# --- INISIALISASI SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url: str = st.secrets["SUPABASE_URL"].strip()
    key: str = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

# --- HELPER: coba insert/update dengan fallback jika terjadi error kolom tidak ada ---
def insert_with_optional_columns(table_name: str, payload: dict):
    """
    Coba insert payload. Jika PostgREST error menyebut kolom tertentu tidak ada,
    buang kolom itu dan coba lagi. Kembalikan tuple (success_bool, message_or_response).
    """
    try:
        res = supabase.table(table_name).insert(payload).execute()
        return True, res
    except Exception as e:
        msg = str(e)
        # contoh pesan: "Could not find the 'jenis_pajak' column of 'data_pembelian' in the schema cache"
        # cari pola kolom yang tidak ada
        if "Could not find the '" in msg and "' column" in msg:
            try:
                start = msg.index("Could not find the '") + len("Could not find the '")
                col = msg[start: msg.index("'", start)]
                if col in payload:
                    payload2 = {k: v for k, v in payload.items() if k != col}
                    try:
                        res2 = supabase.table(table_name).insert(payload2).execute()
                        return False, f"Kolom '{col}' tidak ditemukan di tabel '{table_name}'. Data disimpan tanpa kolom tersebut."
                    except Exception as e2:
                        return False, f"Gagal menyimpan data (setelah menghapus '{col}'): {e2}"
            except Exception:
                pass
        return False, f"Gagal menyimpan data pembelian: {msg}"

def update_with_optional_columns(table_name: str, payload: dict, where_field: str, where_value):
    try:
        res = supabase.table(table_name).update(payload).eq(where_field, where_value).execute()
        return True, res
    except Exception as e:
        msg = str(e)
        if "Could not find the '" in msg and "' column" in msg:
            try:
                start = msg.index("Could not find the '") + len("Could not find the '")
                col = msg[start: msg.index("'", start)]
                if col in payload:
                    payload2 = {k: v for k, v in payload.items() if k != col}
                    try:
                        res2 = supabase.table(table_name).update(payload2).eq(where_field, where_value).execute()
                        return False, f"Kolom '{col}' tidak ditemukan di tabel '{table_name}'. Data diperbarui tanpa kolom tersebut."
                    except Exception as e2:
                        return False, f"Gagal mengupdate data (setelah menghapus '{col}'): {e2}"
            except Exception:
                pass
        return False, f"Gagal mengupdate data pembelian: {msg}"

# --- FUNGSI AMBIL DATA SUPPLIER ---
def ambil_data_supplier(cari=""):
    try:
        query = supabase.table("data_supplier").select("*")
        response = query.execute()
        if not response.data:
            # jika tidak ada data, kembalikan df kosong namun dengan kolom yang aman
            cols = ["id", "no_urut", "nama_supplier", "tagihan", "jenis_pajak", "sistem_bayar", "jatuh_tempo"]
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame(response.data)
        df.columns = [str(c).lower() for c in df.columns]
        
        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)
            
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
        if "no_urut" in df.columns:
            df["no_urut"] = pd.to_numeric(df["no_urut"], errors="coerce").fillna(1).astype(int)
        else:
            df["no_urut"] = range(1, len(df) + 1)
        if "tagihan" in df.columns:
            df["tagihan"] = pd.to_numeric(df["tagihan"], errors="coerce").fillna(0.0).astype(float)
        else:
            df["tagihan"] = 0.0
        df["nama_supplier"] = df["nama_supplier"].astype(str) if "nama_supplier" in df.columns else ""
        if "jenis_pajak" in df.columns:
            df["jenis_pajak"] = df["jenis_pajak"].astype(str).fillna("Non PKP")
        else:
            df["jenis_pajak"] = "Non PKP"
        df["sistem_bayar"] = df["sistem_bayar"].astype(str) if "sistem_bayar" in df.columns else ""
        
        if "jatuh_tempo" in df.columns:
            df["jatuh_tempo"] = pd.to_datetime(df["jatuh_tempo"], errors="coerce").dt.date
        else:
            df["jatuh_tempo"] = pd.Series([datetime.date.today() for _ in range(len(df))])
            
        if cari:
            kw = cari.lower()
            df = df[
                df["nama_supplier"].str.lower().str.contains(kw) |
                df["jenis_pajak"].str.lower().str.contains(kw) |
                df["sistem_bayar"].str.lower().str.contains(kw)
            ]
        return df
    except Exception:
        cols = ["id", "no_urut", "nama_supplier", "tagihan", "jenis_pajak", "sistem_bayar", "jatuh_tempo"]
        return pd.DataFrame(columns=cols)

# --- FUNGSI AMBIL DATA PEMBELIAN / INVOICE ---
def ambil_data_pembelian(cari=""):
    try:
        query = supabase.table("data_pembelian").select("*")
        response = query.execute()
        if not response.data:
            # kembalikan df kosong dengan kolom yang umum agar UI tidak pecah
            cols = ["id", "no_invoice", "nama_supplier", "total_tagihan", "tgl_datang", "jatuh_tempo", "status_lunas", "link_foto", "link_bayar", "link_faktur_pajak", "jenis_pajak"]
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame(response.data)
        df.columns = [str(c).lower() for c in df.columns]
        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)
        
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
        if "total_tagihan" in df.columns:
            df["total_tagihan"] = pd.to_numeric(df["total_tagihan"], errors="coerce").fillna(0.0).astype(float)
        else:
            df["total_tagihan"] = 0.0
        
        if "tgl_datang" in df.columns:
            df["tgl_datang"] = pd.to_datetime(df["tgl_datang"], errors="coerce").dt.date
        if "jatuh_tempo" in df.columns:
            df["jatuh_tempo"] = pd.to_datetime(df["jatuh_tempo"], errors="coerce").dt.date

        # ensure new columns exist and default values
        if "link_foto" not in df.columns:
            df["link_foto"] = ""
        else:
            df["link_foto"] = df["link_foto"].fillna("")
        if "link_bayar" not in df.columns:
            df["link_bayar"] = ""
        else:
            df["link_bayar"] = df["link_bayar"].fillna("")
        if "link_faktur_pajak" not in df.columns:
            df["link_faktur_pajak"] = ""
        else:
            df["link_faktur_pajak"] = df["link_faktur_pajak"].fillna("")
        if "jenis_pajak" not in df.columns:
            df["jenis_pajak"] = "Non PKP"
        else:
            df["jenis_pajak"] = df["jenis_pajak"].fillna("Non PKP")
        if "status_lunas" not in df.columns:
            df["status_lunas"] = ""
        # filter search
        if cari:
            kw = cari.lower()
            mask = pd.Series([False] * len(df))
            if "nama_supplier" in df.columns:
                mask = mask | df["nama_supplier"].astype(str).str.lower().str.contains(kw, na=False)
            if "no_invoice" in df.columns:
                mask = mask | df["no_invoice"].astype(str).str.lower().str.contains(kw, na=False)
            if "status_lunas" in df.columns:
                mask = mask | df["status_lunas"].astype(str).str.lower().str.contains(kw, na=False)
            df = df[mask]
        return df
    except Exception:
        cols = ["id", "no_invoice", "nama_supplier", "total_tagihan", "tgl_datang", "jatuh_tempo", "status_lunas", "link_foto", "link_bayar", "link_faktur_pajak", "jenis_pajak"]
        return pd.DataFrame(columns=cols)

# Ambil data supplier untuk cek notifikasi
df_sup_notif = ambil_data_supplier()
notif_jatuh_tempo = []
hari_ini = datetime.date.today()

if not df_sup_notif.empty and "jatuh_tempo" in df_sup_notif.columns:
    for _, row in df_sup_notif.iterrows():
        tgl_jt = row.get("jatuh_tempo")
        if isinstance(tgl_jt, datetime.date):
            try:
                selisih = (tgl_jt - hari_ini).days
                if selisih < 0:
                    notif_jatuh_tempo.append(f"{row['nama_supplier']} sudah jatuh tempo sejak {abs(selisih)} hari lalu.")
                elif selisih <= 3:
                    notif_jatuh_tempo.append(f"{row['nama_supplier']} jatuh tempo dalam {selisih} hari ({tgl_jt}).")
            except Exception:
                pass

# --- FUNGSI GENERATE PDF LAPORAN SUPPLIER ---
def generate_pdf_supplier(df_export, jenis_filter):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=reportlab.lib.pagesizes.A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'), alignment=1, spaceAfter=6)
    style_subtitle = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=15)
    style_cell = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#1E293B'))
    style_cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E293B'))

    elements.append(Paragraph("TOSERBA NURJA BERKAH", style_title))
    elements.append(Paragraph(f"Laporan Data Supplier ({html.escape(str(jenis_filter))}) — Dicetak pada: {datetime.date.today().strftime('%d-%m-%Y')}", style_subtitle))
    elements.append(Spacer(1, 5*mm))

    table_data = [[
        Paragraph("<b>No</b>", style_cell_bold),
        Paragraph("<b>Nama Supplier</b>", style_cell_bold),
        Paragraph("<b>Tagihan (Rp)</b>", style_cell_bold),
        Paragraph("<b>Jenis</b>", style_cell_bold),
        Paragraph("<b>Sistem Bayar</b>", style_cell_bold),
        Paragraph("<b>Jatuh Tempo</b>", style_cell_bold)
    ]] 

    total_tagihan_pdf = 0
    for idx, row in df_export.iterrows():
        tagihan_val = float(row.get('tagihan', 0) or 0)
        total_tagihan_pdf += tagihan_val
        table_data.append([
            Paragraph(str(row.get('no_urut', idx+1)), style_cell),
            Paragraph(html.escape(str(row.get('nama_supplier', ''))), style_cell),
            Paragraph(f"Rp {tagihan_val:,.0f}", style_cell),
            Paragraph(html.escape(str(row.get('jenis_pajak', ''))), style_cell),
            Paragraph(html.escape(str(row.get('sistem_bayar', ''))), style_cell),
            Paragraph(str(row.get('jatuh_tempo', '')), style_cell)
        ])

    table_data.append([
        Paragraph("<b>TOTAL</b>", style_cell_bold),
        Paragraph("", style_cell),
        Paragraph(f"<b>Rp {total_tagihan_pdf:,.0f}</b>", style_cell_bold),
        Paragraph("", style_cell),
        Paragraph("", style_cell),
        Paragraph("", style_cell)
    ])

    col_widths = [15*mm, 60*mm, 35*mm, 20*mm, 25*mm, 25*mm]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor('#0F172A')),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# --- FUNGSI GENERATE PDF LAPORAN RETUR ---
def generate_pdf_retur_custom(df_export, judul_laporan):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=reportlab.lib.pagesizes.A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'), alignment=1, spaceAfter=4)
    style_subtitle = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=15)
    style_cell = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#1E293B'))
    style_cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E293B'))

    elements.append(Paragraph("TOSERBA NURJA BERKAH", style_title))
    elements.append(Paragraph(f"Laporan Barang Retur — {html.escape(str(judul_laporan))}<br/>Dicetak pada: {datetime.date.today().strftime('%d-%m-%Y')}", style_subtitle))
    elements.append(Spacer(1, 5*mm))

    table_data = [[
        Paragraph("<b>Kode</b>", style_cell_bold),
        Paragraph("<b>Nama Barang</b>", style_cell_bold),
        Paragraph("<b>Supplier</b>", style_cell_bold),
        Paragraph("<b>Qty</b>", style_cell_bold),
        Paragraph("<b>HPP (Rp)</b>", style_cell_bold),
        Paragraph("<b>Total (Rp)</b>", style_cell_bold),
        Paragraph("<b>Status</b>", style_cell_bold)
    ]]

    total_nilai_retur = 0
    for idx, row in df_export.iterrows():
        qty_v = float(row.get('qty', 0) or 0)
        hpp_v = float(row.get('hpp', 0) or 0)
        tot_v = float(row.get('total', qty_v * hpp_v) or (qty_v * hpp_v))
        total_nilai_retur += tot_v
        
        table_data.append([
            Paragraph(html.escape(str(row.get('kode', ''))), style_cell),
            Paragraph(html.escape(str(row.get('nama', ''))), style_cell),
            Paragraph(html.escape(str(row.get('supplier', ''))), style_cell),
            Paragraph(str(int(qty_v)), style_cell),
            Paragraph(f"{hpp_v:,.0f}", style_cell),
            Paragraph(f"{tot_v:,.0f}", style_cell),
            Paragraph(html.escape(str(row.get('status', ''))), style_cell)
        ])

    table_data.append([
        Paragraph("<b>TOTAL</b>", style_cell_bold),
        Paragraph("", style_cell),
        Paragraph("", style_cell),
        Paragraph("", style_cell),
        Paragraph("", style_cell),
        Paragraph(f"<b>Rp {total_nilai_retur:,.0f}</b>", style_cell_bold),
        Paragraph("", style_cell)
    ])

    col_widths = [20*mm, 50*mm, 40*mm, 12*mm, 22*mm, 24*mm, 22*mm]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor('#0F172A')),
    ]))

    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# --- SIDEBAR (TOGGLE MODE DI SIDEBAR) ---
with st.sidebar:
    st.markdown("<div style='display:flex;align-items:center;gap:12px'><div style='width:44px;height:44px;background:#2563EB;border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700'>TN</div><div><div style='font-weight:700'>Toserba Nurja Berkah</div><div style='font-size:12px;color:#94A3B8'>Manajemen Retur & Supplier</div></div></div>", unsafe_allow_html=True)
    st.divider()
    theme_choice = st.radio("Pilih Mode", ["Terang", "Gelap"], index=0 if st.session_state.theme == "Terang" else 1, label_visibility="collapsed")
    st.session_state.theme = "Terang" if "Terang" in theme_choice else "Gelap"
    st.divider()
    st.markdown("Menu")
    menu_pilihan = st.radio(
    "",
    [
        "Home","Input Retur","List Retur","Permintaan Barang",
        "Input Pembelian",
        "Data Supplier",
        "Laporan",
        "Pengaturan"
    ],
    index=0)
    st.divider()
    st.markdown("Admin Gudang")
    if st.button("Keluar Sistem", use_container_width=True):
        st.info("Sistem terkunci.")
    st.markdown("<div class='small-muted' style='margin-top:8px'>Tips: Gunakan fitur 'Download' untuk simpan laporan PDF.</div>", unsafe_allow_html=True)

# --- CSS DINAMIS BERDASARKAN TEMA ---
if st.session_state.theme == "Gelap":
    st.markdown('''
        <style>
        .stApp { background-color: #0B1220; color: #F8FAFC; }
        .stButton>button { border-radius:8px; }
        </style>
    ''', unsafe_allow_html=True)
    plotly_template = "plotly_dark"
else:
    st.markdown('''
        <style>
        .stApp { background-color: #F8FAFC; color: #0F172A; }
        .stButton>button { border-radius:8px; }
        </style>
    ''', unsafe_allow_html=True)
    plotly_template = "plotly"

# --- CONSTANTS ---
DAFTAR_SUPPLIER = [
    "Belum Tau",
    "PT ARTABOGA (Hanif)",
    "PT. PANGAN LESTARI (Ratna)",
    "SINAR SURYA SUKSES (Adhit)",
    "PT Borwita Citra Prima (Listin)",
    "PT. SINAR NIAGA SEJAHTERA (Angga)",
    "PT SINARMAS DISTRIBUSI NUSANTARA (Mathias)",
    "PT Eka Artha Buana Darmawan (Unilever)",
    "PT Eka Artha Buana Darmawan (Nestle)",
    "TRI USAHA JAYA",
    "PT BAHAGIA INTRA NIAGA (Onky)",
    "PT Pinus Merah Abadi (Bayuhan)",
    "PT JAPFA FOOD INDONESIA (Uwais)",
    "PT BUKIT MAKMUR INTI ABADI (Badrus)",
    "PT Dinamika Daya Segara",
    "PT SUBUR MITRA SUKSES (Taufiq)",
    "PT. AJINOMOTO SALES INDONESIA (Rosi)",
    "PT TIGARAKSA SENTOSA",
    "PT masamedi intifarm indo (Romeo)",
    "PT DISTRINDO AMAN SEJAHTERA (Agus)",
    "PT BINA SAN PRIMA (Alfia)",
    "PT LIVIA MANURI SEJATI (Aldi)",
    "PT SUMBER BARU NIAGA (Tomi)",
    "PT ANDATU MULIA LESTARI (Muhammad Haris)",
    "PT JAVAS TRIPTA MANDALA (Roby)",
    "PT KHINGGUAN (Ima)",
    "PT TIRTA PRIMA RASA (Dwi)",
    "PT VICTORIA CARE INDONESIA TBK (Saryono)",
    "PT FARMA NIAGA DISTRIBUSINDO",
    "PT TARUNAKUSUMA (Wasik)",
    "PT SEKAWAN KOSMETIK WASANTARA (Ainun)",
    "PT. SAKTISETIA SANTOSA",
    "SINAR SURYA UTAMA",
    "SINAR TERANG",
    "PT. SEMESTANUSTRA DISTRINDO (Imron)",
    "PT SEMESTANUSRTA DISTRINDO",
    "PT PELITA NUSA RAYA (Yulio)",
    "PT Fastra Buana Kanfans (ABDUL)",
    "UD PILAR MAKMUR",
    "PT WIRA SADANA LESTARI (Yono)",
    "PT SAI (Yuli)",
    "Atribut Rezeki",
    "Nova (Ari)",
    "PT SNACK RIzky (Tris)",
    "UD ARJO JAYA (Aldi)",
    "COCA COLA",
    "PT. PERUSAHAAN DAGANG TEMPO",
    "UD KENCONO WUNGU (Opium)",
    "PT CIPTA NIAGA SEMESTA (Dika)",
    "PT CIPTA NIAGA SEMESTA (Yoga)",
    "PT CIPTA NIAGA SEMESTA (Fir)",
    "PUNGGING ELECTRIC",
    "PT Unirama Duta Niaga (Amru)",
    "PT.TUMBAKMAS NIAGA (Hasan)",
    "PT SUPRALITA MANDIRI (Farida)",
    "PT Surya Gemilang Lestari Sentosa (Davina)",
    "PT ASIA PARAMITA INDAH (Andhie)",
    "PT PUJI SURYA INDAH (Qomari)",
    "PT MANOHARA ADIKA DISTRINDO (Deni)",
    "UD SRI REJEKI (Sumar)",
    "CV SINAR ASIA PERKASA (Valentinus)",
    "Toserba Sundra (Kaesang)",
    "PT PANCA PILAR (Aru)",
    "PT INDOMARCO ADI PRIMA",
    "PT KEVINDO PRATAMA PERKASA",
    "PT ARTA DWITUNGGAL ABADI (Febri)",
    "DC NURUL JADID",
    "CV Belva",
    "PT HARSI PANGAN UTAMA",
    "BORNEO",
    "EGIZ UMKM (Ibu Riz)",
    "UD Mentari Jaya Putra",
    "AIRA",
    "PT KIAN RAGAM DISTRIBUTOR",
    "OPIK PUTRA SNACK",
    "PT. PRAKARSA JAYA SENTOSA",
    "HELLO (memenuhi selera anda)",
    "HASAN MEJA",
    "PT CAMPINA ICE CREAM INDUSTRY",
    "Yakult",
    "PT LUKINDARI PERMATA",
    "PT PARIMAS BOGA RAYA",
    "CV.NUGRAHENI KARTIKA SARI DRINGU",
    "PPPPPP",
    "AZKA BAROKAH",
    "REJEKI JAYA",
    "DWIKARYA INDONESIA MANDIRI",
    "PT GOLDEN AICE",
    "BERKAH HS",
    "PT Mitra Pharmasi Jaya",
    "INDOWANGI PARFUM",
    "CV ARGO BENTAR GEMILANG",
    "Atribut Rezeki",
    "Istana Kurma",
    "UD ANUGERAH JAYA PROBOLINGGO",
    "PT SUKANDA DJAYA",
    "PT ULTRAJAYA MILK INDUSTRI & TRADING CO.TBK",
    "Bulog Indonesia",
    "AVERO COLLECTION",
    "TOKO JELITA",
    "CV DAFFA JAYA PRATAMA",
    "PT FKS PANGAN NUSANTRA",
    "HASINUDDIN",
    "TOKO EDDY SURABAYA",
    "PT ANTARMITRA SEMBADA",
    "UD HARIS JAYA PROBOLINGGO",
    "NIKITA JAYA",
    "UD. PUTRA GUNUNG",
    "PT ALAMUIMAS DISTRIBUSI INDONESIA",
    "PT LAMCOS MITRA JAYA",
    "CV. LAJU JAYA MAKMUR",
    "Depaiton",
    "SUMBER PLASTIK JAYA",
    "Esbas Toys",
    "Azka Kaos dan Kain",
    "C.B HANGER",
    "ROSO UTOMO",
    "Lampu Sniper Ecolis",
    "Almandury",
    "PT PENTA VALENT TBK",
    "PT PADMATIRTA WINESA",
    "Umar Faruq",
    "TOKO TAUFIQ",
    "Family Star",
    "PT ENSEVAL PUTERA MEGTRADING TBK",
    "UD NAURA SNACK",
    "CV. SURYA KENCANA ASEMBAKOR",
    "ANUGERAH JAYA",
    "PT. KARYA ANANDA SUKSES",
    "Orlen Roti",
    "MARGA NUSANTARA",
    "Toko Farida",
    "Cv. Primarasa food industri",
    "PT PARIT PADANG GLOBAL",
    "MUSTIKA DIGDAYA",
    "ANGGA PT. ASATU MAKMUR SENTOSA",
    "PT Parama global inspira",
    "MITRA CAMILAN",
    "BSM ELEKTRONIK",
    "GEHEL SNACK PAITON",
    "CV PUMA UTAMA MAKMUR ARTARIA",
    "PT HM SAMPOERNA TBK",
    "REJEKI JAYA",
    "PT PILAR UTAMA DISTRIBUSI",
    "DANHIL",
    "INDOMARCO MAKANAN BAYI",
    "PT MILINIUM",
    "MANDIRI LOGISTI",
    "PT SOLUSI",
    "SUKUN MC. WARTONO",
    "PT KARYA ANADA",
    "TRI USAHA SAKTI ROKOK ESSE",
    "PT USAHA SEKAWAN FARMASI",
    "JAYA SUBUR",
    "PODO JOYO",
    "MAGLI LAJU",
    "UD BERAS",
    "BSU",
    "KOPRASI BUEKA",
    "BOLAMAS",
    "PT SUMBER CIPTA MULTINIAGA",
]
def ambil_data_retur(filter_supplier="SEMUA SUPPLIER", filter_status="SEMUA STATUS", cari=""):
    query = supabase.table("barang_retur").select("*")
    if filter_supplier and filter_supplier != "SEMUA SUPPLIER":
        query = query.eq("supplier", filter_supplier)
    if filter_status and filter_status != "SEMUA STATUS":
        query = query.eq("status", filter_status)
    
    response = query.execute()
    if not response.data:
        return pd.DataFrame(columns=["id", "kode", "nama", "qty", "hpp", "total", "ket", "ed", "supplier", "status", "tgl_input"])

    df = pd.DataFrame(response.data)
    df.columns = [str(c).lower() for c in df.columns]

    if "id" not in df.columns:
        df["id"] = range(1, len(df) + 1)

    if cari:
        kw = cari.lower()
        df = df[
            df["kode"].astype(str).str.lower().str.contains(kw, na=False) |
            df["nama"].astype(str).str.lower().str.contains(kw, na=False) |
            df["ket"].astype(str).str.lower().str.contains(kw, na=False) |
            df["supplier"].astype(str).str.lower().str.contains(kw, na=False) |
            df["status"].astype(str).str.lower().str.contains(kw, na=False)
        ]
    return df

# ==========================================
# CEK DUPLIKAT DATA RETUR
# ==========================================
def cek_retur_sudah_ada(kode, nama, exclude_id=None):
    """
    Cek apakah kombinasi kode barang + nama barang sudah ada.
    Perbandingan kode dan nama dibuat aman terhadap spasi dan huruf besar/kecil.
    exclude_id dipakai saat EDIT agar baris yang sedang diedit tidak dianggap duplikat.
    """
    try:
        kode_cari = str(kode or "").strip()
        nama_cari = " ".join(str(nama or "").strip().lower().split())

        if not kode_cari or not nama_cari:
            return None

        response = (
            supabase
            .table("barang_retur")
            .select("*")
            .eq("kode", kode_cari)
            .execute()
        )

        if not response.data:
            return None

        for data in response.data:
            if exclude_id is not None:
                try:
                    if int(data.get("id")) == int(exclude_id):
                        continue
                except Exception:
                    pass

            nama_db = " ".join(
                str(data.get("nama", "") or "").strip().lower().split()
            )

            if nama_db == nama_cari:
                return data

        return None

    except Exception as e:
        st.error(f"Gagal mengecek data retur: {e}")
        return None


# ==========================================
# POPUP DATA RETUR SUDAH ADA
# ==========================================
@st.dialog("Data Retur Sudah Ada")
def dialog_retur_sudah_ada(data_lama, qty_input=None):
    st.error("Maaf, data barang ini sudah ada di database.")

    kode_lama = data_lama.get("kode", "-")
    nama_lama = data_lama.get("nama", "-")
    qty_lama = data_lama.get("qty", 0)
    hpp_lama = data_lama.get("hpp", 0)

    c1, c2 = st.columns(2)

    with c1:
        st.write("**Kode Barang**")
        st.info(str(kode_lama))

        st.write("**Nama Barang**")
        st.info(str(nama_lama))

    with c2:
        st.write("**Qty Tersimpan**")
        st.warning(f"{qty_lama} PCS")

        if qty_input is not None:
            st.write("**Qty yang Anda Input**")
            st.warning(f"{qty_input} PCS")

        st.write("**HPP Tersimpan**")
        try:
            st.info(format_rp(float(hpp_lama or 0)))
        except Exception:
            st.info(str(hpp_lama))

    st.divider()
    st.warning(
        "Data BARU tidak disimpan agar Qty retur tidak menjadi dobel. "
        "Jika Qty perlu ditambah atau dikoreksi, silakan edit data yang sudah ada di menu List Retur."
    )

    st.markdown("**Pastikan Qty sesuai barang fisik/nota retur sebelum menyimpan perubahan.**")

    if st.button("Tutup", type="primary", use_container_width=True):
        st.rerun()


@st.dialog("Peringatan Jatuh Tempo Supplier")
def dialog_notifikasi_jatuh_tempo():
    st.markdown("Daftar Peringatan Jatuh Tempo")
    if not notif_jatuh_tempo:
        st.success("Tidak ada tagihan supplier yang mendekati atau melewati jatuh tempo.")
    else:
        for n in notif_jatuh_tempo:
            st.markdown(f"- {n}")
    if st.button("Tutup", use_container_width=True, type="primary"):
        st.experimental_rerun()

# --- HEADER ---
head_c1, head_c2 = st.columns([10, 1])
with head_c1:
    st.markdown("<div class='app-header'><div><h1 class='app-title'>Sistem Manajemen Retur & Supplier</h1><div class='app-sub'>Toserba Nurja Berkah — Kelola retur, tagihan, dan laporan</div></div></div>", unsafe_allow_html=True)
with head_c2:
    jml_notif = len(notif_jatuh_tempo)
    label_notif = f"Notifikasi ({jml_notif})" if jml_notif > 0 else "Notifikasi"
    if st.button(label_notif, help="Cek Peringatan Jatuh Tempo"):
        dialog_notifikasi_jatuh_tempo()

st.divider()

# ==========================================
# MENU 0: HOME / DASHBOARD
# ==========================================
if menu_pilihan == "Home":
    st.markdown("Dashboard Ringkasan Sistem")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Selamat datang — ringkasan cepat sistem dan indikator utama.</p>", unsafe_allow_html=True)
    
    df_ret_home = ambil_data_retur()
    df_sup_home = ambil_data_supplier()
    df_inv_home = ambil_data_pembelian()
    
    # Metrics as cards
    col1, col2, col3 = st.columns(3)
    with col1:
        total_retur_val = df_ret_home["total"].sum() if not df_ret_home.empty and "total" in df_ret_home.columns else 0
        st.markdown(f"<div class='metric-card'><div class='card-title'>Total Nilai Barang Retur</div><div style='font-size:18px;font-weight:700'>{format_rp(total_retur_val)}</div><div class='small-muted'>Periode: Semua</div></div>", unsafe_allow_html=True)
    with col2:
        total_tagihan_val = df_sup_home["tagihan"].sum() if not df_sup_home.empty and "tagihan" in df_sup_home.columns else 0
        st.markdown(f"<div class='metric-card'><div class='card-title'>Total Tagihan Supplier</div><div style='font-size:18px;font-weight:700'>{format_rp(total_tagihan_val)}</div><div class='small-muted'>Segera cek jatuh tempo</div></div>", unsafe_allow_html=True)
    with col3:
        total_inv_val = df_inv_home["total_tagihan"].sum() if not df_inv_home.empty and "total_tagihan" in df_inv_home.columns else 0
        st.markdown(f"<div class='metric-card'><div class='card-title'>Total Invoice Pembelian</div><div style='font-size:18px;font-weight:700'>{format_rp(total_inv_val)}</div><div class='small-muted'>Data transaksi masuk</div></div>", unsafe_allow_html=True)

    st.divider()
    
    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        st.markdown("Status Retur Barang")
        if not df_ret_home.empty:
            fig_ret = px.pie(df_ret_home, names='status', values='qty', title="Distribusi Status Retur", template=plotly_template)
            fig_ret.update_layout(margin=dict(t=40,b=10,l=10,r=10))
            st.plotly_chart(fig_ret, use_container_width=True)
        else:
            st.info("Belum ada data retur untuk divisualisasikan.")
            
    with col_ch2:
        st.markdown("Status Pelunasan Invoice")
        if not df_inv_home.empty:
            fig_inv = px.pie(df_inv_home, names='status_lunas', values='total_tagihan', title="Distribusi Pembelian Supplier", template=plotly_template)
            fig_inv.update_layout(margin=dict(t=40,b=10,l=10,r=10))
            st.plotly_chart(fig_inv, use_container_width=True)
        else:
            st.info("Belum ada data invoice pembelian untuk divisualisasikan.")

# ==========================================
# MENU 1: INPUT RETUR
# ==========================================
elif menu_pilihan == "Input Retur":
    st.markdown("Input Barang Retur")
    st.markdown(
        "<p class='small-muted' style='margin-top:-10px'>"
        "Masukkan barang retur baru. Sistem akan mengecek Kode + Nama agar data tidak dobel.</p>",
        unsafe_allow_html=True
    )

    with st.form("form_input_retur", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)

        with fc1:
            f_kode = st.text_input(
                "Kode Barcode / SKU",
                placeholder="Masukkan kode barang"
            )
            f_nama = st.text_input(
                "Nama Barang",
                placeholder="Masukkan nama barang"
            )
            f_qty = st.number_input(
                "Quantity (Qty)",
                min_value=1,
                value=1,
                step=1,
                format="%d"
            )

        with fc2:
            f_hpp = st.number_input(
                "Harga HPP (Rp)",
                min_value=0.0,
                value=0.0,
                step=100.0
            )
            f_ket = st.selectbox(
                "Keterangan Retur",
                ["ED", "Rusak", "Salah PO", "Lebih Bayar", "Lainnya"]
            )
            f_ed = st.text_input(
                "Tanggal ED (jika ada, misal: 31-12-2026 atau -)"
            )

        with fc3:
            f_supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER)
            f_status = st.selectbox(
                "Status Retur",
                ["Pengajuan", "Sedang Diproses", "Sukses"]
            )
            f_tgl = st.date_input(
                "Tanggal Input",
                value=datetime.date.today()
            )

        submit_retur = st.form_submit_button(
            "Simpan Data Retur",
            type="primary",
            use_container_width=True
        )

    if submit_retur:
        kode_input = str(f_kode or "").strip()
        nama_input = str(f_nama or "").strip()
        qty_input = int(f_qty)

        if not kode_input:
            st.warning("Kode barang tidak boleh kosong!")
        elif not nama_input:
            st.warning("Nama barang tidak boleh kosong!")
        elif qty_input <= 0:
            st.warning("Qty harus lebih dari 0!")
        elif float(f_hpp) < 0:
            st.warning("HPP tidak boleh minus!")
        else:
            try:
                # CEK DUPLIKAT SEBELUM INSERT
                data_lama = cek_retur_sudah_ada(
                    kode_input,
                    nama_input
                )

                if data_lama is not None:
                    dialog_retur_sudah_ada(
                        data_lama,
                        qty_input=qty_input
                    )
                else:
                    total_val = qty_input * float(f_hpp)

                    payload_retur = {
                        "kode": kode_input,
                        "nama": nama_input,
                        "qty": qty_input,
                        "hpp": float(f_hpp),
                        "total": float(total_val),
                        "ket": str(f_ket),
                        "ed": str(f_ed or "").strip(),
                        "supplier": str(f_supplier),
                        "status": str(f_status),
                        "tgl_input": str(f_tgl)
                    }

                    success, resp = insert_with_optional_columns(
                        "barang_retur",
                        payload_retur
                    )

                    if success:
                        st.success(
                            f"Data barang retur berhasil disimpan! Qty: {qty_input} PCS"
                        )
                        st.rerun()
                    else:
                        # Helper lama dapat menyimpan data walaupun ada kolom opsional
                        # yang tidak tersedia. Tampilkan pesannya dan refresh.
                        st.warning(str(resp))
                        st.rerun()

            except Exception as e:
                st.error(f"Gagal menyimpan data retur: {e}")

    st.divider()
    st.markdown("Riwayat Retur Terbaru")
    df_history = ambil_data_retur()
    if not df_history.empty:
        st.dataframe(
            df_history.tail(10).reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Belum ada data retur.")

# ==========================================
# MENU 2: LIST RETUR
# ==========================================
elif menu_pilihan == "List Retur":
    st.markdown("List Data Retur & Manajemen Edit")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Filter data retur berdasarkan supplier/status, edit langsung tabel, simpan perubahan, atau cetak laporan PDF per supplier.</p>", unsafe_allow_html=True)
    
    fl_c1, fl_c2, fl_c3 = st.columns(3)
    with fl_c1:
        opsi_supp_filter = ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER
        pilih_sup_filter = st.selectbox("Filter Supplier", opsi_supp_filter)
    with fl_c2:
        pilih_status_filter = st.selectbox("Filter Status", ["SEMUA STATUS", "Pengajuan", "Sedang Diproses", "Sukses"])
    with fl_c3:
        cari_retur_input = st.text_input("Cari Data Retur (Kode / Nama / Keterangan)")

    df_retur_view = ambil_data_retur(filter_supplier=pilih_sup_filter, filter_status=pilih_status_filter, cari=cari_retur_input)

    if not df_retur_view.empty:
        safe_name = pilih_sup_filter.replace(" ", "_").replace("/", "_")
        pdf_bytes = generate_pdf_retur_custom(df_retur_view, pilih_sup_filter)
        st.download_button(
            label=f"Download Laporan PDF ({pilih_sup_filter})",
            data=pdf_bytes,
            file_name=f"Laporan_Retur_{safe_name}_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("Edit Data Retur")
        edited_df_retur = st.data_editor(
            df_retur_view,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small", disabled=True),
                "kode": st.column_config.TextColumn("Kode Barcode/SKU", width="medium"),
                "nama": st.column_config.TextColumn("Nama Barang", width="large"),
                "qty": st.column_config.NumberColumn("Qty", min_value=0, width="small"),
                "hpp": st.column_config.NumberColumn("HPP (Rp)", format="Rp %'d", width="medium"),
                "total": st.column_config.NumberColumn("Total (Rp)", format="Rp %'d", width="medium", disabled=True),
                "ket": st.column_config.SelectboxColumn("Keterangan", options=["ED", "Rusak", "Salah PO", "Lebih Bayar", "Lainnya"], required=True, width="small"),
                "ed": st.column_config.TextColumn("Tanggal ED", width="small"),
                "supplier": st.column_config.SelectboxColumn("Supplier", options=DAFTAR_SUPPLIER, required=True, width="large"),
                "status": st.column_config.SelectboxColumn("Status", options=["Pengajuan", "Sedang Diproses", "Sukses"], required=True, width="medium"),
                "tgl_input": st.column_config.TextColumn("Tanggal Input", width="small", disabled=True),
            },
            disabled=["id", "total", "tgl_input"],
            hide_index=True,
            use_container_width=True,
            key="editor_tabel_retur_v2"
        )

        st.markdown("Aksi Data Retur")
        list_retur_ids = df_retur_view["id"].tolist()
        selected_retur_ids = st.multiselect("Pilih ID Retur (untuk Hapus):", options=list_retur_ids, key="multiselect_retur_id")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("Simpan Perubahan Data Retur", type="primary", use_container_width=True):
                count_upd_retur = 0
                for _, row in edited_df_retur.iterrows():
                    orig_row = df_retur_view.loc[df_retur_view["id"] == row["id"]]
                    if not orig_row.empty:
                        orig = orig_row.iloc[0]
                        new_qty = float(row["qty"])
                        new_hpp = float(row["hpp"])
                        new_total = new_qty * new_hpp
                        
                        kode_edit = str(row["kode"] or "").strip()
                        nama_edit = str(row["nama"] or "").strip()

                        if not kode_edit or not nama_edit:
                            st.warning(f"ID {row['id']}: Kode dan nama barang wajib diisi.")
                            continue

                        if new_qty <= 0:
                            st.warning(f"ID {row['id']}: Qty harus lebih dari 0.")
                            continue

                        duplikat_edit = cek_retur_sudah_ada(
                            kode_edit,
                            nama_edit,
                            exclude_id=int(row["id"])
                        )

                        if duplikat_edit is not None:
                            st.error(
                                f"ID {row['id']}: Kode + Nama barang sudah ada pada ID {duplikat_edit.get('id')}. "
                                "Perubahan tidak disimpan agar data tidak dobel."
                            )
                            continue

                        if (
                            kode_edit != str(orig.get("kode", "")).strip() or
                            nama_edit != str(orig.get("nama", "")).strip() or
                            new_qty != float(orig.get("qty", 0) or 0) or
                            new_hpp != float(orig.get("hpp", 0) or 0) or
                            str(row["ket"]) != str(orig.get("ket", "")) or
                            str(row["ed"]) != str(orig.get("ed", "")) or
                            str(row["supplier"]) != str(orig.get("supplier", "")) or
                            str(row["status"]) != str(orig.get("status", ""))
                        ):
                            try:
                                supabase.table("barang_retur").update({
                                    "kode": kode_edit,
                                    "nama": nama_edit,
                                    "qty": int(new_qty),
                                    "hpp": float(new_hpp),
                                    "total": float(new_total),
                                    "ket": str(row["ket"]),
                                    "ed": str(row["ed"]),
                                    "supplier": str(row["supplier"]),
                                    "status": str(row["status"])
                                }).eq("id", int(row["id"])).execute()
                                count_upd_retur += 1
                            except Exception as e:
                                st.error(f"Gagal memperbarui ID {row['id']}: {e}")
                if count_upd_retur > 0:
                    st.success(f"Berhasil memperbarui {count_upd_retur} data retur!")
                    st.experimental_rerun()
                else:
                    st.info("Tidak ada perubahan data retur yang terdeteksi.")
        with col_r2:
            if st.button("Hapus Retur Terpilih", type="secondary", use_container_width=True):
                if not selected_retur_ids:
                    st.warning("Pilih minimal satu ID retur yang ingin dihapus!")
                else:
                    for rid in selected_retur_ids:
                        try:
                            supabase.table("barang_retur").delete().eq("id", int(float(str(rid)))).execute()
                        except (ValueError, TypeError, Exception):
                            continue
                    st.success("Data retur terpilih berhasil dihapus!")
                    st.experimental_rerun()
    else:
        st.info("Tidak ada data retur yang ditemukan sesuai filter.")
# ==========================================
# MENU: PERMINTAAN BARANG
# ==========================================
elif menu_pilihan == "Permintaan Barang":

    st.markdown("Permintaan Barang")
    st.markdown(
        "<p class='small-muted' style='margin-top:-10px'>"
        "Pencatatan permintaan barang dari pramuniaga."
        "</p>",
        unsafe_allow_html=True
    )

    # ------------------------------------------
    # FORM INPUT PERMINTAAN
    # ------------------------------------------
    with st.form("form_permintaan_barang", clear_on_submit=True):

        pc1, pc2 = st.columns(2)

        with pc1:
            p_kode = st.text_input(
                "Kode Barang",
                placeholder="Contoh: 8999999999999"
            )

            p_nama = st.text_input(
                "Nama Barang",
                placeholder="Contoh: Indomie Goreng"
            )

            p_jumlah = st.number_input(
                "Jumlah",
                min_value=1,
                value=1,
                step=1
            )

        with pc2:

            p_satuan = st.selectbox(
                "Satuan",
                ["PCS", "BOX", "PACK", "DUS"]
            )

            p_pramuniaga = st.text_input(
                "Nama Pramuniaga / Peminta",
                placeholder="Masukkan nama pramuniaga"
            )

            p_tanggal = st.date_input(
                "Tanggal Permintaan",
                value=datetime.date.today()
            )

        p_keterangan = st.text_area(
            "Keterangan",
            placeholder="Contoh: Stok rak habis / permintaan tambahan..."
        )

        submit_permintaan = st.form_submit_button(
            "Simpan Permintaan Barang",
            type="primary",
            use_container_width=True
        )

        if submit_permintaan:

            if not p_kode:
                st.warning("Kode barang tidak boleh kosong!")

            elif not p_nama:
                st.warning("Nama barang tidak boleh kosong!")

            elif not p_pramuniaga:
                st.warning("Nama pramuniaga tidak boleh kosong!")

            else:

                payload_permintaan = {
                    "kode_barang": str(p_kode).strip(),
                    "nama_barang": str(p_nama).strip(),
                    "jumlah": int(p_jumlah),
                    "satuan": str(p_satuan),
                    "nama_pramuniaga": str(p_pramuniaga).strip(),
                    "tanggal_permintaan": str(p_tanggal),
                    "status": "Diajukan",
                    "keterangan": str(p_keterangan).strip()
                }

                try:

                    response = supabase.table(
                        "permintaan_barang"
                    ).insert(
                        payload_permintaan
                    ).execute()

                    st.success(
                        "Permintaan barang berhasil disimpan!"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Gagal menyimpan permintaan barang: {e}"
                    )

    st.divider()

    # ------------------------------------------
    # DAFTAR PERMINTAAN
    # ------------------------------------------
    st.markdown("### Daftar Permintaan Barang")

    pc_filter1, pc_filter2 = st.columns(2)

    with pc_filter1:
        cari_permintaan = st.text_input(
            "Cari Barang / Kode / Pramuniaga",
            key="cari_permintaan"
        )

    with pc_filter2:
        filter_status_permintaan = st.selectbox(
            "Filter Status",
            [
                "SEMUA STATUS",
                "Diajukan",
                "Diproses",
                "Terpenuhi",
                "Ditolak"
            ],
            key="filter_status_permintaan"
        )

    try:

        query_permintaan = supabase.table(
            "permintaan_barang"
        ).select("*").order(
            "id",
            desc=True
        )

        if filter_status_permintaan != "SEMUA STATUS":
            query_permintaan = query_permintaan.eq(
                "status",
                filter_status_permintaan
            )

        response_permintaan = query_permintaan.execute()

        if response_permintaan.data:

            df_permintaan = pd.DataFrame(
                response_permintaan.data
            )

            # --------------------------------------
            # SEARCH
            # --------------------------------------
            if cari_permintaan:

                keyword = cari_permintaan.lower()

                mask = (
                    df_permintaan["kode_barang"]
                    .astype(str)
                    .str.lower()
                    .str.contains(keyword, na=False)
                    |
                    df_permintaan["nama_barang"]
                    .astype(str)
                    .str.lower()
                    .str.contains(keyword, na=False)
                    |
                    df_permintaan["nama_pramuniaga"]
                    .astype(str)
                    .str.lower()
                    .str.contains(keyword, na=False)
                )

                df_permintaan = df_permintaan[mask]

            # --------------------------------------
            # FORMAT TABEL
            # --------------------------------------
            if not df_permintaan.empty:

                kolom_tampil = [
                    "id",
                    "kode_barang",
                    "nama_barang",
                    "jumlah",
                    "satuan",
                    "nama_pramuniaga",
                    "tanggal_permintaan",
                    "status",
                    "keterangan"
                ]

                df_tampil = df_permintaan[
                    [
                        kolom
                        for kolom in kolom_tampil
                        if kolom in df_permintaan.columns
                    ]
                ].copy()

                st.dataframe(
                    df_tampil,
                    column_config={
                        "id": st.column_config.NumberColumn(
                            "ID",
                            width="small"
                        ),

                        "kode_barang": st.column_config.TextColumn(
                            "Kode Barang",
                            width="medium"
                        ),

                        "nama_barang": st.column_config.TextColumn(
                            "Nama Barang",
                            width="large"
                        ),

                        "jumlah": st.column_config.NumberColumn(
                            "Jumlah",
                            width="small"
                        ),

                        "satuan": st.column_config.TextColumn(
                            "Satuan",
                            width="small"
                        ),

                        "nama_pramuniaga": st.column_config.TextColumn(
                            "Pramuniaga",
                            width="medium"
                        ),

                        "tanggal_permintaan": st.column_config.DateColumn(
                            "Tanggal",
                            width="medium"
                        ),

                        "status": st.column_config.TextColumn(
                            "Status",
                            width="medium"
                        ),

                        "keterangan": st.column_config.TextColumn(
                            "Keterangan",
                            width="large"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )

                st.markdown("### Kelola Permintaan")

                # --------------------------------------
                # PILIH DATA
                # --------------------------------------
                pilihan_permintaan = df_permintaan.apply(
                    lambda row:
                    f"ID: {row['id']} | "
                    f"{row['nama_barang']} | "
                    f"{row['jumlah']} {row['satuan']} | "
                    f"{row['nama_pramuniaga']}",
                    axis=1
                ).tolist()

                selected_permintaan = st.selectbox(
                    "Pilih Permintaan",
                    pilihan_permintaan,
                    key="selected_permintaan"
                )

                if selected_permintaan:

                    selected_id = int(
                        selected_permintaan
                        .split("|")[0]
                        .replace("ID:", "")
                        .strip()
                    )

                    data_perm = df_permintaan[
                        df_permintaan["id"] == selected_id
                    ].iloc[0]

                    c_status, c_hapus = st.columns(2)

                    # ----------------------------------
                    # UPDATE STATUS
                    # ----------------------------------
                    with c_status:

                        status_baru = st.selectbox(
                            "Ubah Status",
                            [
                                "Diajukan",
                                "Diproses",
                                "Terpenuhi",
                                "Ditolak"
                            ],
                            index=[
                                "Diajukan",
                                "Diproses",
                                "Terpenuhi",
                                "Ditolak"
                            ].index(
                                data_perm.get(
                                    "status",
                                    "Diajukan"
                                )
                            ),
                            key="status_baru_permintaan"
                        )

                        if st.button(
                            "Update Status",
                            type="primary",
                            use_container_width=True
                        ):

                            try:

                                supabase.table(
                                    "permintaan_barang"
                                ).update({
                                    "status": status_baru
                                }).eq(
                                    "id",
                                    selected_id
                                ).execute()

                                st.success(
                                    "Status berhasil diperbarui!"
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Gagal memperbarui status: {e}"
                                )

                    # ----------------------------------
                    # HAPUS
                    # ----------------------------------
                    with c_hapus:

                        st.markdown(
                            "<br>",
                            unsafe_allow_html=True
                        )

                        if st.button(
                            "Hapus Permintaan",
                            type="secondary",
                            use_container_width=True
                        ):

                            try:

                                supabase.table(
                                    "permintaan_barang"
                                ).delete().eq(
                                    "id",
                                    selected_id
                                ).execute()

                                st.success(
                                    "Permintaan berhasil dihapus!"
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Gagal menghapus data: {e}"
                                )

            else:

                st.info(
                    "Tidak ada permintaan yang sesuai."
                )

        else:

            st.info(
                "Belum ada permintaan barang."
            )

    except Exception as e:

        st.error(
            f"Gagal mengambil data permintaan barang: {e}"
        )
# ==========================================
# MENU 3: INPUT PEMBELIAN / INVOICE
# ==========================================
elif menu_pilihan == "Input Pembelian":
    st.markdown("Pencatatan & Manajemen Invoice Supplier")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Formulir pencatatan faktur/invoice barang masuk lengkap dengan upload bukti nota, bukti pembayaran, dan faktur pajak.</p>", unsafe_allow_html=True)
    
    # Ambil data terbaru (digunakan juga untuk mengetahui kolom yang tersedia secara implisit)
    df_inv_view = ambil_data_pembelian("")
    
    # Buat Tabs untuk memisahkan Menu Tambah dan Edit/Hapus
    tab_tambah, tab_edit = st.tabs(["Tambah Pembelian Baru", "Edit / Hapus Pembelian"])
    
    # ================= TAB 1: TAMBAH PEMBELIAN =================
    with tab_tambah:
        with st.form("form_input_pembelian", clear_on_submit=True):
            ic1, ic2 = st.columns(2)
            with ic1:
                i_invoice = st.text_input("Nomor Invoice / Faktur")
                i_supplier = st.selectbox("Nama Supplier", DAFTAR_SUPPLIER, key="inv_sup_baru")
                i_tagihan = st.number_input("Total Tagihan / Nilai Faktur (Rp)", min_value=0.0, value=0.0, step=1000.0)
                i_jenis_pajak = st.selectbox("Jenis Pajak", ["Non PKP", "PKP"], index=0)
            with ic2:
                i_tgl_datang = st.date_input("Tanggal Datang Barang", value=datetime.date.today())
                i_jatuh_tempo = st.date_input("Tanggal Jatuh Tempo", value=datetime.date.today() + datetime.timedelta(days=30))
                i_status_lunas = st.selectbox("Status Pelunasan", ["Belum Lunas", "Lunas", "Sebagian"], key="inv_stat_baru")
                
            st.markdown("---")
            uc1, uc2, uc3 = st.columns([1,1,1])
            with uc1:
                i_file_nota = st.file_uploader("Upload Foto/File Bukti Nota (Opsional)", type=["png", "jpg", "jpeg", "pdf"], key="up_nota")
            with uc2:
                i_file_bayar = st.file_uploader("Upload Foto/File Bukti Pembayaran (Opsional)", type=["png", "jpg", "jpeg", "pdf"], key="up_bayar")
            with uc3:
                i_file_faktur_pajak = st.file_uploader("Upload Foto/File Faktur Pajak (Opsional)", type=["png", "jpg", "jpeg", "pdf"], key="up_faktur_pajak")
            
            submit_inv = st.form_submit_button("Simpan Data Pembelian", type="primary")
            if submit_inv:
                if not i_invoice:
                    st.warning("Nomor invoice tidak boleh kosong!")
                else:
                    try:
                        public_url_nota = ""
                        public_url_bayar = ""
                        public_url_faktur_pajak = ""
                        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_invoice = str(i_invoice).replace("/", "_")

                        if i_file_nota is not None:
                            ext_nota = i_file_nota.name.split(".")[-1]
                            name_nota = f"nota_{timestamp_str}_{safe_invoice}.{ext_nota}"
                            supabase.storage.from_("bukti_pembelian").upload(
                                path=name_nota,
                                file=i_file_nota.getvalue(),
                                file_options={"content-type": i_file_nota.type}
                            )
                            res_nota = supabase.storage.from_("bukti_pembelian").get_public_url(name_nota)
                            public_url_nota = extract_public_url(res_nota)

                        if i_file_bayar is not None:
                            ext_bayar = i_file_bayar.name.split(".")[-1]
                            name_bayar = f"bayar_{timestamp_str}_{safe_invoice}.{ext_bayar}"
                            supabase.storage.from_("bukti_pembelian").upload(
                                path=name_bayar,
                                file=i_file_bayar.getvalue(),
                                file_options={"content-type": i_file_bayar.type}
                            )
                            res_bayar = supabase.storage.from_("bukti_pembelian").get_public_url(name_bayar)
                            public_url_bayar = extract_public_url(res_bayar)

                        if i_file_faktur_pajak is not None:
                            ext_fp = i_file_faktur_pajak.name.split(".")[-1]
                            name_fp = f"faktur_pajak_{timestamp_str}_{safe_invoice}.{ext_fp}"
                            supabase.storage.from_("bukti_pembelian").upload(
                                path=name_fp,
                                file=i_file_faktur_pajak.getvalue(),
                                file_options={"content-type": i_file_faktur_pajak.type}
                            )
                            res_fp = supabase.storage.from_("bukti_pembelian").get_public_url(name_fp)
                            public_url_faktur_pajak = extract_public_url(res_fp)

                        payload_inv = {
                            "no_invoice": str(i_invoice),
                            "nama_supplier": str(i_supplier),
                            "total_tagihan": float(i_tagihan),
                            "tgl_datang": str(i_tgl_datang),
                            "jatuh_tempo": str(i_jatuh_tempo),
                            "status_lunas": str(i_status_lunas),
                            "link_foto": str(public_url_nota),
                            "link_bayar": str(public_url_bayar),
                            "link_faktur_pajak": str(public_url_faktur_pajak),
                            "jenis_pajak": str(i_jenis_pajak)
                        }

                        # coba insert; jika kolom tidak ada, fungsi helper akan menangani fallback
                        success, resp = insert_with_optional_columns("data_pembelian", payload_inv)
                        if success:
                            st.success("Data pembelian berhasil disimpan!")
                            st.experimental_rerun()
                        else:
                            # resp bisa berupa pesan peringatan kalau kolom dihapus saat insert
                            st.warning(str(resp))
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan data pembelian: {e}")

    # ================= TAB 2: EDIT / HAPUS PEMBELIAN =================
    with tab_edit:
        st.markdown("Form Edit & Hapus Data Pembelian")
        if df_inv_view.empty:
            st.info("Belum ada data pembelian untuk diedit.")
        else:
            pilihan_data = df_inv_view.apply(lambda row: f"ID: {row.get('id', '')} | Inv: {row.get('no_invoice', '')} | {row.get('nama_supplier','')}", axis=1).tolist()
            selected_str = st.selectbox("Pilih Data Pembelian yang ingin di-Edit/Hapus", pilihan_data)
            
            if selected_str:
                selected_id = int(selected_str.split("|")[0].replace("ID:", "").strip())
                data_terpilih = df_inv_view[df_inv_view["id"] == selected_id].iloc[0]

                # ambil link yang sudah tersimpan (jika ada)
                current_link_nota = data_terpilih.get("link_foto", "") if "link_foto" in data_terpilih else ""
                current_link_bayar = data_terpilih.get("link_bayar", "") if "link_bayar" in data_terpilih else ""
                current_link_faktur_pajak = data_terpilih.get("link_faktur_pajak", "") if "link_faktur_pajak" in data_terpilih else ""
                current_jenis_pajak = data_terpilih.get("jenis_pajak", "Non PKP") if "jenis_pajak" in data_terpilih else "Non PKP"
                
                with st.form("form_edit_pembelian"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_invoice = st.text_input("Nomor Invoice / Faktur", value=str(data_terpilih.get("no_invoice", "")))
                        sup_idx = DAFTAR_SUPPLIER.index(data_terpilih.get("nama_supplier")) if data_terpilih.get("nama_supplier") in DAFTAR_SUPPLIER else 0
                        e_supplier = st.selectbox("Nama Supplier", DAFTAR_SUPPLIER, index=sup_idx, key="edit_sup")
                        e_tagihan = st.number_input("Total Tagihan / Nilai Faktur (Rp)", min_value=0.0, value=float(data_terpilih.get("total_tagihan", 0) or 0), step=1000.0)
                        e_jenis_pajak = st.selectbox("Jenis Pajak", ["Non PKP", "PKP"], index=0 if current_jenis_pajak == "Non PKP" else 1)
                    with ec2:
                        try:
                            parsed_tgl_datang = datetime.datetime.strptime(str(data_terpilih.get("tgl_datang", "")), "%Y-%m-%d").date() if pd.notna(data_terpilih.get("tgl_datang", "")) else datetime.date.today()
                        except Exception:
                            parsed_tgl_datang = datetime.date.today()
                        e_tgl_datang = st.date_input("Tanggal Datang Barang", value=parsed_tgl_datang)
                        
                        try:
                            parsed_jatuh_tempo = datetime.datetime.strptime(str(data_terpilih.get("jatuh_tempo", "")), "%Y-%m-%d").date() if pd.notna(data_terpilih.get("jatuh_tempo", "")) else datetime.date.today()
                        except Exception:
                            parsed_jatuh_tempo = datetime.date.today()
                        e_jatuh_tempo = st.date_input("Tanggal Jatuh Tempo", value=parsed_jatuh_tempo)
                        
                        stat_list = ["Belum Lunas", "Lunas", "Sebagian"]
                        stat_idx = stat_list.index(data_terpilih.get("status_lunas")) if data_terpilih.get("status_lunas") in stat_list else 0
                        e_status_lunas = st.selectbox("Status Pelunasan", stat_list, index=stat_idx, key="edit_stat")
                    
                    # show current files (preview for images, link for PDFs)
                    st.markdown("Bukti Saat Ini")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if current_link_nota:
                            if str(current_link_nota).lower().endswith(".pdf"):
                                st.markdown(f"[Lihat / Unduh Bukti Nota]({current_link_nota})")
                            else:
                                try:
                                    st.image(current_link_nota, width=200, caption="Bukti Nota (saat ini)")
                                except Exception:
                                    st.markdown(f"[Lihat / Unduh Bukti Nota]({current_link_nota})")
                        else:
                            st.markdown("Tidak ada bukti nota tersimpan.")
                    with c2:
                        if current_link_bayar:
                            if str(current_link_bayar).lower().endswith(".pdf"):
                                st.markdown(f"[Lihat / Unduh Bukti Pembayaran]({current_link_bayar})")
                            else:
                                try:
                                    st.image(current_link_bayar, width=200, caption="Bukti Pembayaran (saat ini)")
                                except Exception:
                                    st.markdown(f"[Lihat / Unduh Bukti Pembayaran]({current_link_bayar})")
                        else:
                            st.markdown("Tidak ada bukti pembayaran tersimpan.")
                    with c3:
                        if current_link_faktur_pajak:
                            if str(current_link_faktur_pajak).lower().endswith(".pdf"):
                                st.markdown(f"[Lihat / Unduh Faktur Pajak]({current_link_faktur_pajak})")
                            else:
                                try:
                                    st.image(current_link_faktur_pajak, width=200, caption="Faktur Pajak (saat ini)")
                                except Exception:
                                    st.markdown(f"[Lihat / Unduh Faktur Pajak]({current_link_faktur_pajak})")
                        else:
                            st.markdown("Tidak ada faktur pajak tersimpan.")

                    st.markdown("---")
                    st.markdown("Upload Bukti Baru (opsional)")
                    uu1, uu2, uu3 = st.columns([1,1,1])
                    with uu1:
                        e_file_nota = st.file_uploader("Upload Bukti Nota (png/jpg/pdf) - opsional", type=["png", "jpg", "jpeg", "pdf"], key="edit_up_nota")
                    with uu2:
                        e_file_bayar = st.file_uploader("Upload Bukti Pembayaran (png/jpg/pdf) - opsional", type=["png", "jpg", "jpeg", "pdf"], key="edit_up_bayar")
                    with uu3:
                        e_file_faktur_pajak = st.file_uploader("Upload Faktur Pajak (png/jpg/pdf) - opsional", type=["png", "jpg", "jpeg", "pdf"], key="edit_up_faktur_pajak")

                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        submit_update = st.form_submit_button("Update / Simpan Perubahan", type="primary", use_container_width=True)
                    with btn_col2:
                        submit_delete = st.form_submit_button("Hapus Data Ini", type="secondary", use_container_width=True)
                        
                    if submit_update:
                        try:
                            public_url_nota = current_link_nota or ""
                            public_url_bayar = current_link_bayar or ""
                            public_url_faktur_pajak = current_link_faktur_pajak or ""
                            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            safe_invoice = str(e_invoice).replace("/", "_")

                            if e_file_nota is not None:
                                ext_nota = e_file_nota.name.split(".")[-1]
                                name_nota = f"nota_{timestamp_str}_{safe_invoice}.{ext_nota}"
                                supabase.storage.from_("bukti_pembelian").upload(
                                    path=name_nota,
                                    file=e_file_nota.getvalue(),
                                    file_options={"content-type": e_file_nota.type}
                                )
                                res_nota = supabase.storage.from_("bukti_pembelian").get_public_url(name_nota)
                                public_url_nota = extract_public_url(res_nota)

                            if e_file_bayar is not None:
                                ext_bayar = e_file_bayar.name.split(".")[-1]
                                name_bayar = f"bayar_{timestamp_str}_{safe_invoice}.{ext_bayar}"
                                supabase.storage.from_("bukti_pembelian").upload(
                                    path=name_bayar,
                                    file=e_file_bayar.getvalue(),
                                    file_options={"content-type": e_file_bayar.type}
                                )
                                res_bayar = supabase.storage.from_("bukti_pembelian").get_public_url(name_bayar)
                                public_url_bayar = extract_public_url(res_bayar)

                            if e_file_faktur_pajak is not None:
                                ext_fp = e_file_faktur_pajak.name.split(".")[-1]
                                name_fp = f"faktur_pajak_{timestamp_str}_{safe_invoice}.{ext_fp}"
                                supabase.storage.from_("bukti_pembelian").upload(
                                    path=name_fp,
                                    file=e_file_faktur_pajak.getvalue(),
                                    file_options={"content-type": e_file_faktur_pajak.type}
                                )
                                res_fp = supabase.storage.from_("bukti_pembelian").get_public_url(name_fp)
                                public_url_faktur_pajak = extract_public_url(res_fp)

                            payload_update = {
                                "no_invoice": str(e_invoice),
                                "nama_supplier": str(e_supplier),
                                "total_tagihan": float(e_tagihan),
                                "tgl_datang": str(e_tgl_datang),
                                "jatuh_tempo": str(e_jatuh_tempo),
                                "status_lunas": str(e_status_lunas),
                                "link_foto": str(public_url_nota),
                                "link_bayar": str(public_url_bayar),
                                "link_faktur_pajak": str(public_url_faktur_pajak),
                                "jenis_pajak": str(e_jenis_pajak)
                            }

                            success_upd, resp_upd = update_with_optional_columns("data_pembelian", payload_update, "id", selected_id)
                            if success_upd:
                                st.success("Data pembelian berhasil diperbarui!")
                                st.experimental_rerun()
                            else:
                                st.warning(str(resp_upd))
                                st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Gagal mengupdate data: {e}")
                            
                    if submit_delete:
                        try:
                            supabase.table("data_pembelian").delete().eq("id", selected_id).execute()
                            st.success("Data pembelian berhasil dihapus!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Gagal menghapus data: {e}")

    st.divider()
    st.markdown("Daftar Invoice & Pembelian Masuk")
    
    # --- FILTER PENCARIAN & TABEL VIEW ---
    fc_inv1, fc_inv2, fc_inv3 = st.columns(3)
    with fc_inv1:
        cari_inv = st.text_input("Cari (No Invoice / Nama Supplier)")
    with fc_inv2:
        filter_tgl_tipe = st.selectbox("Filter Berdasarkan Tanggal", ["Tanpa Filter Tanggal", "Tanggal Datang", "Jatuh Tempo"])
    with fc_inv3:
        if filter_tgl_tipe != "Tanpa Filter Tanggal":
            rentang_tgl = st.date_input("Pilih Rentang Tanggal", value=(datetime.date.today() - datetime.timedelta(days=30), datetime.date.today() + datetime.timedelta(days=30)))
        else:
            rentang_tgl = None

    df_inv_filtered = ambil_data_pembelian(cari_inv)

    if not df_inv_filtered.empty and filter_tgl_tipe != "Tanpa Filter Tanggal" and isinstance(rentang_tgl, tuple) and len(rentang_tgl) == 2:
        tgl_mulai, tgl_selesai = rentang_tgl
        kolom_target_tgl = "tgl_datang" if filter_tgl_tipe == "Tanggal Datang" else "jatuh_tempo"
        
        if kolom_target_tgl in df_inv_filtered.columns:
            df_inv_filtered[kolom_target_tgl] = pd.to_datetime(df_inv_filtered[kolom_target_tgl], errors="coerce").dt.date
            df_inv_filtered = df_inv_filtered[
                (df_inv_filtered[kolom_target_tgl] >= tgl_mulai) & 
                (df_inv_filtered[kolom_target_tgl] <= tgl_selesai)
            ]
    
    if not df_inv_filtered.empty:
        st.dataframe(
            df_inv_filtered,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "no_invoice": st.column_config.TextColumn("No Invoice", width="medium"),
                "nama_supplier": st.column_config.TextColumn("Supplier", width="large"),
                "jenis_pajak": st.column_config.TextColumn("Jenis Pajak", width="small"),
                "total_tagihan": st.column_config.NumberColumn("Total Tagihan (Rp)", format="Rp %'d", width="medium"),
                "tgl_datang": st.column_config.DateColumn("Tgl Datang", width="small"),
                "jatuh_tempo": st.column_config.DateColumn("Tgl Jatuh Tempo", width="small"),
                "status_lunas": st.column_config.TextColumn("Status", width="small"),
                "link_foto": st.column_config.LinkColumn("Bukti Nota", display_text="Download Nota", width="medium"),
                "link_bayar": st.column_config.LinkColumn("Bukti Bayar", display_text="Download Bukti Bayar", width="medium"),
                "link_faktur_pajak": st.column_config.LinkColumn("Faktur Pajak", display_text="Download Faktur Pajak", width="medium"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        grand_total_nilai = df_inv_filtered["total_tagihan"].sum() if "total_tagihan" in df_inv_filtered.columns else 0
        col_gt1, col_gt2 = st.columns([2, 1])
        with col_gt2:
            st.markdown(f"<div class='metric-card'><div class='card-title'>Grand Total Tagihan</div><div style='font-size:18px;font-weight:700'>{format_rp(grand_total_nilai)}</div></div>", unsafe_allow_html=True)
    else:
        st.info("Tidak ada data pembelian tercatat yang sesuai dengan filter.")

# ==========================================
# MENU 4: DATA SUPPLIER
# ==========================================
elif menu_pilihan == "Data Supplier":
    st.markdown("Manajemen Data Supplier & Tagihan")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Pengelolaan informasi profil supplier, status pajak, sistem pembayaran, dan monitoring tagihan.</p>", unsafe_allow_html=True)
    
    cari_sup = st.text_input("Cari Supplier (Nama / Jenis Pajak / Sistem Bayar)")
    df_sup_view = ambil_data_supplier(cari_sup)
    
    if not df_sup_view.empty:
        pdf_sup_bytes = generate_pdf_supplier(df_sup_view, "Semua Supplier Aktif")
        st.download_button(
            label="Download Laporan PDF Data Supplier",
            data=pdf_sup_bytes,
            file_name=f"Laporan_Supplier_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        edited_df_sup = st.data_editor(
            df_sup_view,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small", disabled=True),
                "no_urut": st.column_config.NumberColumn("No Urut", width="small"),
                "nama_supplier": st.column_config.TextColumn("Nama Supplier", width="large"),
                "tagihan": st.column_config.NumberColumn("Tagihan (Rp)", format="Rp %'d", width="medium"),
                "jenis_pajak": st.column_config.TextColumn("Jenis Pajak", width="small"),
                "sistem_bayar": st.column_config.TextColumn("Sistem Bayar", width="medium"),
                "jatuh_tempo": st.column_config.DateColumn("Jatuh Tempo", width="medium"),
            },
            disabled=["id"],
            hide_index=True,
            use_container_width=True,
            key="editor_tabel_supplier"
        )
        
        if st.button("Simpan Perubahan Supplier", type="primary"):
            count_upd_sup = 0
            for _, row in edited_df_sup.iterrows():
                orig_row = df_sup_view.loc[df_sup_view["id"] == row["id"]]
                if not orig_row.empty:
                    orig = orig_row.iloc[0]
                    try:
                        if (
                            str(row["nama_supplier"]) != str(orig.get("nama_supplier", "")) or
                            float(row["tagihan"]) != float(orig.get("tagihan", 0) or 0) or
                            str(row["sistem_bayar"]) != str(orig.get("sistem_bayar", ""))
                        ):
                            # update only allowed fields
                            supabase.table("data_supplier").update({
                                "nama_supplier": str(row["nama_supplier"]),
                                "tagihan": float(row["tagihan"]),
                                "sistem_bayar": str(row["sistem_bayar"])
                            }).eq("id", int(row["id"])).execute()
                            count_upd_sup += 1
                    except Exception as e:
                        st.error(f"Gagal memperbarui supplier ID {row['id']}: {e}")
            if count_upd_sup > 0:
                st.success(f"Berhasil memperbarui {count_upd_sup} data supplier!")
                st.experimental_rerun()
            else:
                st.info("Tidak ada perubahan data supplier.")
    else:
        st.info("Belum ada data supplier.")

# ==========================================
# MENU 5: LAPORAN
# ==========================================
elif menu_pilihan == "Laporan":
    st.markdown("Pusat Laporan & Analisis Data")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Analisis visual mendalam terkait performa retur, akumulasi tagihan supplier, dan tren pembelian.</p>", unsafe_allow_html=True)
    
    df_lap_retur = ambil_data_retur()
    df_lap_sup = ambil_data_supplier()
    
    tab_l1, tab_l2 = st.tabs(["Analisis Retur", "Analisis Tagihan Supplier"])
    
    with tab_l1:
        st.markdown("Top Supplier Berdasarkan Nilai Retur")
        if not df_lap_retur.empty and "total" in df_lap_retur.columns:
            df_grouped_retur = df_lap_retur.groupby("supplier")["total"].sum().reset_index().sort_values(by="total", ascending=False).head(10)
            fig_bar_ret = px.bar(df_grouped_retur, x="supplier", y="total", title="10 Supplier dengan Nilai Retur Terbesar", text_auto=",", template=plotly_template)
            fig_bar_ret.update_layout(xaxis_title=None, yaxis_title="Total (Rp)", margin=dict(t=40,b=30,l=10,r=10))
            st.plotly_chart(fig_bar_ret, use_container_width=True)
        else:
            st.info("Data retur belum mencukupi.")
            
    with tab_l2:
        st.markdown("Top Supplier Berdasarkan Tagihan Terbesar")
        if not df_lap_sup.empty and "tagihan" in df_lap_sup.columns:
            df_grouped_sup = df_lap_sup.sort_values(by="tagihan", ascending=False).head(10)
            fig_bar_sup = px.bar(df_grouped_sup, x="nama_supplier", y="tagihan", title="10 Supplier dengan Tagihan Tertinggi", text_auto=",", template=plotly_template)
            fig_bar_sup.update_layout(xaxis_title=None, yaxis_title="Tagihan (Rp)", margin=dict(t=40,b=30,l=10,r=10))
            st.plotly_chart(fig_bar_sup, use_container_width=True)
        else:
            st.info("Data supplier belum mencukupi.")

# ==========================================
# MENU 6: PENGATURAN
# ==========================================
elif menu_pilihan == "Pengaturan":
    st.markdown("Pengaturan Sistem")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Konfigurasi akun, informasi toko, dan preferensi aplikasi.</p>", unsafe_allow_html=True)
    
    st.markdown("Profil Toko")
    st.text_input("Nama Toko", value="Toserba Nurja Berkah", disabled=True)
    st.text_input("Lokasi / Alamat", value="Probolinggo, Jawa Timur", disabled=True)
    st.text_input("Sistem Versi", value="v2.5.0 Production", disabled=True)
    
    st.divider()
    st.markdown("Preferensi Tampilan")
    mode_setting = st.selectbox("Pilih Tema Utama", ["Terang", "Gelap"], index=0 if st.session_state.theme == "Terang" else 1)
    if st.button("Terapkan Tema", type="primary"):
        st.session_state.theme = "Terang" if "Terang" in mode_setting else "Gelap"
        st.success("Tema berhasil diperbarui! Silakan refresh halaman jika diperlukan.")
