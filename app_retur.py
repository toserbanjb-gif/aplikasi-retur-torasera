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
    .app-header { display:flex; align-items:center; gap:18px; }
    .app-title { font-size:22px; font-weight:700; margin:0; }
    .app-sub { margin:0; color: #64748B; font-size:13px; }
    .metric-card { background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); padding:14px; border-radius:10px; box-shadow: 0 1px 4px rgba(2,6,23,0.06); }
    .small-muted { color:#94A3B8; font-size:12px; }
    .btn-primary { background-color:#2563EB !important; color:white !important; border-radius:8px !important; padding:8px 12px; }
    .download-btn { background:#10B981 !important; color:white !important; border-radius:8px !important; padding:8px 12px; }
    .card-title { font-size:14px; font-weight:600; margin-bottom:6px; }
    .table-header { background-color:#0F172A !important; color:white !important; }
    /* Sidebar tweaks */
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

# --- INISIALISASI SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url: str = st.secrets["SUPABASE_URL"].strip()
    key: str = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

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
        df["jenis_pajak"] = df["jenis_pajak"].astype(str)
        df["sistem_bayar"] = df["sistem_bayar"].astype(str)
        
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
            return pd.DataFrame(columns=["id", "no_invoice", "nama_supplier", "total_tagihan", "tgl_datang", "jatuh_tempo", "status_lunas"])
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

        if cari:
            kw = cari.lower()
            df = df[
                df["nama_supplier"].str.lower().str.contains(kw) |
                df["no_invoice"].str.lower().str.contains(kw) |
                df["status_lunas"].str.lower().str.contains(kw)
            ]
        return df
    except Exception:
        return pd.DataFrame(columns=["id", "no_invoice", "nama_supplier", "total_tagihan", "tgl_datang", "jatuh_tempo", "status_lunas"])

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
            Paragraph(html.escape(str(row['jenis_pajak'])), style_cell),
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
    st.markdown("<div style='display:flex;align-items:center;gap:12px'><div style='width:48px;height:48px;background:#2563EB;border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700'>TN</div><div><div style='font-weight:700'>Toserba Nurja Berkah</div><div style='font-size:12px;color:#94A3B8'>Manajemen Retur & Supplier</div></div></div>", unsafe_allow_html=True)
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
    "PT Borwita Citra Prima (Listin)", "PT. SINAR NIAGA SEJAHTERA (Angga)", "PT SINARMAS DISTRIBUSI NUSANTARA (Mathias)",
    # ... (sisa daftar tetap sama seperti sebelumnya)
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
    label_lonceng = f"Notifikasi ({jml_notif})" if jml_notif > 0 else "Notifikasi"
    if st.button(label_lonceng, help="Cek Peringatan Jatuh Tempo"):
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
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Formulir pencatatan barang retur baru ke database sistem.</p>", unsafe_allow_html=True)
    
    with st.form("form_input_retur", clear_on_submit=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_kode = st.text_input("Kode Barcode / SKU")
            f_nama = st.text_input("Nama Barang")
            f_qty = st.number_input("Quantity (Qty)", min_value=1, value=1)
        with fc2:
            f_hpp = st.number_input("Harga HPP (Rp)", min_value=0.0, value=0.0, step=100.0)
            f_ket = st.selectbox("Keterangan Retur", ["ED", "Rusak", "Salah PO", "Lebih Bayar", "Lainnya"])
            f_ed = st.text_input("Tanggal ED (jika ada, misal: 31-12-2026 atau -)")
        with fc3:
            f_supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER)
            f_status = st.selectbox("Status Retur", ["Pengajuan", "Sedang Diproses", "Sukses"])
            f_tgl = st.date_input("Tanggal Input", value=datetime.date.today())
        
        submit_retur = st.form_submit_button("Simpan Data Retur", type="primary")
        if submit_retur:
            if not f_nama:
                st.warning("Nama barang tidak boleh kosong!")
            else:
                try:
                    total_val = float(f_qty) * float(f_hpp)
                    payload_retur = {
                        "kode": str(f_kode),
                        "nama": str(f_nama),
                        "qty": int(f_qty),
                        "hpp": float(f_hpp),
                        "total": float(total_val),
                        "ket": str(f_ket),
                        "ed": str(f_ed),
                        "supplier": str(f_supplier),
                        "status": str(f_status),
                        "tgl_input": str(f_tgl)
                    }
                    supabase.table("barang_retur").insert(payload_retur).execute()
                    st.success("Data barang retur berhasil disimpan!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data retur: {e}")

    st.divider()
    st.markdown("Riwayat Retur Terbaru")
    df_history = ambil_data_retur()
    if not df_history.empty:
        st.dataframe(df_history.tail(10).reset_index(drop=True), use_container_width=True, hide_index=True)
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
                        
                        if (
                            str(row["kode"]) != str(orig["kode"]) or
                            str(row["nama"]) != str(orig["nama"]) or
                            new_qty != float(orig["qty"]) or
                            new_hpp != float(orig["hpp"]) or
                            str(row["ket"]) != str(orig["ket"]) or
                            str(row["ed"]) != str(orig["ed"]) or
                            str(row["supplier"]) != str(orig["supplier"]) or
                            str(row["status"]) != str(orig["status"])
                        ):
                            supabase.table("barang_retur").update({
                                "kode": str(row["kode"]),
                                "nama": str(row["nama"]),
                                "qty": int(new_qty),
                                "hpp": float(new_hpp),
                                "total": float(new_total),
                                "ket": str(row["ket"]),
                                "ed": str(row["ed"]),
                                "supplier": str(row["supplier"]),
                                "status": str(row["status"])
                            }).eq("id", int(row["id"])).execute()
                            count_upd_retur += 1
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
                        except (ValueError, TypeError):
                            continue
                    st.success("Data retur terpilih berhasil dihapus!")
                    st.experimental_rerun()
    else:
        st.info("Tidak ada data retur yang ditemukan sesuai filter.")

# ==========================================
# MENU 3: INPUT PEMBELIAN / INVOICE
# ==========================================
elif menu_pilihan == "Input Pembelian":
    st.markdown("Pencatatan & Manajemen Invoice Supplier")
    st.markdown("<p class='small-muted' style='margin-top:-10px'>Formulir pencatatan faktur/invoice barang masuk lengkap dengan upload bukti nota dan bukti pembayaran.</p>", unsafe_allow_html=True)
    
    df_inv_view = ambil_data_pembelian("")
    tab_tambah, tab_edit = st.tabs(["Tambah Pembelian Baru", "Edit / Hapus Pembelian"])
    
    with tab_tambah:
        with st.form("form_input_pembelian", clear_on_submit=True):
            ic1, ic2 = st.columns(2)
            with ic1:
                i_invoice = st.text_input("Nomor Invoice / Faktur")
                i_supplier = st.selectbox("Nama Supplier", DAFTAR_SUPPLIER, key="inv_sup_baru")
                i_tagihan = st.number_input("Total Tagihan / Nilai Faktur (Rp)", min_value=0.0, value=0.0, step=1000.0)
            with ic2:
                i_tgl_datang = st.date_input("Tanggal Datang Barang", value=datetime.date.today())
                i_jatuh_tempo = st.date_input("Tanggal Jatuh Tempo", value=datetime.date.today() + datetime.timedelta(days=30))
                i_status_lunas = st.selectbox("Status Pelunasan", ["Belum Lunas", "Lunas", "Sebagian"], key="inv_stat_baru")
                
            st.markdown("---")
            uc1, uc2 = st.columns(2)
            with uc1:
                i_file_nota = st.file_uploader("Upload Foto/File Bukti Nota (Opsional)", type=["png", "jpg", "jpeg", "pdf"], key="up_nota")
            with uc2:
                i_file_bayar = st.file_uploader("Upload Foto/File Bukti Pembayaran (Opsional)", type=["png", "jpg", "jpeg", "pdf"], key="up_bayar")
            
            submit_inv = st.form_submit_button("Simpan Data Pembelian", type="primary")
            if submit_inv:
                if not i_invoice:
                    st.warning("Nomor invoice tidak boleh kosong!")
                else:
                    try:
                        public_url_nota = ""
                        public_url_bayar = ""
                        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        if i_file_nota is not None:
                            ext_nota = i_file_nota.name.split(".")[-1]
                            name_nota = f"nota_{timestamp_str}_{str(i_invoice).replace('/', '_')}.{ext_nota}"
                            supabase.storage.from_("bukti_pembelian").upload(
                                path=name_nota,
                                file=i_file_nota.getvalue(),
                                file_options={"content-type": i_file_nota.type}
                            )
                            res_nota = supabase.storage.from_("bukti_pembelian").get_public_url(name_nota)
                            public_url_nota = res_nota if isinstance(res_nota, str) else res_nota.get("publicUrl", "")

                        if i_file_bayar is not None:
                            ext_bayar = i_file_bayar.name.split(".")[-1]
                            name_bayar = f"bayar_{timestamp_str}_{str(i_invoice).replace('/', '_')}.{ext_bayar}"
                            supabase.storage.from_("bukti_pembelian").upload(
                                path=name_bayar,
                                file=i_file_bayar.getvalue(),
                                file_options={"content-type": i_file_bayar.type}
                            )
                            res_bayar = supabase.storage.from_("bukti_pembelian").get_public_url(name_bayar)
                            public_url_bayar = res_bayar if isinstance(res_bayar, str) else res_bayar.get("publicUrl", "")

                        payload_inv = {
                            "no_invoice": str(i_invoice),
                            "nama_supplier": str(i_supplier),
                            "total_tagihan": float(i_tagihan),
                            "tgl_datang": str(i_tgl_datang),
                            "jatuh_tempo": str(i_jatuh_tempo),
                            "status_lunas": str(i_status_lunas),
                            "link_foto": str(public_url_nota),
                            "link_bayar": str(public_url_bayar)
                        }
                        supabase.table("data_pembelian").insert(payload_inv).execute()
                        st.success("Data pembelian berhasil disimpan!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan data pembelian: {e}")

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
                
                with st.form("form_edit_pembelian"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_invoice = st.text_input("Nomor Invoice / Faktur", value=str(data_terpilih["no_invoice"]))
                        sup_idx = DAFTAR_SUPPLIER.index(data_terpilih["nama_supplier"]) if data_terpilih["nama_supplier"] in DAFTAR_SUPPLIER else 0
                        e_supplier = st.selectbox("Nama Supplier", DAFTAR_SUPPLIER, index=sup_idx, key="edit_sup")
                        e_tagihan = st.number_input("Total Tagihan / Nilai Faktur (Rp)", min_value=0.0, value=float(data_terpilih["total_tagihan"]), step=1000.0)
                    with ec2:
                        parsed_tgl_datang = datetime.datetime.strptime(str(data_terpilih["tgl_datang"]), "%Y-%m-%d").date() if pd.notna(data_terpilih["tgl_datang"]) else datetime.date.today()
                        e_tgl_datang = st.date_input("Tanggal Datang Barang", value=parsed_tgl_datang)
                        
                        parsed_jatuh_tempo = datetime.datetime.strptime(str(data_terpilih["jatuh_tempo"]), "%Y-%m-%d").date() if pd.notna(data_terpilih["jatuh_tempo"]) else datetime.date.today()
                        e_jatuh_tempo = st.date_input("Tanggal Jatuh Tempo", value=parsed_jatuh_tempo)
                        
                        stat_list = ["Belum Lunas", "Lunas", "Sebagian"]
                        stat_idx = stat_list.index(data_terpilih["status_lunas"]) if data_terpilih["status_lunas"] in stat_list else 0
                        e_status_lunas = st.selectbox("Status Pelunasan", stat_list, index=stat_idx, key="edit_stat")
                    
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        submit_update = st.form_submit_button("Update / Simpan Perubahan", type="primary", use_container_width=True)
                    with btn_col2:
                        submit_delete = st.form_submit_button("Hapus Data Ini", type="secondary", use_container_width=True)
                        
                    if submit_update:
                        try:
                            supabase.table("data_pembelian").update({
                                "no_invoice": str(e_invoice),
                                "nama_supplier": str(e_supplier),
                                "total_tagihan": float(e_tagihan),
                                "tgl_datang": str(e_tgl_datang),
                                "jatuh_tempo": str(e_jatuh_tempo),
                                "status_lunas": str(e_status_lunas)
                            }).eq("id", selected_id).execute()
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
        if "link_foto" not in df_inv_filtered.columns:
            df_inv_filtered["link_foto"] = ""
        else:
            df_inv_filtered["link_foto"] = df_inv_filtered["link_foto"].fillna("")
            
        if "link_bayar" not in df_inv_filtered.columns:
            df_inv_filtered["link_bayar"] = ""
        else:
            df_inv_filtered["link_bayar"] = df_inv_filtered["link_bayar"].fillna("")

        st.dataframe(
            df_inv_filtered,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "no_invoice": st.column_config.TextColumn("No Invoice", width="medium"),
                "nama_supplier": st.column_config.TextColumn("Supplier", width="large"),
                "total_tagihan": st.column_config.NumberColumn("Total Tagihan (Rp)", format="Rp %'d", width="medium"),
                "tgl_datang": st.column_config.DateColumn("Tgl Datang", width="small"),
                "jatuh_tempo": st.column_config.DateColumn("Tgl Jatuh Tempo", width="small"),
                "status_lunas": st.column_config.TextColumn("Status", width="small"),
                "link_foto": st.column_config.LinkColumn("Bukti Nota", display_text="Download Nota", width="medium"),
                "link_bayar": st.column_config.LinkColumn("Bukti Bayar", display_text="Download Bukti Bayar", width="medium"),
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
                    if (
                        str(row["nama_supplier"]) != str(orig["nama_supplier"]) or
                        float(row["tagihan"]) != float(orig["tagihan"]) or
                        str(row["sistem_bayar"]) != str(orig["sistem_bayar"])
                    ):
                        supabase.table("data_supplier").update({
                            "nama_supplier": str(row["nama_supplier"]),
                            "tagihan": float(row["tagihan"]),
                            "sistem_bayar": str(row["sistem_bayar"])
                        }).eq("id", int(row["id"])).execute()
                        count_upd_sup += 1
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
