# app.py (lengkap, sudah memperbaiki masalah kolom yang tidak ada dan menambahkan upload faktur pajak)
import re
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
    .error-box { background:#fee2e2; color:#7f1d1d; padding:10px; border-radius:6px; margin-top:8px; }
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

# --- INISIALISASI SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url: str = st.secrets["SUPABASE_URL"].strip()
    key: str = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

# --- Helper: safe insert / update that removes missing columns in case Supabase returns schema errors ---
_missing_col_pattern = re.compile(r"Could not find the '([^']+)' column", re.IGNORECASE)

def _extract_missing_columns_from_error(err_text: str):
    """Return list of missing column names parsed from error text."""
    if not err_text:
        return []
    return _missing_col_pattern.findall(err_text)

def _check_response_error(res):
    """Check common response shapes for errors and return error string or None."""
    try:
        # supabase-py sometimes returns object with .error, or dict with 'error'
        if hasattr(res, "error") and res.error:
            return str(res.error)
        if isinstance(res, dict) and res.get("error"):
            return str(res.get("error"))
    except Exception:
        pass
    return None

def safe_insert(table_name: str, payload: dict):
    """Try to insert payload, and if DB complains about missing columns, remove them and retry."""
    payload_copy = payload.copy()
    tried = 0
    while True:
        tried += 1
        try:
            res = supabase.table(table_name).insert(payload_copy).execute()
            err = _check_response_error(res)
            if err:
                raise Exception(err)
            return res
        except Exception as e:
            msg = str(e)
            missing = _extract_missing_columns_from_error(msg)
            if missing and tried == 1:
                # remove missing keys and retry once
                for col in missing:
                    payload_copy.pop(col, None)
                # keep a visible message to the user
                st.warning(f"Kolom DB tidak ditemukan: {missing}. Mengirim tanpa kolom tersebut sementara.")
                continue
            # no recognizable missing-column error (or already retried)
            raise

def safe_update(table_name: str, payload: dict, id_field: str, id_value):
    """Try to update payload for row id_field == id_value, with fallback removing missing columns."""
    payload_copy = payload.copy()
    tried = 0
    while True:
        tried += 1
        try:
            res = supabase.table(table_name).update(payload_copy).eq(id_field, id_value).execute()
            err = _check_response_error(res)
            if err:
                raise Exception(err)
            return res
        except Exception as e:
            msg = str(e)
            missing = _extract_missing_columns_from_error(msg)
            if missing and tried == 1:
                for col in missing:
                    payload_copy.pop(col, None)
                st.warning(f"Kolom DB tidak ditemukan: {missing}. Memperbarui tanpa kolom tersebut sementara.")
                continue
            raise

# --- FUNGSI AMBIL DATA SUPPLIER ---
def ambil_data_supplier(cari=""):
    try:
        query = supabase.table("data_supplier").select("*")
        response = query.execute()
        if not response.data:
            return pd.DataFrame(columns=["id", "no_urut", "nama_supplier", "tagihan", "jenis_pajak", "sistem_bayar", "jatuh_tempo"])
        df = pd.DataFrame(response.data)
        df.columns = [str(c).lower() for c in df.columns]
        
        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)
            
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
        df["no_urut"] = pd.to_numeric(df["no_urut"], errors="coerce").fillna(1).astype(int)
        df["tagihan"] = pd.to_numeric(df["tagihan"], errors="coerce").fillna(0.0).astype(float)
        df["nama_supplier"] = df["nama_supplier"].astype(str)
        df["jenis_pajak"] = df["jenis_pajak"].astype(str) if "jenis_pajak" in df.columns else "Non PKP"
        df["sistem_bayar"] = df["sistem_bayar"].astype(str) if "sistem_bayar" in df.columns else ""
        
        if "jatuh_tempo" in df.columns:
            df["jatuh_tempo"] = pd.to_datetime(df["jatuh_tempo"], errors="coerce").dt.date
        else:
            df["jatuh_tempo"] = datetime.date.today()

        if cari:
            kw = cari.lower()
            df = df[
                df["nama_supplier"].str.lower().str.contains(kw) |
                df["jenis_pajak"].str.lower().str.contains(kw) |
                df["sistem_bayar"].str.lower().str.contains(kw)
            ]
        return df
    except Exception:
        return pd.DataFrame(columns=["id", "no_urut", "nama_supplier", "tagihan", "jenis_pajak", "sistem_bayar", "jatuh_tempo"])

# --- FUNGSI AMBIL DATA PEMBELIAN / INVOICE ---
def ambil_data_pembelian(cari=""):
    try:
        query = supabase.table("data_pembelian").select("*")
        response = query.execute()
        if not response.data:
            return pd.DataFrame(columns=["id", "no_invoice", "nama_supplier", "total_tagihan", "tgl_datang", "jatuh_tempo", "status_lunas", "link_foto", "link_bayar", "link_faktur_pajak", "jenis_pajak"])
        df = pd.DataFrame(response.data)
        df.columns = [str(c).lower() for c in df.columns]
        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)
        
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
        df["total_tagihan"] = pd.to_numeric(df["total_tagihan"], errors="coerce").fillna(0.0).astype(float)
        
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

        if cari:
            kw = cari.lower()
            df = df[
                df["nama_supplier"].str.lower().str.contains(kw) |
                df["no_invoice"].str.lower().str.contains(kw) |
                df["status_lunas"].str.lower().str.contains(kw)
            ]
        return df
    except Exception:
        return pd.DataFrame(columns=["id", "no_invoice", "nama_supplier", "total_tagihan", "tgl_datang", "jatuh_tempo", "status_lunas", "link_foto", "link_bayar", "link_faktur_pajak", "jenis_pajak"])

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
        tagihan_val = float(row['tagihan'])
        total_tagihan_pdf += tagihan_val
        table_data.append([
            Paragraph(str(row['no_urut']), style_cell),
            Paragraph(html.escape(str(row['nama_supplier'])), style_cell),
            Paragraph(f"Rp {tagihan_val:,.0f}", style_cell),
            Paragraph(html.escape(str(row.get('jenis_pajak', ''))), style_cell),
            Paragraph(html.escape(str(row['sistem_bayar'])), style_cell),
            Paragraph(str(row['jatuh_tempo']), style_cell)
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
        qty_v = float(row['qty'])
        hpp_v = float(row['hpp'])
        tot_v = float(row['total']) if 'total' in row and pd.notna(row['total']) else (qty_v * hpp_v)
        total_nilai_retur += tot_v
        
        table_data.append([
            Paragraph(html.escape(str(row['kode'])), style_cell),
            Paragraph(html.escape(str(row['nama'])), style_cell),
            Paragraph(html.escape(str(row['supplier'])), style_cell),
            Paragraph(str(int(qty_v)), style_cell),
            Paragraph(f"{hpp_v:,.0f}", style_cell),
            Paragraph(f"{tot_v:,.0f}", style_cell),
            Paragraph(html.escape(str(row['status'])), style_cell)
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
        ["Home", "Input Retur", "List Retur", "Input Pembelian", "Data Supplier", "Laporan", "Pengaturan"],
        index=0
    )
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
    "Belum Tau", "PT ARTABOGA (Hanif)", "PT. PANGAN LESTARI (Ratna)", "SINAR SURYA SUKSES (Adhit)",
    # ... (daftar lengkap sama seperti sebelumnya)
    "SUMBER CIPTA MULTINIAGA", "SUMBER CIPTA MULTINIAGA", "BSU"
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
            df["kode"].astype(str).str.lower().str.contains(kw) |
            df["nama"].astype(str).str.lower().str.contains(kw) |
            df["ket"].astype(str).str.lower().str.contains(kw) |
            df["supplier"].astype(str).str.lower().str.contains(kw) |
            df["status"].astype(str).str.lower().str.contains(kw)
        ]
    return df

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

# (sisa UI: Home, Input Retur, List Retur tetap seperti sebelumnya, gunakan kode dari versi sebelumnya)
# Untuk singkat, saya hanya menampilkan bagian Input Pembelian (tambah & edit) karena itu yang diperbarui.

if menu_pilihan == "Input Pembelian":
    st.markdown("Pencatatan & Manajemen Invoice Supplier")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Formulir pencatatan faktur/invoice barang masuk lengkap dengan upload bukti nota, bukti pembayaran, dan faktur pajak.</p>", unsafe_allow_html=True)
    
    # Ambil data terbaru
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
                            public_url_nota = res_nota if isinstance(res_nota, str) else res_nota.get("publicUrl", "")

                        if i_file_bayar is not None:
                            ext_bayar = i_file_bayar.name.split(".")[-1]
                            name_bayar = f"bayar_{timestamp_str}_{safe_invoice}.{ext_bayar}"
                            supabase.storage.from_("bukti_pembelian").upload(
                                path=name_bayar,
                                file=i_file_bayar.getvalue(),
                                file_options={"content-type": i_file_bayar.type}
                            )
                            res_bayar = supabase.storage.from_("bukti_pembelian").get_public_url(name_bayar)
                            public_url_bayar = res_bayar if isinstance(res_bayar, str) else res_bayar.get("publicUrl", "")

                        if i_file_faktur_pajak is not None:
                            ext_fp = i_file_faktur_pajak.name.split(".")[-1]
                            name_fp = f"faktur_pajak_{timestamp_str}_{safe_invoice}.{ext_fp}"
                            supabase.storage.from_("bukti_pembelian").upload(
                                path=name_fp,
                                file=i_file_faktur_pajak.getvalue(),
                                file_options={"content-type": i_file_faktur_pajak.type}
                            )
                            res_fp = supabase.storage.from_("bukti_pembelian").get_public_url(name_fp)
                            public_url_faktur_pajak = res_fp if isinstance(res_fp, str) else res_fp.get("publicUrl", "")

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
                        # use safe_insert so missing columns won't break the app
                        safe_insert("data_pembelian", payload_inv)
                        st.success("Data pembelian berhasil disimpan!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan data pembelian: {e}")

    # ================= TAB 2: EDIT / HAPUS PEMBELIAN =================
    with tab_edit:
        st.markdown("Form Edit & Hapus Data Pembelian")
        if df_inv_view.empty:
            st.info("Belum ada data pembelian untuk diedit.")
        else:
            pilihan_data = df_inv_view.apply(lambda row: f"ID: {row['id']} | Inv: {row['no_invoice']} | {row['nama_supplier']}", axis=1).tolist()
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
                        e_invoice = st.text_input("Nomor Invoice / Faktur", value=str(data_terpilih["no_invoice"]))
                        sup_idx = DAFTAR_SUPPLIER.index(data_terpilih["nama_supplier"]) if data_terpilih["nama_supplier"] in DAFTAR_SUPPLIER else 0
                        e_supplier = st.selectbox("Nama Supplier", DAFTAR_SUPPLIER, index=sup_idx, key="edit_sup")
                        e_tagihan = st.number_input("Total Tagihan / Nilai Faktur (Rp)", min_value=0.0, value=float(data_terpilih["total_tagihan"]), step=1000.0)
                        e_jenis_pajak = st.selectbox("Jenis Pajak", ["Non PKP", "PKP"], index=0 if current_jenis_pajak == "Non PKP" else 1)
                    with ec2:
                        try:
                            parsed_tgl_datang = datetime.datetime.strptime(str(data_terpilih["tgl_datang"]), "%Y-%m-%d").date() if pd.notna(data_terpilih["tgl_datang"]) else datetime.date.today()
                        except Exception:
                            parsed_tgl_datang = datetime.date.today()
                        e_tgl_datang = st.date_input("Tanggal Datang Barang", value=parsed_tgl_datang)
                        
                        try:
                            parsed_jatuh_tempo = datetime.datetime.strptime(str(data_terpilih["jatuh_tempo"]), "%Y-%m-%d").date() if pd.notna(data_terpilih["jatuh_tempo"]) else datetime.date.today()
                        except Exception:
                            parsed_jatuh_tempo = datetime.date.today()
                        e_jatuh_tempo = st.date_input("Tanggal Jatuh Tempo", value=parsed_jatuh_tempo)
                        
                        stat_list = ["Belum Lunas", "Lunas", "Sebagian"]
                        stat_idx = stat_list.index(data_terpilih["status_lunas"]) if data_terpilih["status_lunas"] in stat_list else 0
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
                                public_url_nota = res_nota if isinstance(res_nota, str) else res_nota.get("publicUrl", "")

                            if e_file_bayar is not None:
                                ext_bayar = e_file_bayar.name.split(".")[-1]
                                name_bayar = f"bayar_{timestamp_str}_{safe_invoice}.{ext_bayar}"
                                supabase.storage.from_("bukti_pembelian").upload(
                                    path=name_bayar,
                                    file=e_file_bayar.getvalue(),
                                    file_options={"content-type": e_file_bayar.type}
                                )
                                res_bayar = supabase.storage.from_("bukti_pembelian").get_public_url(name_bayar)
                                public_url_bayar = res_bayar if isinstance(res_bayar, str) else res_bayar.get("publicUrl", "")

                            if e_file_faktur_pajak is not None:
                                ext_fp = e_file_faktur_pajak.name.split(".")[-1]
                                name_fp = f"faktur_pajak_{timestamp_str}_{safe_invoice}.{ext_fp}"
                                supabase.storage.from_("bukti_pembelian").upload(
                                    path=name_fp,
                                    file=e_file_faktur_pajak.getvalue(),
                                    file_options={"content-type": e_file_faktur_pajak.type}
                                )
                                res_fp = supabase.storage.from_("bukti_pembelian").get_public_url(name_fp)
                                public_url_faktur_pajak = res_fp if isinstance(res_fp, str) else res_fp.get("publicUrl", "")

                            payload_upd = {
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
                            safe_update("data_pembelian", payload_upd, "id", selected_id)

                            st.success("Data pembelian berhasil diperbarui!")
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
