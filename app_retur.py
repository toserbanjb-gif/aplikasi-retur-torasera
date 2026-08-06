import datetime
from io import BytesIO
import re
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client

# --- CONFIG PAGE ---
st.set_page_config(
    page_title="Sistem Manajemen Retur - Toserba Nurja Berkah",
    page_icon="📦",
    layout="wide",
)

# --- INISIALISASI STATE THEME ---
if "theme" not in st.session_state:
    st.session_state.theme = "Terang"

# --- TOGGLE MODE DI SIDEBAR ---
with st.sidebar:
    st.markdown("### 🛒 TOSERBA")
    st.markdown("<p style='font-size: 12px; margin-top: -5px;'>NURJA BERKAH<br>Belanja Lengkap, Keluarga Bahagia</p>", unsafe_allow_html=True)
    st.divider()
    
    # Tombol Ganti Tema
    st.markdown("🎨 **Tampilan Tema**")
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
    st.markdown("""
        <style>
        .stApp {
            background-color: #0F172A;
            color: #F8FAFC;
        }
        [data-testid="stSidebar"] {
            background-color: #1E293B;
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label {
            color: #F8FAFC !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #F8FAFC !important;
        }
        p, span, label {
            color: #E2E8F0;
        }
        .stButton button[kind="primary"] {
            background-color: #2563EB;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            border: none;
        }
        .stButton button[kind="primary"]:hover {
            background-color: #1D4ED8;
        }
        @keyframes kedapKedi {
            0% { opacity: 1; }
            50% { opacity: 0.2; }
            100% { opacity: 1; }
        }
        .plotly .js-plotly-plot .traces path.js-line {
            animation: kedapKedi 1.2s infinite ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)
    plotly_template = "plotly_dark"
else:
    st.markdown("""
        <style>
        .stApp {
            background-color: #F8FAFC;
            color: #0F172A;
        }
        [data-testid="stSidebar"] {
            background-color: #0F172A;
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label {
            color: #E2E8F0 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #0F172A !important;
        }
        p, span, label {
            color: #334155;
        }
        .stButton button[kind="primary"] {
            background-color: #2563EB;
            color: white;
            border-radius: 8px;
            font-weight: 600;
            border: none;
        }
        .stButton button[kind="primary"]:hover {
            background-color: #1D4ED8;
        }
        @keyframes kedapKedi {
            0% { opacity: 1; }
            50% { opacity: 0.2; }
            100% { opacity: 1; }
        }
        .plotly .js-plotly-plot .traces path.js-line {
            animation: kedapKedi 1.2s infinite ease-in-out;
        }
        </style>
    """, unsafe_allow_html=True)
    plotly_template = "plotly"

# --- INISIALISASI SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url: str = st.secrets["SUPABASE_URL"].strip()
    key: str = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

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
    "PT AJINOMOTO SALES INDONESIA (Rosi)",
    "PT TIGARAKSA SENTOSA",
    "PT Masamedi Intifarm Indo (Romeo)",
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
    "PT SAKTISETIA SANTOSA",
    "SINAR SURYA UTAMA",
    "CV SINAR TERANG (Gontor)",
    "PT SEMESTANUSTRA DISTRINDO (Imron)",
    "PT PELITA NUSA RAYA (Yulio)",
    "PT Fastra Buana Kanfans (Abdul)",
    "UD PILAR MAKMUR",
    "PT WIRA SADANA LESTARI (Yono)",
    "PT SAI (Yuli)",
    "Nova (Ari)",
    "PT SNACK (Rizky/Tris)",
    "UD ARJO JAYA (Aldi)",
    "COCA COLA",
    "PT PERUSAHAAN DAGANG TEMPO",
    "UD KENCONO WUNGU (Opium)",
    "PT CIPTA NIAGA SEMESTA",
    "PUNGGING ELECTRIC",
    "PT Unirama Duta Niaga (Amru)",
    "PT TUMBAKMAS NIAGA (Hasan)",
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
    "PT PRAKARSA JAYA SENTOSA",
    "HELLO (Memenuhi Selera Anda)",
    "HASAN MEJA",
    "PT CAMPINA ICE CREAM INDUSTRY",
    "Yakult",
    "PT LUKINDARI PERMATA",
    "PT PARIMAS BOGA RAYA",
    "CV NUGRAHENI KARTIKA SARI DRINGU",
    "AZKA BAROKAH",
    "REJEKI JAYA",
    "DWIKARYA INDONESIA MANDIRI",
    "PT GOLDEN AICE",
    "BERKAH HS",
    "PT Mitra Pharmasi Jaya",
    "INDOWANGI PARFUM",
    "CV Argo Bentar Gemilang",
    "UD ANUGERAH JAYA PROBOLINGGO",
    "PT SUKANDA DJAYA",
    "PT ULTRAJAYA MILK INDUSTRI & TRADING CO. TBK",
    "Bulog Indonesia",
    "UD HARIS JAYA PROBOLINGGO",
    "CV Jaya Subur",
    "PADMATIRTA",
    "PT PABRIK MINYAK PERNIAGA DAN INDUSTRI IKAN DORANG",
    "MARGA NUSARAYA",
]
DAFTAR_STATUS = ["Pengajuan", "Sedang Diverifikasi", "Sukses"]

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

def cek_barang_duplikat(supplier, kode, nama):
    query = supabase.table("barang_retur").select("id, kode, nama, supplier")
    if supplier and supplier != "Belum Tau":
        query = query.eq("supplier", supplier)
    response = query.execute()
    
    if not response.data:
        return False
    
    df_existing = pd.DataFrame(response.data)
    df_existing.columns = [str(c).lower() for c in df_existing.columns]
    if df_existing.empty:
        return False
    
    kw_nama = nama.strip().lower()
    kw_kode = kode.strip().lower() if kode else ""
    
    for _, row in df_existing.iterrows():
        db_nama = str(row["nama"]).strip().lower()
        db_kode = str(row["kode"]).strip().lower() if row["kode"] else ""
        
        match_nama = (db_nama == kw_nama) and (kw_nama != "")
        match_kode = (db_kode == kw_kode) and (kw_kode != "" and kw_kode != "-")
        
        if match_nama or match_kode:
            return True
    return False

def generate_pdf_retur(df_data, supplier_label):
    df_filtered = df_data.copy()
    df_filtered["qty"] = pd.to_numeric(df_filtered["qty"], errors="coerce").fillna(0)
    df_filtered = df_filtered[
        (df_filtered["qty"] > 0) & 
        (df_filtered["status"].astype(str).str.strip().str.lower() != "sukses")
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(210 * mm, 297 * mm),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    story = []
    styles = getSampleStyleSheet()

    company_style = ParagraphStyle("Company", parent=styles["Heading2"], fontSize=14, alignment=1, spaceAfter=2, fontName="Helvetica-Bold")
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=12, alignment=1, spaceAfter=10, textColor=colors.HexColor("#2B6CB0"), fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Text", parent=styles["Normal"], fontSize=9)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)
    cell_center = ParagraphStyle("CellCenter", parent=styles["Normal"], fontSize=8, alignment=1, leading=10)
    cell_right = ParagraphStyle("CellRight", parent=styles["Normal"], fontSize=8, alignment=2, leading=10)

    story.append(Paragraph("TOSERBA NURJA BERKAH", company_style))
    story.append(Paragraph("NOTA RETUR BARANG", title_style))

    tgl = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    info_data = [[
        Paragraph(f"<b>Tgl:</b> {tgl}", normal_style),
        Paragraph(f"<b>Supplier:</b> {supplier_label}", normal_style),
    ]]
    story.append(Table(info_data, colWidths=[60 * mm, 130 * mm]))
    story.append(Spacer(1, 8))

    data_tabel = [[
        Paragraph("<b>Kode</b>", cell_center),
        Paragraph("<b>Nama Barang</b>", cell_style),
        Paragraph("<b>Qty</b>", cell_center),
        Paragraph("<b>Total (Rp)</b>", cell_right),
        Paragraph("<b>Ket.</b>", cell_center),
        Paragraph("<b>ED</b>", cell_center),
        Paragraph("<b>Status</b>", cell_center),
    ]]

    grand_total = 0
    for _, r in df_filtered.iterrows():
        data_tabel.append([
            Paragraph(str(r["kode"]), cell_center),
            Paragraph(str(r["nama"]), cell_style),
            Paragraph(str(r["qty"]), cell_center),
            Paragraph(f"{r['total']:,.0f}", cell_right),
            Paragraph(str(r["ket"]), cell_center),
            Paragraph(str(r["ed"]), cell_center),
            Paragraph(str(r.get("status", "Pengajuan")), cell_center),
        ])
        grand_total += r["total"]

    data_tabel.append([
        "", "",
        Paragraph("<b>TOTAL</b>", cell_center),
        Paragraph(f"<b>{grand_total:,.0f}</b>", cell_right),
        "", "", "",
    ])

    tabel_b = Table(data_tabel, colWidths=[28 * mm, 72 * mm, 12 * mm, 26 * mm, 17 * mm, 15 * mm, 20 * mm])
    tabel_b.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#CBD5E0")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EDF2F7")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#2B6CB0")),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(tabel_b)
    story.append(Spacer(1, 20))

    data_ttd = [
        [Paragraph("<b>Dibuat,</b>", normal_style), Paragraph("<b>Disetujui,</b>", normal_style)],
        ["\n\n\n________________________", "\n\n\n________________________"],
        [Paragraph("<b>( Admin )</b>", normal_style), Paragraph(f"<b>( {supplier_label} )</b>", normal_style)],
    ]
    tabel_ttd = Table(data_ttd, colWidths=[95 * mm, 95 * mm])
    story.append(tabel_ttd)

    doc.build(story)
    buffer.seek(0)
    return buffer

@st.dialog("⚠️ Konfirmasi Persetujuan Retur")
def dialog_konfirmasi_setujui(id_list, status_baru):
    st.warning("Apakah barang ini **benar-benar sudah disetujui** oleh supplier?")
    st.markdown(f"- **Jumlah barang terpilih:** `{len(id_list)}` item\n- **Tindakan:** Status diubah menjadi **{status_baru}**, dan **Qty** serta **Total** nominal menjadi **0**.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Ya, Benar Disetujui", type="primary", use_container_width=True):
            for item_id in id_list:
                try:
                    if pd.isna(item_id) or str(item_id).lower() == "none":
                        continue
                    valid_id = int(float(str(item_id)))
                    if status_baru == "Sukses":
                        supabase.table("barang_retur").update({"status": status_baru, "qty": 0, "total": 0}).eq("id", valid_id).execute()
                    else:
                        supabase.table("barang_retur").update({"status": status_baru}).eq("id", valid_id).execute()
                except (ValueError, TypeError):
                    continue
            st.success("Status berhasil diperbarui!")
            st.rerun()
    with col2:
        if st.button("❌ Batal", use_container_width=True):
            st.rerun()

@st.dialog("✏️ Edit Data Barang Retur")
def dialog_edit_barang(item_id):
    res = supabase.table("barang_retur").select("*").eq("id", int(item_id)).execute()
    if not res.data:
        st.error("Data tidak ditemukan!")
        if st.button("Tutup"):
            st.rerun()
        return

    data_item = res.data[0]
    sup_val = data_item.get("supplier", "Belum Tau")
    sup_idx = DAFTAR_SUPPLIER.index(sup_val) if sup_val in DAFTAR_SUPPLIER else 0
    stat_val = data_item.get("status", "Pengajuan")
    stat_idx = DAFTAR_STATUS.index(stat_val) if stat_val in DAFTAR_STATUS else 0

    with st.form("form_edit_satuan"):
        st.markdown(f"**Edit Data ID: {item_id}**")
        e_sup = st.selectbox("Supplier", DAFTAR_SUPPLIER, index=sup_idx)
        
        c1, c2 = st.columns(2)
        with c1:
            e_kode = st.text_input("Kode / Barcode", value=str(data_item.get("kode", "-")))
        with c2:
            e_qty = st.number_input("Qty", min_value=0, value=int(data_item.get("qty", 1)))

        c3, c4 = st.columns(2)
        with c3:
            e_nama = st.text_input("Nama Barang", value=str(data_item.get("nama", "")))
        with c4:
            e_hpp = st.number_input("HPP (Rp)", min_value=0.0, value=float(data_item.get("hpp", 0.0)), step=500.0)

        c5, c6, c7 = st.columns(3)
        with c5:
            e_ket = st.text_input("Keterangan", value=str(data_item.get("ket", "Rusak")))
        with c6:
            e_ed = st.text_input("ED", value=str(data_item.get("ed", "-")))
        with c7:
            e_status = st.selectbox("Status", DAFTAR_STATUS, index=stat_idx)

        submit_edit = st.form_submit_button("💾 Simpan Perubahan", type="primary")
        if submit_edit:
            is_sukses = (e_status == "Sukses")
            final_qty = 0 if is_sukses else e_qty
            total_val = 0 if is_sukses else (e_qty * e_hpp)

            supabase.table("barang_retur").update({
                "supplier": e_sup,
                "kode": e_kode if e_kode else "-",
                "nama": e_nama,
                "qty": final_qty,
                "hpp": e_hpp,
                "total": total_val,
                "ket": e_ket,
                "ed": e_ed,
                "status": e_status
            }).eq("id", int(item_id)).execute()

            st.success("Data berhasil diperbarui!")
            st.rerun()

# --- KONTEN UTAMA DASHBOARD ---
st.markdown("## 📦 Input Retur Barang")
st.markdown("<p style='margin-top: -10px;'>Kelola pencatatan dan monitoring retur barang dari supplier secara real-time.</p>", unsafe_allow_html=True)

df_semua = ambil_data_retur()

# --- 1. GRAFIK TREN DI BAGIAN ATAS ---
st.markdown("### 📈 Grafik Tren Nilai Retur over Time")
if not df_semua.empty and "tgl_input" in df_semua.columns:
    df_chart = df_semua.groupby("tgl_input")["total"].sum().reset_index()
    df_chart = df_chart.sort_values("tgl_input")

    if len(df_chart) > 1:
        nilai_awal = df_chart["total"].iloc[0]
        nilai_akhir = df_chart["total"].iloc[-1]
        
        if nilai_akhir > nilai_awal:
            warna_garis = "#EF4444"  # Merah
        else:
            warna_garis = "#22C55E"  # Hijau
    else:
        warna_garis = "#22C55E"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_chart['tgl_input'],
        y=df_chart['total'],
        mode='lines+markers',
        line=dict(color=warna_garis, width=4),
        marker=dict(size=8),
        hovertemplate='Tanggal: %{x}<br>Total: Rp %{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        xaxis_title="Tanggal Input",
        yaxis_title="Total (Rp)",
        margin=dict(l=20, r=20, t=30, b=20),
        height=380,
        template=plotly_template
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Belum cukup data tanggal untuk menampilkan grafik tren.")

st.divider()

# --- 2. STATISTIK KARTU METRIK ---
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
total_retur_count = len(df_semua)
total_supplier_count = df_semua["supplier"].nunique() if not df_semua.empty else 0
total_pending = len(df_semua[df_semua["status"] == "Pengajuan"]) if not df_semua.empty else 0
total_sukses = len(df_semua[df_semua["status"] == "Sukses"]) if not df_semua.empty else 0
grand_total_all = df_semua['total'].sum() if not df_semua.empty else 0

col_m1.metric("Total Retur", f"{total_retur_count} Item")
col_m2.metric("Supplier", f"{total_supplier_count}")
col_m3.metric("Menunggu", f"{total_pending}")
col_m4.metric("Sukses", f"{total_sukses}")
col_m5.metric("Total Nilai", f"Rp {grand_total_all:,.0f}")

st.divider()

# --- FORM INPUT & PENCATATAN ---
with st.expander("➕ Form Tambah Barang Retur Baru (Satuan & Massal)", expanded=True):
    tab_satuan, tab_paste = st.tabs(["📝 Input Satuan Manual", "📋 Copy-Paste Data"])

    with tab_satuan:
        with st.form("form_tambah_retur", clear_on_submit=True):
            f_in_sup = st.selectbox("Supplier", DAFTAR_SUPPLIER, key="satuan_sup")
            
            c1, c2 = st.columns(2)
            with c1:
                f_in_kode = st.text_input("Kode / Barcode")
            with c2:
                f_in_qty = st.number_input("Qty PCS", min_value=1, value=1)

            c3, c4 = st.columns(2)
            with c3:
                f_in_nama = st.text_input("Nama Barang")
            with c4:
                f_in_hpp = st.number_input("HPP (Rp)", min_value=0.0, value=0.0, step=500.0)

            c5, c6, c7 = st.columns(3)
            with c5:
                f_in_ket = st.selectbox("Keterangan", ["Rusak", "ED", "Salah PO", "Lainnya"])
            with c6:
                f_in_ed = st.text_input("ED (Tanggal / -)", value="-")
            with c7:
                f_in_status = st.selectbox("Status", DAFTAR_STATUS, index=0)

            submitted = st.form_submit_button("💾 Simpan Barang Retur", type="primary")
            if submitted:
                if not f_in_nama.strip():
                    st.error("Nama barang tidak boleh kosong!")
                else:
                    is_duplicate = cek_barang_duplikat(f_in_sup, f_in_kode, f_in_nama)
                    if is_duplicate:
                        st.warning("⚠️ Peringatan: Barang dengan Nama atau Kode tersebut sudah terdaftar di database untuk supplier ini!")
                        st.stop()
                    
                    is_sukses = (f_in_status == "Sukses")
                    final_qty = 0 if is_sukses else f_in_qty
                    total_val = 0 if is_sukses else (f_in_qty * f_in_hpp)

                    # Payload TANPA kolom id agar diserahkan penuh ke Identity Supabase
                    payload = {
                        "supplier": f_in_sup,
                        "kode": f_in_kode if f_in_kode else "-",
                        "nama": f_in_nama,
                        "qty": final_qty,
                        "hpp": f_in_hpp,
                        "total": total_val,
                        "ket": f_in_ket,
                        "ed": f_in_ed,
                        "status": f_in_status,
                        "tgl_input": str(datetime.date.today())
                    }
                    try:
                        supabase.table("barang_retur").insert(payload).execute()
                        st.success("Barang retur berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan pada database: {e}")

    with tab_paste:
        paste_sup_default = st.selectbox("Pilih Supplier Default", DAFTAR_SUPPLIER, key="paste_sup_target")
        raw_paste_text = st.text_area("Paste Data Tabel di Sini:", height=120)
        if raw_paste_text and st.button("💾 Proses Data Paste", type="primary"):
            st.success("Data berhasil diproses.")

st.divider()

# --- FILTER DAN PENCARIAN ---
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    filter_sup = st.selectbox("Filter Supplier", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER, key="f_sup_retur")
with f_col2:
    filter_stat = st.selectbox("Filter Status", ["SEMUA STATUS"] + DAFTAR_STATUS, key="f_stat_retur")
with f_col3:
    filter_cari = st.text_input("🔍 Cari Kode / Nama / Ket / Supplier", key="f_cari_retur")

df_retur = ambil_data_retur(filter_sup, filter_stat, filter_cari)

st.markdown("### 📋 Daftar Barang Retur")

if not df_retur.empty:
    edited_df = st.data_editor(
        df_retur,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "kode": st.column_config.TextColumn("Kode"),
            "nama": st.column_config.TextColumn("Nama Barang"),
            "qty": st.column_config.NumberColumn("Qty"),
            "hpp": st.column_config.NumberColumn("HPP", format="Rp %'d"),
            "total": st.column_config.NumberColumn("Total", format="Rp %'d"),
            "ket": st.column_config.TextColumn("Ket."),
            "ed": st.column_config.TextColumn("ED"),
            "supplier": st.column_config.TextColumn("Supplier"),
            "status": st.column_config.SelectboxColumn("Status", options=DAFTAR_STATUS, required=True),
            "tgl_input": st.column_config.TextColumn("Tgl Input", disabled=True),
        },
        disabled=["id", "tgl_input"],
        hide_index=True,
        use_container_width=True,
        key="editor_tabel_retur"
    )

    grand_total = df_retur["total"].sum()
    st.markdown(f"#### **Grand Total: Rp {grand_total:,.0f}**")
    st.divider()

    # --- KONTROL AKSI ---
    st.markdown("### 🛠️ Pengelolaan Data Terpilih")
    list_all_ids = df_retur["id"].tolist()
    selected_ids = st.multiselect("Pilih ID Barang Retur (untuk Aksi Edit / Ubah Status / Hapus):", options=list_all_ids)

    act_col1, act_col2, act_col3, act_col4 = st.columns(4)

    with act_col1:
        if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
            perubahan_tercatat = 0
            for idx, row in edited_df.iterrows():
                original_row = df_retur.loc[df_retur["id"] == row["id"]]
                if not original_row.empty:
                    orig = original_row.iloc[0]
                    if (
                        str(row["kode"]) != str(orig["kode"]) or
                        str(row["nama"]) != str(orig["nama"]) or
                        int(row["qty"]) != int(orig["qty"]) or
                        float(row["hpp"]) != float(orig["hpp"]) or
                        str(row["ket"]) != str(orig["ket"]) or
                        str(row["ed"]) != str(orig["ed"]) or
                        str(row["supplier"]) != str(orig["supplier"]) or
                        str(row["status"]) != str(orig["status"])
                    ):
                        is_sukses = (str(row["status"]) == "Sukses")
                        new_qty = 0 if is_sukses else int(row["qty"])
                        new_total = 0 if is_sukses else (int(row["qty"]) * float(row["hpp"]))

                        supabase.table("barang_retur").update({
                            "kode": str(row["kode"]),
                            "nama": str(row["nama"]),
                            "qty": new_qty,
                            "hpp": float(row["hpp"]),
                            "total": float(new_total),
                            "ket": str(row["ket"]),
                            "ed": str(row["ed"]),
                            "supplier": str(row["supplier"]),
                            "status": str(row["status"])
                        }).eq("id", int(row["id"])).execute()
                        perubahan_tercatat += 1

            if perubahan_tercatat > 0:
                st.success(f"Berhasil menyimpan perubahan untuk {perubahan_tercatat} baris!")
                st.rerun()
            else:
                st.info("Tidak ada perubahan data yang terdeteksi.")

    with act_col2:
        if st.button("✏️ Edit Data Terpilih", use_container_width=True):
            if not selected_ids or len(selected_ids) != 1:
                st.warning("Pilih tepat **1 ID** saja untuk diedit.")
            else:
                dialog_edit_barang(selected_ids[0])

    with act_col3:
        status_baru_massal = st.selectbox("Status:", DAFTAR_STATUS, key="status_massal_input", label_visibility="collapsed")
        if st.button("🔄 Ubah Status", use_container_width=True):
            if not selected_ids:
                st.warning("Pilih minimal satu ID barang!")
            else:
                if status_baru_massal == "Sukses":
                    dialog_konfirmasi_setujui(selected_ids, status_baru_massal)
                else:
                    for item_id in selected_ids:
                        try:
                            valid_id = int(float(str(item_id)))
                            supabase.table("barang_retur").update({"status": status_baru_massal}).eq("id", valid_id).execute()
                        except (ValueError, TypeError):
                            continue
                    st.success("Status berhasil diperbarui!")
                    st.rerun()

    with act_col4:
        st.markdown("")
        if st.button("🗑️ Hapus ID", type="secondary", use_container_width=True):
            if not selected_ids:
                st.warning("Pilih minimal satu ID yang ingin dihapus!")
            else:
                for item_id in selected_ids:
                    try:
                        valid_id = int(float(str(item_id)))
                        supabase.table("barang_retur").delete().eq("id", valid_id).execute()
                    except (ValueError, TypeError):
                        continue
                st.success("Data terpilih berhasil dihapus!")
                st.rerun()
else:
    st.info("Belum ada data barang retur.")

st.divider()

# --- CETAK PDF ---
st.markdown("### 🖨️ Cetak Nota Retur (PDF)")
col_pdf1, col_pdf2 = st.columns([3, 1])
with col_pdf1:
    pdf_supplier_target = st.selectbox("Pilih Supplier untuk Cetak Nota:", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER, key="pdf_sup_target")
with col_pdf2:
    st.markdown("<br>", unsafe_allow_html=True)
    df_pdf_data = ambil_data_retur(filter_supplier=pdf_supplier_target) if pdf_supplier_target != "SEMUA SUPPLIER" else df_semua
    if not df_pdf_data.empty:
        pdf_bytes = generate_pdf_retur(df_pdf_data, pdf_supplier_target)
        st.download_button(
            label="📄 Download PDF Nota Retur",
            data=pdf_bytes,
            file_name=f"Nota_Retur_{pdf_supplier_target.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.button("📄 Download PDF Kosong", disabled=True, use_container_width=True)
