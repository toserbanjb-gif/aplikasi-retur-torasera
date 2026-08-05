import datetime
from io import BytesIO
import re
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from supabase import Client, create_client

# --- CONFIG PAGE ---
st.set_page_config(
    page_title="Sistem Manajemen Barang - Torasera Nurja Berkah",
    page_icon="📦",
    layout="wide",
)

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
    "Jaya Subur",
    "PADMATIRTA",
    "PT PABRIK MINYAK PERNIAGA DAN INDUSTRI IKAN DORANG",
]
DAFTAR_STATUS = ["Pengajuan", "Sedang Diverifikasi", "Sukses"]


def ambil_data_retur(filter_supplier="SEMUA SUPPLIER", filter_status="SEMUA STATUS", cari=""):
    # Mengambil semua kolom termasuk mengantisipasi variasi kapitalisasi id
    query = supabase.table("barang_retur").select("*")
    if filter_supplier and filter_supplier != "SEMUA SUPPLIER":
        query = query.eq("supplier", filter_supplier)
    if filter_status and filter_status != "SEMUA STATUS":
        query = query.eq("status", filter_status)
    
    response = query.execute()

    if not response.data:
        return pd.DataFrame(columns=["id", "kode", "nama", "qty", "hpp", "total", "ket", "ed", "supplier", "status", "tgl_input"])

    df = pd.DataFrame(response.data)

    # Normalisasi nama kolom menjadi huruf kecil semua agar seragam (misal 'ID' jadi 'id')
    df.columns = [str(c).lower() for c in df.columns]

    # Pastikan kolom id benar-benar ada, jika tidak buat kolom id default
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


def parse_pasted_retur_data(pasted_text):
    lines = [line.strip() for line in pasted_text.strip().split("\n") if line.strip()]
    if not lines:
        return pd.DataFrame()

    parsed_rows = []
    for line in lines:
        cols = re.split(r"\t+|\s{2,}", line)
        if len(cols) >= 2:
            if any(h in cols[0].lower() or (len(cols) > 1 and h in cols[1].lower()) for h in ["pilih", "id", "kode", "status", "barang"]):
                continue

            def clean_num(val):
                v = re.sub(r"[^\d.]", "", str(val).replace(",", "."))
                try:
                    return float(v) if "." in v else int(v) if v else 0
                except:
                    return 0

            clean_cols = []
            for c in cols:
                if c in ["True", "False", ""]:
                    continue
                clean_cols.append(c)

            if clean_cols and clean_cols[0].isdigit() and len(clean_cols[0]) <= 5 and not clean_cols[0].startswith("8"):
                clean_cols.pop(0)

            if len(clean_cols) < 2:
                continue

            kode = clean_cols[0] if len(clean_cols) > 0 else "-"
            nama = clean_cols[1] if len(clean_cols) > 1 else "Barang Retur"
            qty = int(clean_num(clean_cols[2])) if len(clean_cols) > 2 and clean_num(clean_cols[2]) > 0 else 1
            hpp = clean_num(clean_cols[3]) if len(clean_cols) > 3 else 0
            
            ket = "Rusak"
            ed = "-"
            supp_parsed = None
            stat_parsed = "Pengajuan"

            if len(clean_cols) > 5 and not clean_cols[4].replace('.', '', 1).isdigit():
                ket = clean_cols[4]
                ed = clean_cols[5] if len(clean_cols) > 5 else "-"
            else:
                if len(clean_cols) > 5:
                    ket = clean_cols[5]
                if len(clean_cols) > 6:
                    ed = clean_cols[6]
                if len(clean_cols) > 7:
                    supp_parsed = clean_cols[7]
                if len(clean_cols) > 8:
                    stat_parsed = clean_cols[8]

            subtotal = qty * hpp

            parsed_rows.append({
                "Kode": kode,
                "Nama Barang": nama,
                "Qty": qty,
                "HPP": hpp,
                "Total": subtotal,
                "Keterangan": ket,
                "ED": ed,
                "Supplier": supp_parsed,
                "Status": stat_parsed
            })

    return pd.DataFrame(parsed_rows)


def generate_pdf_retur(df_data, supplier_label):
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

    company_style = ParagraphStyle(
        "Company", parent=styles["Heading2"], fontSize=14, alignment=1, spaceAfter=2, fontName="Helvetica-Bold"
    )
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"], fontSize=12, alignment=1, spaceAfter=10, textColor=colors.HexColor("#2B6CB0"), fontName="Helvetica-Bold"
    )
    normal_style = ParagraphStyle("Text", parent=styles["Normal"], fontSize=9)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)
    cell_center = ParagraphStyle("CellCenter", parent=styles["Normal"], fontSize=8, alignment=1, leading=10)
    cell_right = ParagraphStyle("CellRight", parent=styles["Normal"], fontSize=8, alignment=2, leading=10)

    story.append(Paragraph("TORASERA NURJA BERKAH", company_style))
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
    for _, r in df_data.iterrows():
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
    st.markdown(
        f"""
    - **Jumlah barang terpilih:** `{len(id_list)}` item
    - **Tindakan:** Status diubah menjadi **{status_baru}**, dan **Qty** serta **Total** nominal retur barang tersebut akan **otomatis diubah menjadi 0**.
    """
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Ya, Benar Disetujui", type="primary", use_container_width=True):
            for item_id in id_list:
                if status_baru == "Sukses":
                    supabase.table("barang_retur").update({"status": status_baru, "qty": 0, "total": 0}).eq("id", int(item_id)).execute()
                else:
                    supabase.table("barang_retur").update({"status": status_baru}).eq("id", int(item_id)).execute()

            st.success(f"Berhasil memperbarui status barang menjadi '{status_baru}'!")
            st.rerun()

    with col2:
        if st.button("❌ Batal", use_container_width=True):
            st.rerun()


# --- TAMPILAN UTAMA HALAMAN RETUR BARANG ---
st.title("📦 Retur Barang - Torasera Nurja Berkah")

df_semua = ambil_data_retur()
if not df_semua.empty:
    st.markdown("### 📊 Analisis & Grafik Retur Overall")
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("**Total Nominal Retur per Supplier**")
        top_sup_retur = df_semua.groupby("supplier")["total"].sum().reset_index().sort_values(by="total", ascending=False).head(10)
        st.bar_chart(top_sup_retur.set_index("supplier"))

    with g_col2:
        st.markdown("**Status Pengajuan Retur**")
        status_dist = df_semua.groupby("status")["id"].count().reset_index().rename(columns={"id": "jumlah"})
        st.bar_chart(status_dist.set_index("status"))

st.divider()

with st.expander("➕ Tambah Barang Retur Baru (Satuan, Copy-Paste, & CSV)", expanded=False):
    tab_form_satuan, tab_form_paste, tab_form_csv = st.tabs(["📝 Input Satuan Manual", "📋 Copy-Paste Data", "📁 Upload File CSV"])

    with tab_form_satuan:
        with st.form("form_tambah_retur", clear_on_submit=True):
            f_in_sup = st.selectbox("Supplier", DAFTAR_SUPPLIER, key="satuan_sup")
            
            c1, c2 = st.columns(2)
            with c1:
                f_in_kode = st.text_input("Kode / Barcode")
            with c2:
                f_in_qty = st.number_input("Qty", min_value=1, value=1)

            c3, c4 = st.columns(2)
            with c3:
                f_in_nama = st.text_input("Nama Barang")
            with c4:
                f_in_hpp = st.number_input("HPP (Rp)", min_value=0.0, value=0.0, step=500.0)

            c5, c6, c7 = st.columns(3)
            with c5:
                f_in_ket = st.selectbox("Keterangan (sesuai ED / Rusak)", ["Rusak", "ED", "Lainnya"])
            with c6:
                f_in_ed = st.text_input("ED (Contoh: 2026-12-31 atau -)", value="-")
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
                    
                    total_val = f_in_qty * f_in_hpp if f_in_status != "Sukses" else 0
                    payload = {
                        "supplier": f_in_sup,
                        "kode": f_in_kode if f_in_kode else "-",
                        "nama": f_in_nama,
                        "qty": f_in_qty if f_in_status != "Sukses" else 0,
                        "hpp": f_in_hpp,
                        "total": total_val,
                        "ket": f_in_ket,
                        "ed": f_in_ed,
                        "status": f_in_status,
                        "tgl_input": str(datetime.date.today())
                    }
                    supabase.table("barang_retur").insert(payload).execute()
                    st.success("Barang retur berhasil ditambahkan!")
                    st.rerun()

    with tab_form_paste:
        st.subheader("📋 Input Retur Massal via Copy-Paste")
        paste_sup_default = st.selectbox("Pilih Supplier Default", DAFTAR_SUPPLIER, key="paste_sup_target")
        raw_paste_text = st.text_area("Paste Baris Tabel Retur di Sini:", height=150)

        if raw_paste_text:
            df_parsed_retur = parse_pasted_retur_data(raw_paste_text)
            if not df_parsed_retur.empty:
                st.dataframe(df_parsed_retur, use_container_width=True)
                if st.button("💾 Simpan Semua Data Paste ke Database Retur", type="primary"):
                    records_to_insert = []
                    for _, r in df_parsed_retur.iterrows():
                        final_supp = r["Supplier"] if r["Supplier"] and r["Supplier"] in DAFTAR_SUPPLIER else paste_sup_default
                        final_stat = r["Status"] if r["Status"] in DAFTAR_STATUS else "Pengajuan"
                        
                        records_to_insert.append({
                            "supplier": final_supp,
                            "kode": str(r["Kode"]),
                            "nama": str(r["Nama Barang"]),
                            "qty": int(r["Qty"]),
                            "hpp": float(r["HPP"]),
                            "total": float(r["Total"]),
                            "ket": str(r["Keterangan"]),
                            "ed": str(r["ED"]),
                            "status": final_stat,
                            "tgl_input": str(datetime.date.today())
                        })
                    supabase.table("barang_retur").insert(records_to_insert).execute()
                    st.success(f"Berhasil menyimpan {len(records_to_insert)} item barang retur!")
                    st.rerun()

    with tab_form_csv:
        st.subheader("📁 Upload File CSV Retur Barang")
        csv_sup_default = st.selectbox("Pilih Supplier Default untuk File CSV", DAFTAR_SUPPLIER, key="csv_sup_target")
        uploaded_csv = st.file_uploader("Pilih file CSV", type=["csv"])

        if uploaded_csv is not None:
            df_csv = pd.read_csv(uploaded_csv)
            st.dataframe(df_csv.head(5), use_container_width=True)
            if st.button("💾 Proses & Simpan Data CSV ke Database", type="primary"):
                records_to_insert = []
                df_csv.columns = [str(c).strip().lower() for c in df_csv.columns]
                for _, row in df_csv.iterrows():
                    records_to_insert.append({
                        "supplier": csv_sup_default,
                        "kode": str(row.get("kode", "-")),
                        "nama": str(row.get("nama", "Barang")),
                        "qty": int(row.get("qty", 1)),
                        "hpp": float(row.get("hpp", 0)),
                        "total": int(row.get("qty", 1)) * float(row.get("hpp", 0)),
                        "ket": str(row.get("ket", "Rusak")),
                        "ed": str(row.get("ed", "-")),
                        "status": "Pengajuan",
                        "tgl_input": str(datetime.date.today())
                    })
                supabase.table("barang_retur").insert(records_to_insert).execute()
                st.success("Berhasil mengimpor CSV!")
                st.rerun()

st.divider()

f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    filter_sup = st.selectbox("Filter Supplier", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER, key="f_sup_retur")
with f_col2:
    filter_stat = st.selectbox("Filter Status", ["SEMUA STATUS"] + DAFTAR_STATUS, key="f_stat_retur")
with f_col3:
    filter_cari = st.text_input("🔍 Cari Kode / Nama / Ket / Supplier / Status", key="f_cari_retur")

df_retur = ambil_data_retur(filter_sup, filter_stat, filter_cari)

st.markdown("### 📋 Daftar Barang Retur")

if not df_retur.empty:
    if "selected_rows" not in st.session_state:
        st.session_state.selected_rows = []

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

    st.markdown("### ⚡ Ubah Status Pengajuan (Pilih Massal / Satu-satu)")
    list_all_ids = df_retur["id"].tolist()
    selected_ids = st.multiselect("Pilih ID Barang Retur yang Akan Diubah Statusnya:", options=list_all_ids, default=st.session_state.get("selected_rows", []))
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        status_baru_massal = st.selectbox("Pilih Status Baru:", DAFTAR_STATUS, key="status_massal_input")
    with col_s2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_ubah_status = st.button("Ubah Status Barang Terpilih", type="primary", use_container_width=True)

    if btn_ubah_status:
        if not selected_ids:
            st.warning("Silakan pilih minimal satu barang terlebih dahulu!")
        else:
            if status_baru_massal == "Sukses":
                dialog_konfirmasi_setujui(selected_ids, status_baru_massal)
            else:
                for item_id in selected_ids:
                    supabase.table("barang_retur").update({"status": status_baru_massal}).eq("id", int(item_id)).execute()
                st.success(f"Berhasil memperbarui status menjadi '{status_baru_massal}'!")
                st.rerun()

    st.divider()

    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("💾 Update Detail Edit Manual", use_container_width=True):
            for _, row in edited_df.iterrows():
                try:
                    raw_id = row["id"]
                    if pd.isna(raw_id):
                        continue
                    item_id = int(float(str(raw_id)))
                except (ValueError, TypeError):
                    continue

                new_total = row["qty"] * row["hpp"] if row["status"] != "Sukses" else 0
                new_qty = row["qty"] if row["status"] != "Sukses" else 0
                
                supabase.table("barang_retur").update({
                    "kode": str(row["kode"]),
                    "nama": str(row["nama"]),
                    "qty": int(new_qty),
                    "hpp": float(row["hpp"]),
                    "total": float(new_total),
                    "ket": str(row["ket"]),
                    "ed": str(row["ed"]),
                    "supplier": str(row["supplier"]),
                    "status": str(row["status"])
                }).eq("id", item_id).execute()
                
            st.success("Perubahan data berhasil disimpan!")
            st.rerun()

    with col_act2:
        if st.button("🗑️ Hapus Data Retur Terpilih", use_container_width=True, type="secondary"):
            if not selected_ids:
                st.warning("Pilih data yang ingin dihapus terlebih dahulu.")
            else:
                for item_id in selected_ids:
                    supabase.table("barang_retur").delete().eq("id", int(item_id)).execute()
                st.success("Data berhasil dihapus!")
                st.rerun()
else:
    st.info("Tidak ada data barang retur yang ditemukan di database atau sesuai filter. Silakan tambah data baru melalui menu di atas.")

st.divider()

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
