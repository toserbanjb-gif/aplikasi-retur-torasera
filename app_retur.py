import datetime
from io import BytesIO
import html
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client
import reportlab.lib.pagesizes

# --- CONFIG PAGE ---
st.set_page_config(
    page_title="Sistem Manajemen Retur - Toserba Nurja Berkah",
    page_icon="📦",
    layout="wide",
)

# --- INISIALISASI STATE THEME ---
if "theme" not in st.session_state:
    st.session_state.theme = "Terang"

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

# Ambil data supplier untuk cek notifikasi lonceng
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
                    notif_jatuh_tempo.append(f"🔴 **{row['nama_supplier']}** sudah **JATUH TEMPO** sejak {abs(selisih)} hari lalu!")
                elif selisih <= 3:
                    notif_jatuh_tempo.append(f"🟡 **{row['nama_supplier']}** jatuh tempo dalam **{selisih} hari** ({tgl_jt}).")
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
    
    for i in range(len(col_widths)):
        table_data[0][i].style.textColor = colors.whitesmoke

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
    
    for i in range(len(col_widths)):
        table_data[0][i].style.textColor = colors.whitesmoke

    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# --- TOGGLE MODE DI SIDEBAR ---
with st.sidebar:
    st.markdown("### 🛒 TOSERBA")
    st.markdown("<p style='font-size: 12px; margin-top: -5px;'>NURJA BERKAH<br>Belanja Lengkap, Keluarga Bahagia</p>", unsafe_allow_html=True)
    st.divider()
    
    theme_choice = st.radio("Pilih Mode", ["Terang ☀️", "Gelap 🌙"], index=0 if st.session_state.theme == "Terang" else 1, label_visibility="collapsed")
    st.session_state.theme = "Terang" if "Terang" in theme_choice else "Gelap"
    
    st.divider()
    
    menu_pilihan = st.radio(
        "Menu Utama",
        ["🏠 Home", "📦 Input Retur", "📋 List Retur", "🏢 Data Supplier", "📊 Laporan", "⚙️ Pengaturan"]
    )
    
    st.divider()
    st.markdown("👤 **Admin Gudang**")
    if st.button("🚪 Keluar Sistem", use_container_width=True):
        st.info("Sistem terkunci.")

# --- CSS DINAMIS BERDASARKAN TEMA ---
if st.session_state.theme == "Gelap":
    st.markdown('''
        <style>
        .stApp { background-color: #0F172A; color: #F8FAFC; }
        [data-testid="stSidebar"] { background-color: #1E293B; padding-top: 1rem; }
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label { color: #F8FAFC !important; }
        h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; }
        p, span, label { color: #E2E8F0; }
        .stButton button[kind="primary"] { background-color: #2563EB; color: white; border-radius: 8px; font-weight: 600; border: none; }
        .stButton button[kind="primary"]:hover { background-color: #1D4ED8; }
        </style>
    ''', unsafe_allow_html=True)
    plotly_template = "plotly_dark"
else:
    st.markdown('''
        <style>
        .stApp { background-color: #F8FAFC; color: #0F172A; }
        [data-testid="stSidebar"] { background-color: #0F172A; padding-top: 1rem; }
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label { color: #E2E8F0 !important; }
        h1, h2, h3, h4, h5, h6 { color: #0F172A !important; }
        p, span, label { color: #334155; }
        .stButton button[kind="primary"] { background-color: #2563EB; color: white; border-radius: 8px; font-weight: 600; border: none; }
        .stButton button[kind="primary"]:hover { background-color: #1D4ED8; }
        </style>
    ''', unsafe_allow_html=True)
    plotly_template = "plotly"

DAFTAR_SUPPLIER = [
    "Belum Tau", "PT ARTABOGA (Hanif)", "PT. PANGAN LESTARI (Ratna)", "SINAR SURYA SUKSES (Adhit)",
    "PT Borwita Citra Prima (Listin)", "PT. SINAR NIAGA SEJAHTERA (Angga)", "PT SINARMAS DISTRIBUSI NUSANTARA (Mathias)",
    "PT Eka Artha Buana Darmawan (Unilever)", "PT Eka Artha Buana Darmawan (Nestle)", "TRI USAHA JAYA",
    "PT BAHAGIA INTRA NIAGA (Onky)", "PT Pinus Merah Abadi (Bayuhan)", "PT JAPFA FOOD INDONESIA (Uwais)",
    "PT BUKIT MAKMUR INTI ABADI (Badrus)", "PT Dinamika Daya Segara", "PT SUBUR MITRA SUKSES (Taufiq)",
    "PT AJINOMOTO SALES INDONESIA (Rosi)", "PT TIGARAKSA SENTOSA", "PT Masamedi Intifarm Indo (Romeo)",
    "PT DISTRINDO AMAN SEJAHTERA (Agus)", "PT BINA SAN PRIMA (Alfia)", "PT LIVIA MANURI SEJATI (Aldi)",
    "PT SUMBER BARU NIAGA (Tomi)", "PT ANDATU MULIA LESTARI (Muhammad Haris)", "PT JAVAS TRIPTA MANDALA (Roby)",
    "PT KHINGGUAN (Ima)", "PT TIRTA PRIMA RASA (Dwi)", "PT VICTORIA CARE INDONESIA TBK (Saryono)",
    "PT FARMA NIAGA DISTRIBUSINDO", "PT TARUNAKUSUMA (Wasik)", "PT SEKAWAN KOSMETIK WASANTARA (Ainun)",
    "PT SAKTISETIA SANTOSA", "SINAR SURYA UTAMA", "CV SINAR TERANG (Gontor)", "PT SEMESTANUSTRA DISTRINDO (Imron)",
    "PT PELITA NUSA RAYA (Yulio)", "PT Fastra Buana Kanfans (Abdul)", "UD PILAR MAKMUR", "PT WIRA SADANA LESTARI (Yono)",
    "PT SAI (Yuli)", "Nova (Ari)", "PT SNACK (Rizky/Tris)", "UD ARJO JAYA (Aldi)", "COCA COLA",
    "PT PERUSAHAAN DAGANG TEMPO", "UD KENCONO WUNGU (Opium)", "PT CIPTA NIAGA SEMESTA", "PUNGGING ELECTRIC",
    "PT Unirama Duta Niaga (Amru)", "PT TUMBAKMAS NIAGA (Hasan)", "PT SUPRALITA MANDIRI (Farida)",
    "PT Surya Gemilang Lestari Sentosa (Davina)", "PT ASIA PARAMITA INDAH (Andhie)", "PT PUJI SURYA INDAH (Qomari)",
    "PT MANOHARA ADIKA DISTRINDO (Deni)", "UD SRI REJEKI (Sumar)", "CV SINAR ASIA PERKASA (Valentinus)",
    "Toserba Sundra (Kaesang)", "PT PANCA PILAR (Aru)", "PT INDOMARCO ADI PRIMA", "PT KEVINDO PRATAMA PERKASA",
    "PT ARTA DWITUNGGAL ABADI (Febri)", "DC NURUL JADID", "CV Belva", "PT HARSI PANGAN UTAMA", "BORNEO",
    "EGIZ UMKM (Ibu Riz)", "UD Mentari Jaya Putra", "AIRA", "PT KIAN RAGAM DISTRIBUTOR", "OPIK PUTRA SNACK", "CV PUMA UTAMA MAKMUR ARTARIA",
    "PT PRAKARSA JAYA SENTOSA", "HELLO (Memenuhi Selera Anda)", "HASAN MEJA", "PT CAMPINA ICE CREAM INDUSTRY",
    "Yakult", "PT LUKINDARI PERMATA", "PT PARIMAS BOGA RAYA", "CV NUGRAHENI KARTIKA SARI DRINGU", "AZKA BAROKAH",
    "REJEKI JAYA", "DWIKARYA INDONESIA MANDIRI", "PT GOLDEN AICE", "BERKAH HS", "PT Mitra Pharmasi Jaya",
    "INDOWANGI PARFUM", "CV Argo Bentar Gemilang", "UD ANUGERAH JAYA PROBOLINGGO", "PT SUKANDA DJAYA", "CV KARTIKA JAYA MAKMUR",
    "PT ULTRAJAYA MILK INDUSTRI & TRADING CO. TBK", "Bulog Indonesia", "UD HARIS JAYA PROBOLINGGO", "Jaya Subur",
    "PADMATIRTA", "PT PABRIK MINYAK PERNIAGA DAN INDUSTRI IKAN DORANG", "MARGA NUSARAYA"
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

@st.dialog("🔔 Peringatan Jatuh Tempo Supplier")
def dialog_notifikasi_jatuh_tempo():
    st.markdown("### Daftar Peringatan Jatuh Tempo")
    if not notif_jatuh_tempo:
        st.success("Tidak ada tagihan supplier yang mendekati atau melewati jatuh tempo.")
    else:
        for n in notif_jatuh_tempo:
            st.markdown(f"- {n}")
    if st.button("Tutup", use_container_width=True, type="primary"):
        st.rerun()

# --- HEADER DENGAN IKON LONCENG NOTIFIKASI ---
head_c1, head_c2 = st.columns([10, 1])
with head_c1:
    st.markdown("## 🏢 Sistem Manajemen Retur & Supplier")
with head_c2:
    st.markdown("<br>", unsafe_allow_html=True)
    jml_notif = len(notif_jatuh_tempo)
    label_lonceng = f"🔔 {jml_notif}" if jml_notif > 0 else "🔔"
    if st.button(label_lonceng, help="Cek Peringatan Jatuh Tempo"):
        dialog_notifikasi_jatuh_tempo()

st.divider()

# ==========================================
# MENU 1: INPUT RETUR
# ==========================================
if menu_pilihan == "📦 Input Retur":
    st.markdown("## 📦 Input Barang Retur")
    st.markdown("<p style='margin-top: -10px;'>Formulir pencatatan barang retur baru ke database sistem.</p>", unsafe_allow_html=True)
    
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
        
        submit_retur = st.form_submit_button("💾 Simpan Data Retur", type="primary")
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
    st.markdown("### 📋 Riwayat Retur Terbaru")
    df_history = ambil_data_retur()
    if not df_history.empty:
        st.dataframe(df_history.tail(10), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data retur.")

# ==========================================
# MENU 2: LIST RETUR
# ==========================================
elif menu_pilihan == "📋 List Retur":
    st.markdown("## 📋 List Data Retur & Manajemen Edit")
    st.markdown("<p style='margin-top: -10px;'>Filter data retur berdasarkan supplier/status, edit langsung tabel, simpan perubahan, atau cetak laporan PDF per supplier.</p>", unsafe_allow_html=True)
    
    fl_c1, fl_c2, fl_c3 = st.columns(3)
    with fl_c1:
        opsi_supp_filter = ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER
        pilih_sup_filter = st.selectbox("Filter Supplier", opsi_supp_filter)
    with fl_c2:
        pilih_status_filter = st.selectbox("Filter Status", ["SEMUA STATUS", "Pengajuan", "Sedang Diproses", "Sukses"])
    with fl_c3:
        cari_retur_input = st.text_input("🔍 Cari Data Retur (Kode / Nama / Keterangan)")

    df_retur_view = ambil_data_retur(filter_supplier=pilih_sup_filter, filter_status=pilih_status_filter, cari=cari_retur_input)

    if not df_retur_view.empty:
        pdf_bytes = generate_pdf_retur_custom(df_retur_view, pilih_sup_filter)
        st.download_button(
            label=f"📥 Download Laporan PDF ({pilih_sup_filter})",
            data=pdf_bytes,
            file_name=f"Laporan_Retur_{pilih_sup_filter.replace(' ', '_')}_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("### ✏️ Edit Data Retur")
        st.markdown("<p style='font-size: 13px; color: gray;'>Anda dapat langsung mengubah data (Qty, HPP, Status, Keterangan, dll) di tabel bawah ini, lalu klik tombol Simpan Perubahan.</p>", unsafe_allow_html=True)

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

        st.markdown("### 🛠️ Aksi Data Retur")
        list_retur_ids = df_retur_view["id"].tolist()
        selected_retur_ids = st.multiselect("Pilih ID Retur (untuk Hapus):", options=list_retur_ids, key="multiselect_retur_id")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("💾 Simpan Perubahan Data Retur", type="primary", use_container_width=True):
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
                    st.rerun()
                else:
                    st.info("Tidak ada perubahan data retur yang terdeteksi.")
        with col_r2:
            if st.button("🗑️ Hapus Retur Terpilih", type="secondary", use_container_width=True):
                if not selected_retur_ids:
                    st.warning("Pilih minimal satu ID retur yang ingin dihapus!")
                else:
                    for rid in selected_retur_ids:
                        try:
                            supabase.table("barang_retur").delete().eq("id", int(float(str(rid)))).execute()
                        except (ValueError, TypeError):
                            continue
                    st.success("Data retur terpilih berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Tidak ada data retur yang ditemukan sesuai filter.")
        # ... (kode Anda yang lain di atas) ...

# ==========================================
# MENU 2: INPUT PEMBELIAN SUPPLIER (TAMBAHAN)
# ==========================================
elif menu_pilihan == "🛒 Input Pembelian Supplier":
    st.markdown("## 🛒 Input Pembelian Supplier")
    
    with st.form("form_input_pembelian", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            f_supplier = st.selectbox("Nama Supplier", [
                "PT ARTABOGA (Hanif)", "PT. PANGAN LESTARI (Ratna)", "SINAR SURYA SUKSES (Adhit)",
                "PT Borwita Citra Prima (Listin)", "PT. SINAR NIAGA SEJAHTERA (Angga)", 
                "PT SINARMAS DISTRIBUSI NUSANTARA (Mathias)", "TRI USAHA JAYA"
            ])
            f_amount = st.number_input("Nominal Tagihan (Rp)", min_value=0.0, step=1000.0)
        with col2:
            f_tgl_datang = st.date_input("Tanggal Datang")
            f_tgl_tempo = st.date_input("Jatuh Tempo")
        
        f_status = st.selectbox("Status Lunas", ["menunggu tanggal tempo", "lunas"])
        
        if st.form_submit_button("💾 Simpan Data Pembelian", type="primary"):
            try:
                data = {
                    "supplier_name": str(f_supplier),
                    "amount": float(f_amount),
                    "tanggal_datang": str(f_tgl_datang),
                    "jatuh_tempo": str(f_tgl_tempo),
                    "status_lunas": str(f_status)
                }
                supabase.table("supplier_invoices").insert(data).execute()
                st.success("Data pembelian berhasil disimpan!")
            except Exception as e:
                st.error(f"Gagal menyimpan data: {e}")

    st.divider()
    st.subheader("📋 Riwayat Pembelian")
    # Memanggil fungsi ambil data dari Supabase
    df_riwayat = ambil_data_invoice_supplier() 
    if not df_riwayat.empty:
        st.dataframe(df_riwayat, use_container_width=True)

# ==========================================
# MENU LAIN (INPUT RETUR, DLL)
# ==========================================
elif menu_pilihan == "📦 Input Retur":
    # ... (kode lama Anda tetap di sini) ...

# ==========================================
# MENU 3: DATA SUPPLIER
# ==========================================
elif menu_pilihan == "🏢 Data Supplier":
    st.markdown("## 🏢 Manajemen Data Supplier")
    st.markdown("<p style='margin-top: -10px;'>Kelola informasi supplier, nomor urut, nominal tagihan, status PKP/Non-PKP, sistem pembayaran, serta tanggal jatuh tempo.</p>", unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Data Supplier Baru", expanded=True):
        with st.form("form_tambah_supplier", clear_on_submit=True):
            sc1, sc2 = st.columns(2)
            with sc1:
                s_nourut = st.number_input("No Urut", min_value=1, value=1)
                s_nama = st.selectbox("Nama Supplier", DAFTAR_SUPPLIER)
                s_tagihan = st.number_input("Total Tagihan (Rp)", min_value=0.0, value=0.0, step=1000.0)
            with sc2:
                s_pajak = st.selectbox("Jenis Pendaftaran", ["Non-PKP", "PKP"])
                s_bayar = st.selectbox("Sistem Pembayaran", ["Kredit", "Transfer"])
                s_jatuhtempo = st.date_input("Tanggal Jatuh Tempo", value=datetime.date.today() + datetime.timedelta(days=30))
            
            submit_sup = st.form_submit_button("💾 Simpan Supplier", type="primary")
            if submit_sup:
                try:
                    payload_sup = {
                        "no_urut": int(s_nourut),
                        "nama_supplier": str(s_nama),
                        "tagihan": float(s_tagihan),
                        "jenis_pajak": str(s_pajak),
                        "sistem_bayar": str(s_bayar),
                        "jatuh_tempo": str(s_jatuhtempo)
                    }
                    supabase.table("data_supplier").insert(payload_sup).execute()
                    st.success("Data supplier berhasil disimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan ke database: {e}")

    st.divider()
    
    ex_c1, ex_c2 = st.columns([2, 1])
    with ex_c1:
        cari_sup = st.text_input("🔍 Cari Supplier (Nama / Pajak / Sistem Bayar)")
    with ex_c2:
        st.markdown("<br>", unsafe_allow_html=True)
        pilihan_filter_pdf = st.selectbox("Pilihan Ekspor PDF Supplier", ["SEMUA", "PKP", "Non-PKP"], label_visibility="collapsed")

    df_supplier_view = ambil_data_supplier(cari_sup)

    if not df_supplier_view.empty:
        if pilihan_filter_pdf == "PKP":
            df_pdf = df_supplier_view[df_supplier_view["jenis_pajak"].str.upper() == "PKP"]
        elif pilihan_filter_pdf == "Non-PKP":
            df_pdf = df_supplier_view[df_supplier_view["jenis_pajak"].str.upper() == "NON-PKP"]
        else:
            df_pdf = df_supplier_view

        pdf_bytes = generate_pdf_supplier(df_pdf, pilihan_filter_pdf)
        st.download_button(
            label=f"📥 Download Laporan PDF Supplier ({pilihan_filter_pdf})",
            data=pdf_bytes,
            file_name=f"Laporan_Supplier_{pilihan_filter_pdf}_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        edited_df_sup = st.data_editor(
            df_supplier_view,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "no_urut": st.column_config.NumberColumn("No Urut"),
                "nama_supplier": st.column_config.TextColumn("Nama Supplier"),
                "tagihan": st.column_config.NumberColumn("Tagihan", format="Rp %'d"),
                "jenis_pajak": st.column_config.SelectboxColumn("Jenis Pendaftaran", options=["Non-PKP", "PKP"], required=True),
                "sistem_bayar": st.column_config.SelectboxColumn("Sistem Pembayaran", options=["Kredit", "Transfer"], required=True),
                "jatuh_tempo": st.column_config.DateColumn("Jatuh Tempo"),
            },
            disabled=["id"],
            hide_index=True,
            use_container_width=True,
            key="editor_tabel_supplier"
        )

        st.markdown("### 🛠️ Aksi Data Supplier")
        list_sup_ids = df_supplier_view["id"].tolist()
        selected_sup_ids = st.multiselect("Pilih ID Supplier (untuk Simpan Perubahan / Hapus):", options=list_sup_ids, key="multiselect_sup_id")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Simpan Perubahan Data Supplier", type="primary", use_container_width=True):
                count_upd = 0
                for _, row in edited_df_sup.iterrows():
                    orig_row = df_supplier_view.loc[df_supplier_view["id"] == row["id"]]
                    if not orig_row.empty:
                        orig = orig_row.iloc[0]
                        if (
                            int(row["no_urut"]) != int(orig["no_urut"]) or
                            str(row["nama_supplier"]) != str(orig["nama_supplier"]) or
                            float(row["tagihan"]) != float(orig["tagihan"]) or
                            str(row["jenis_pajak"]) != str(orig["jenis_pajak"]) or
                            str(row["sistem_bayar"]) != str(orig["sistem_bayar"]) or
                            str(row["jatuh_tempo"]) != str(orig["jatuh_tempo"])
                        ):
                            supabase.table("data_supplier").update({
                                "no_urut": int(row["no_urut"]),
                                "nama_supplier": str(row["nama_supplier"]),
                                "tagihan": float(row["tagihan"]),
                                "jenis_pajak": str(row["jenis_pajak"]),
                                "sistem_bayar": str(row["sistem_bayar"]),
                                "jatuh_tempo": str(row["jatuh_tempo"])
                            }).eq("id", int(row["id"])).execute()
                            count_upd += 1
                if count_upd > 0:
                    st.success(f"Berhasil memperbarui {count_upd} data supplier!")
                    st.rerun()
                else:
                    st.info("Tidak ada perubahan data supplier yang terdeteksi.")
        with col_s2:
            if st.button("🗑️ Hapus Supplier Terpilih", type="secondary", use_container_width=True):
                if not selected_sup_ids:
                    st.warning("Pilih minimal satu ID supplier untuk dihapus!")
                else:
                    for sid in selected_sup_ids:
                        supabase.table("data_supplier").delete().eq("id", int(sid)).execute()
                    st.success("Supplier terpilih berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Tidak ada data supplier yang ditemukan.")
