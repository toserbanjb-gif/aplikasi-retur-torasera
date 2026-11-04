# ui_theme.py  (v4 - gaya Admin Dashboard)
# Modul TAMPILAN saja. Tidak ada akses Supabase / data / logika bisnis di sini.
from urllib.parse import quote

import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------
# Palet warna
# ------------------------------------------------------------------
LIGHT = {
    "bg": "#EEF1F6",
    "surface": "#FFFFFF",
    "surface2": "#F4F6FA",
    "border": "#E1E6EE",
    "text": "#2B3245",
    "text2": "#4A5468",
    "muted": "#7A8499",
    "primary": "#2F80ED",
    "primary_dark": "#2368C9",
    "primary_soft": "rgba(47,128,237,.12)",
    "btn_text": "#FFFFFF",
    "topbar": "#2F80ED",
    "sidebar": "#2B3144",
    "shadow": "0 1px 3px rgba(30,41,59,.08)",
    "shadow_lg": "0 6px 18px rgba(30,41,59,.12)",
}
DARK = {
    "bg": "#171C2B",
    "surface": "#222A3D",
    "surface2": "#1C2335",
    "border": "#2F3950",
    "text": "#E6EBF5",
    "text2": "#B8C2D6",
    "muted": "#8793AC",
    "primary": "#4C97F5",
    "primary_dark": "#3A82E0",
    "primary_soft": "rgba(76,151,245,.16)",
    "btn_text": "#FFFFFF",
    "topbar": "#1F4FA3",
    "sidebar": "#121726",
    "shadow": "0 1px 3px rgba(0,0,0,.35)",
    "shadow_lg": "0 6px 18px rgba(0,0,0,.45)",
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
# Judul kelompok menu sidebar: nomor menu -> judul (urutan menu sama dengan app.py)
_NAV_GROUPS = {1: "DASHBOARD", 2: "RETUR", 4: "TRANSAKSI", 6: "DATA", 8: "SISTEM"}

# ikon kartu statistik: retur, tagihan (kartu), keranjang, laporan
_CARD_ICONS = [
    _NAV_ICONS[1],
    "<rect x='2' y='5' width='20' height='14' rx='2'/><line x1='2' y1='10' x2='22' y2='10'/>",
    _NAV_ICONS[4],
    _NAV_ICONS[6],
]
# hijau, biru, oranye, merah
_CARD_COLORS = [("#2EC57A", "#22A862"), ("#3B8CF5", "#2A6FD6"), ("#FFA53A", "#F28A12"), ("#F0605F", "#D94445")]


def _uri(body: str, color: str) -> str:
    return "data:image/svg+xml," + quote(_SVG.format(c=color, p=body), safe="")


def _nav_css() -> str:
    n = len(_NAV_ICONS)
    base = f'.stApp [data-testid="stSidebar"] div[role="radiogroup"] > label:first-child:nth-last-child({n})'
    out = [
        f'{base}::before, {base} ~ label::before {{content:"";width:18px;height:18px;flex:none;'
        "background:currentColor;-webkit-mask-size:contain;mask-size:contain;"
        "-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;"
        "-webkit-mask-position:center;mask-position:center;}"
    ]
    for k, body in enumerate(_NAV_ICONS, start=1):
        u = _uri(body, "black")
        sel = base if k == 1 else f"{base} ~ label:nth-child({k})"
        out.append(f'{sel}::before{{-webkit-mask-image:url("{u}");mask-image:url("{u}");}}')
        if k in _NAV_GROUPS:
            out.append(
                f"{sel}{{position:relative;margin-top:{26 if k == 1 else 30}px;}}"
                f'{sel}::after{{content:"{_NAV_GROUPS[k]}";position:absolute;left:4px;top:-21px;'
                "font-size:11px;font-weight:700;letter-spacing:.07em;color:#7F8AA3;pointer-events:none;}"
            )
    return "\n".join(out)


def _card_css() -> str:
    out = []
    for k, (body, (c1, c2)) in enumerate(zip(_CARD_ICONS, _CARD_COLORS), start=1):
        col = f'[data-testid="stColumn"]:nth-child({k})'
        out.append(f"{col} {{--c1:{c1};--c2:{c2};}}")
        out.append(
            f'{col} .metric-card::after {{background:url("{_uri(body, "white")}") center/24px no-repeat,'
            "rgba(255,255,255,.22);}"
        )
    return "\n".join(out)


# ------------------------------------------------------------------
# CSS statis
# ------------------------------------------------------------------
_FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');"

_STATIC_CSS = r"""
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp textarea,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-testid="stMarkdownContainer"] {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stMainBlockContainer"], .block-container { padding-top: 4.4rem; max-width: 1400px; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--text); font-weight: 700; letter-spacing: -.01em; }
.stApp [data-testid="stMarkdownContainer"] p { color: var(--text2); }
.stApp [data-testid="stWidgetLabel"] p, .stApp label p { color: var(--text2); font-weight: 600; font-size: 13px; }
hr { border-color: var(--border) !important; opacity: 1; margin: 1.1rem 0 !important; }
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 8px; }

/* ---------- Top bar biru ---------- */
[data-testid="stDecoration"] { display: none; }
[data-testid="stHeader"] { background: var(--topbar); height: 3rem; box-shadow: 0 1px 4px rgba(0,0,0,.18); }
[data-testid="stHeader"] *, [data-testid="stHeader"] button { color: #FFFFFF !important; fill: currentColor; }
[data-testid="stHeader"] button:hover { background: rgba(255,255,255,.14) !important; }

/* ---------- Judul halaman (strip putih) ---------- */
[data-testid="stHorizontalBlock"]:has(.app-header) {
  align-items: center; gap: 1rem; padding: 14px 20px; background: var(--surface); border: 1px solid var(--border);
  border-left: 4px solid var(--primary); border-radius: 6px; box-shadow: var(--shadow); }
[data-testid="stHorizontalBlock"]:has(.app-header) > [data-testid="stColumn"]:last-child {
  flex: 0 0 auto !important; width: auto !important; min-width: 150px; }
.app-header { display: flex; align-items: center; gap: 12px; }
.app-title { font-size: 20px !important; font-weight: 700 !important; letter-spacing: -.01em; margin: 0 !important; padding: 0 !important;
  color: var(--text) !important; line-height: 1.2; }
.app-sub { margin: 3px 0 0 0; color: var(--muted); font-size: 13px; }
[data-testid="stHorizontalBlock"]:has(.app-header) .stButton > button { white-space: nowrap; }

/* ---------- Judul bagian (kepala kartu) ---------- */
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] > p:not([class]) {
  font-size: 15px; font-weight: 700; color: var(--text); margin: .5rem 0 .3rem 0; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
[data-testid="stForm"] [data-testid="stMarkdownContainer"] > p:not([class]) { font-size: 14px; border-bottom: none; padding-bottom: 0; }
.section-title { font-size: 15px; font-weight: 700; color: var(--text); margin: .5rem 0 .3rem 0; padding-bottom: 8px; border-bottom: 1px solid var(--border); }

/* ---------- Kartu statistik berwarna ---------- */
[data-testid="stColumn"] { --c1: #3B8CF5; --c2: #2A6FD6; }
.metric-card { position: relative; overflow: hidden; display: flex; flex-direction: column; min-height: 120px;
  background: linear-gradient(135deg, var(--c1), var(--c2)); color: #fff; border-radius: 6px; padding: 18px 20px 14px 20px;
  box-shadow: var(--shadow); transition: transform .18s ease, box-shadow .18s ease; }
.metric-card:hover { transform: translateY(-2px); box-shadow: var(--shadow_lg); }
.metric-card::after { content: ""; position: absolute; right: 16px; top: 16px; width: 48px; height: 48px; border-radius: 8px; background: rgba(255,255,255,.22); }
.metric-card div[style*="font-size:18px"] { order: 1; font-size: 26px !important; font-weight: 700 !important; letter-spacing: -.01em;
  color: #fff !important; font-variant-numeric: tabular-nums; line-height: 1.15; padding-right: 60px; }
.metric-card .card-title { order: 2; font-size: 13px; font-weight: 500; color: rgba(255,255,255,.92); margin: 4px 0 14px 0; padding-right: 60px; }
.metric-card .small-muted { order: 3; margin: auto -20px -14px -20px !important; padding: 8px 20px; background: rgba(0,0,0,.14);
  color: rgba(255,255,255,.95) !important; font-size: 12px !important; }
.small-muted { color: var(--muted) !important; font-size: 12.5px !important; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background: var(--sidebar); border-right: none; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] li { color: #C5CCDB; }
.stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #C5CCDB; }
[data-testid="stSidebar"] .small-muted { color: #7F8AA3 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08) !important; }
[data-testid="stSidebar"] div[style*="background:#2563EB"] { background: var(--primary) !important; border-radius: 8px !important; }
[data-testid="stSidebar"] div[style*="color:#94A3B8"] { color: #8F9AB2 !important; }
[data-testid="stSidebar"] div[style*="font-weight:700"] { color: #FFFFFF; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"] > label {
  display: flex; align-items: center; gap: 12px; width: 100%; padding: 10px 14px; margin: 0;
  border-radius: 6px; cursor: pointer; transition: background .15s ease; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"] > label > div:nth-of-type(1) { display: none; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"] > label p { margin: 0; font-size: 14px; font-weight: 500; color: inherit; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: rgba(255,255,255,.07); }
.stApp [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background: var(--primary); color: #FFFFFF; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: #FFFFFF; font-weight: 600; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) {
  flex-direction: row; gap: 4px; padding: 4px; background: rgba(255,255,255,.07); border-radius: 8px; }
.stApp [data-testid="stSidebar"] div[role="radiogroup"]:has(> label:first-child:nth-last-child(2)) > label { flex: 1; justify-content: center; padding: 7px 8px; }

/* ---------- Tombol ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 6px; font-weight: 600; padding: .5rem 1rem; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); transition: all .15s ease; box-shadow: var(--shadow); }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
  border-color: var(--primary); color: var(--primary); }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"],
.stDownloadButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[data-testid="stBaseButton-primary"] {
  background: var(--primary); color: var(--btn_text); border: 1px solid var(--primary); }
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button[data-testid="stBaseButton-primary"]:hover {
  background: var(--primary_dark); border-color: var(--primary_dark); color: var(--btn_text); }
.stApp .stButton > button p, .stApp .stDownloadButton > button p, .stApp [data-testid="stFormSubmitButton"] > button p { color: inherit; font-weight: 600; }
[data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.07); border-color: rgba(255,255,255,.14); color: #E3E8F2; box-shadow: none; }
[data-testid="stSidebar"] .stButton > button:hover { background: var(--primary); border-color: var(--primary); color: #fff; }

/* ---------- Input ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  background: var(--surface) !important; border-color: var(--border) !important; border-radius: 6px !important; }
[data-baseweb="base-input"] { background: transparent !important; }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] div { color: var(--text) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-baseweb="textarea"]:focus-within {
  border-color: var(--primary) !important; box-shadow: 0 0 0 3px var(--primary_soft) !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--surface) !important; }
[data-baseweb="popover"] li { color: var(--text) !important; }
[data-baseweb="popover"] li:hover { background: var(--primary_soft) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--surface); border: 1.5px dashed var(--border); border-radius: 6px; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--primary); }
[data-testid="stForm"] { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 20px; box-shadow: var(--shadow); }

/* ---------- Tab garis bawah ---------- */
[data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid var(--border); background: transparent; }
[data-baseweb="tab-border"] { display: none !important; }
[data-baseweb="tab-highlight"] { background: var(--primary) !important; height: 3px !important; }
[data-baseweb="tab"] { padding: 10px 18px; background: transparent; }
.stApp [data-baseweb="tab"] p { font-weight: 600; color: var(--muted); font-size: 14px; }
.stApp [data-baseweb="tab"][aria-selected="true"] p { color: var(--primary); }

/* ---------- Tabel, grafik, notifikasi, dialog ---------- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border: 1px solid var(--border); border-radius: 6px; overflow: hidden; box-shadow: var(--shadow); background: var(--surface); }
[data-testid="stPlotlyChart"] { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 10px; box-shadow: var(--shadow); }
[data-testid="stAlert"] { border-radius: 6px; }
div[role="dialog"] { border-radius: 8px !important; background: var(--surface) !important; border: 1px solid var(--border); box-shadow: var(--shadow_lg); }
[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 6px; background: var(--surface); }
.js-plotly-plot .main-svg { background: transparent !important; }
.js-plotly-plot .plot-container .bg { fill: transparent !important; }

/* ---------- Loading: bar progres ---------- */
[data-testid="stStatusWidget"] { display: none !important; }
.stApp[data-teststate="running"]::after {
  content: ""; position: fixed; top: 0; left: 0; height: 4px; width: 38%; z-index: 999999;
  background: linear-gradient(90deg, transparent, #FFFFFF, #2EC57A, #FFA53A, transparent);
  animation: tn-run 1.05s cubic-bezier(.4,0,.2,1) infinite; }
@keyframes tn-run { 0% { transform: translateX(-100%); } 100% { transform: translateX(300%); } }

/* ---------- Loading: spinner ---------- */
[data-testid="stSpinner"] { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 6px; width: fit-content; box-shadow: var(--shadow); }
[data-testid="stSpinner"] svg, [data-testid="stSpinner"] i { display: none !important; }
[data-testid="stSpinner"]::before { content: ""; flex: none; width: 18px; height: 18px; border-radius: 50%;
  border: 3px solid var(--primary_soft); border-top-color: var(--primary); animation: tn-spin .75s linear infinite; }
[data-testid="stSpinner"] p, [data-testid="stSpinner"] div { color: var(--text2); font-weight: 600; margin: 0; }
@keyframes tn-spin { to { transform: rotate(360deg); } }

/* ---------- Loading: layar pembuka ---------- */
.tn-splash { position: fixed; inset: 0; z-index: 9999999; display: grid; place-items: center; pointer-events: none;
  background: var(--sidebar); animation: tn-splash-out .5s ease 1.2s forwards; }
.tn-splash-inner { display: flex; flex-direction: column; align-items: center; gap: 14px; text-align: center; }
.tn-ring { position: relative; width: 92px; height: 92px; display: grid; place-items: center; }
.tn-ring::before { content: ""; position: absolute; inset: 0; border-radius: 50%; border: 3px solid rgba(255,255,255,.12);
  border-top-color: #3B8CF5; border-right-color: #2EC57A; animation: tn-spin 1s linear infinite; }
.tn-ring::after { content: ""; position: absolute; inset: -13px; border-radius: 50%; border: 2px solid transparent;
  border-bottom-color: #FFA53A; border-left-color: #F0605F; opacity: .85; animation: tn-spin 1.8s linear infinite reverse; }
.tn-logo { width: 58px; height: 58px; border-radius: 12px; display: grid; place-items: center; color: #fff; font-weight: 700; font-size: 20px;
  background: var(--primary); box-shadow: 0 8px 22px rgba(47,128,237,.5); }
.tn-splash-title { font-size: 21px; font-weight: 700; color: #FFFFFF; margin-top: 8px; }
.tn-splash-sub { font-size: 13px; color: #9AA6BD; }
.tn-bar { width: 190px; height: 4px; border-radius: 4px; background: rgba(255,255,255,.12); overflow: hidden; }
.tn-bar span { display: block; height: 100%; width: 40%; border-radius: 4px; background: linear-gradient(90deg, #3B8CF5, #2EC57A);
  animation: tn-bar 1.1s ease-in-out infinite; }
@keyframes tn-bar { 0% { transform: translateX(-110%); } 100% { transform: translateX(280%); } }
@keyframes tn-splash-out { to { opacity: 0; visibility: hidden; pointer-events: none; } }

@media (prefers-reduced-motion: reduce) {
  .tn-splash { animation-duration: .01ms; animation-delay: .4s; }
  .tn-ring::before, .tn-ring::after, .tn-bar span, [data-testid="stSpinner"]::before { animation-duration: 2.4s; }
}
@media (max-width: 640px) {
  .app-title { font-size: 17px !important; }
  [data-testid="stHorizontalBlock"]:has(.app-header) { padding: 12px 14px; }
  [data-testid="stMainBlockContainer"], .block-container { padding-left: 1rem; padding-right: 1rem; }
}
"""


def _compact(css: str) -> str:
    # Hapus baris kosong & indentasi agar markdown Streamlit tidak memecah blok <style>
    lines = [ln.strip() for ln in css.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _patch_pie() -> None:
    """Pie chart jadi donut dengan legenda di bawah (hanya tampilan, data sama)."""
    orig = getattr(px, "pie", None)
    if orig is None or getattr(orig, "_tn_patched", False):
        return

    def pie(*args, **kwargs):
        kwargs.setdefault("hole", 0.55)
        fig = orig(*args, **kwargs)
        try:
            fig.update_layout(legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"))
            fig.update_traces(textinfo="percent")
        except Exception:
            pass
        return fig

    pie._tn_patched = True
    px.pie = pie


# ------------------------------------------------------------------
# API publik
# ------------------------------------------------------------------
def inject_theme(theme: str = "Terang") -> str:
    """Pasang seluruh CSS. Mengembalikan nama template plotly yang cocok."""
    pal = DARK if theme == "Gelap" else LIGHT
    root = ":root{" + "".join(f"--{k}:{v};" for k, v in pal.items()) + "}"
    css = _FONT_IMPORT + "\n" + root + "\n" + _STATIC_CSS + "\n" + _nav_css() + "\n" + _card_css()
    try:
        st.markdown(f"<style>\n{_compact(css)}\n</style>", unsafe_allow_html=True)
        px.defaults.color_discrete_sequence = [
            "#3B8CF5", "#2EC57A", "#FFA53A", "#F0605F", "#8B5CF6", "#00BCD4", "#64748B",
        ]
        _patch_pie()
    except Exception:
        pass
    return "plotly_dark" if theme == "Gelap" else "plotly"


def show_splash() -> None:
    """Layar pembuka. Hanya tampil sekali per sesi."""
    if st.session_state.get("_tn_splash_done"):
        return
    st.session_state["_tn_splash_done"] = True
    try:
        st.markdown(
            "<div class='tn-splash'><div class='tn-splash-inner'>"
            "<div class='tn-ring'><div class='tn-logo'>TN</div></div>"
            "<div class='tn-splash-title'>Toserba Nurja Berkah</div>"
            "<div class='tn-splash-sub'>Menyiapkan data retur dan supplier</div>"
            "<div class='tn-bar'><span></span></div>"
            "</div></div>",
            unsafe_allow_html=True,
        )
    except Exception:
        pass


def section_title(text: str) -> None:
    """Judul bagian (opsional). Teks st.markdown biasa sudah otomatis bergaya sama."""
    import html as _html

    st.markdown(f"<div class='section-title'>{_html.escape(text)}</div>", unsafe_allow_html=True)
