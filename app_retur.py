import datetime
import io
import re
from io import BytesIO
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
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
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
DAFTAR_STATUS_PESANAN = ["Pending", "Diproses", "Selesai", "Dibatalkan"]


def parse_pasted_po_data(pasted_text):
    """Merapikan & memproses string hasil copy-paste tabel nota PO ke dalam DataFrame pandas."""
    lines = [line.strip() for line in pasted_text.strip().split("\n") if line.strip()]
    if not lines:
        return pd.DataFrame()

    parsed_rows = []
    for line in lines:
        cols = re.split(r"\t+|\s{2,}", line)
        if len(cols) >= 5:
            if any(h in cols[0].lower() or h in cols[1].lower() for h in ["no", "kode", "status", "barang"]):
                continue

            def clean_num(val):
                v = re.sub(r"[^\d.]", "", str(val).replace(",", "."))
                try:
                    return float(v) if "." in v else int(v) if v else 0
                except:
                    return 0

            kode = cols[2] if len(cols) > 2 else cols[0]
            nama = cols[5] if len(cols) > 5 else cols[1]

            hpp = clean_num(cols[6]) if len(cols) > 6 else 0
            harga_order = clean_num(cols[8]) if len(cols) > 8 else 0
            qty = int(clean_num(cols[11])) if len(cols) > 11 else int(clean_num(cols[-2])) if len(cols) > 2 else 1
            subtotal = clean_num(cols[12]) if len(cols) > 12 else clean_num(cols[-1])

            if subtotal == 0 and qty > 0 and harga_order > 0:
                subtotal = qty * harga_order

            parsed_rows.append({
                "Kode": kode,
                "Nama Barang": nama,
                "HPP": hpp,
                "Harga Order": harga_order,
                "Qty": qty,
                "Subtotal": subtotal
            })

    return pd.DataFrame(parsed_rows)


# --- FUNGSI INTERAKSI SUPABASE ---
def ambil_data_retur(filter_supplier="SEMUA SUPPLIER", filter_status="SEMUA STATUS", cari=""):
    try:
        query = supabase.table("barang_retur").select("id, kode, nama, qty, hpp, total, ket, ed, supplier, status, tgl_input")
        if filter_supplier and filter_supplier != "SEMUA SUPPLIER":
            query = query.eq("supplier", filter_supplier)
        if filter_status and filter_status != "SEMUA STATUS":
            query = query.eq("status", filter_status)
        
        response = query.execute()

        if not response.data:
            return pd.DataFrame(columns=["id", "kode", "nama", "qty", "hpp", "total", "ket", "ed", "supplier", "status", "tgl_input"])

        df = pd.DataFrame(response.data)

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
    except Exception as e:
        return pd.DataFrame(columns=["id", "kode", "nama", "qty", "hpp", "total", "ket", "ed", "supplier", "status", "tgl_input"])


def ambil_data_diskontinu(filter_supplier="SEMUA SUPPLIER", cari=""):
    try:
        query = supabase.table("barang_diskontinu").select("id, kode, nama, kategori, supplier, alasan, tgl_diskontinu")
        if filter_supplier and filter_supplier != "SEMUA SUPPLIER":
            query = query.eq("supplier", filter_supplier)
        
        response = query.execute()

        if not response.data:
            return pd.DataFrame(columns=["id", "kode", "nama", "kategori", "supplier", "alasan", "tgl_diskontinu"])

        df = pd.DataFrame(response.data)

        if cari:
            kw = cari.lower()
            df = df[
                df["kode"].astype(str).str.lower().str.contains(kw) |
                df["nama"].astype(str).str.lower().str.contains(kw) |
                df["kategori"].astype(str).str.lower().str.contains(kw) |
                df["supplier"].astype(str).str.lower().str.contains(kw) |
                df["alasan"].astype(str).str.lower().str.contains(kw)
            ]
        return df
    except Exception as e:
        return pd.DataFrame(columns=["id", "kode", "nama", "kategori", "supplier", "alasan", "tgl_diskontinu"])


def ambil_data_pesanan(filter_status="SEMUA STATUS", cari=""):
    try:
        query = supabase.table("pesanan_customer").select("id, nama_customer, no_hp, kode_barang, nama_barang, qty, harga, total, tgl_pesan, status, catatan")
        if filter_status and filter_status != "SEMUA STATUS":
            query = query.eq("status", filter_status)
            
        response = query.execute()

        if not response.data:
            return pd.DataFrame(columns=["id", "nama_customer", "no_hp", "kode_barang", "nama_barang", "qty", "harga", "total", "tgl_pesan", "status", "catatan"])

        df = pd.DataFrame(response.data)

        if cari:
            kw = cari.lower()
            df = df[
                df["nama_customer"].astype(str).str.lower().str.contains(kw) |
                df["no_hp"].astype(str).str.lower().str.contains(kw) |
                df["kode_barang"].astype(str).str.lower().str.contains(kw) |
                df["nama_barang"].astype(str).str.lower().str.contains(kw) |
                df["status"].astype(str).str.lower().str.contains(kw)
            ]
        return df
    except Exception as e:
        return pd.DataFrame(columns=["id", "nama_customer", "no_hp", "kode_barang", "nama_barang", "qty", "harga", "total", "tgl_pesan", "status", "catatan"])


# --- FUNGSI GENERATE PDF ---
def generate_pdf(df_data, supplier_label):
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


def generate_pdf_diskontinu(df_data, supplier_label):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(210 * mm, 297 * mm),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    story = []
    styles = getSampleStyleSheet()

    company_style = ParagraphStyle("Company", parent=styles["Heading2"], fontSize=15, alignment=1, spaceAfter=2, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=9, alignment=1, spaceAfter=10, textColor=colors.HexColor("#4A5568"))
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=13, alignment=1, spaceAfter=12, textColor=colors.HexColor("#C53030"), fontName="Helvetica-Bold")
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=14, spaceAfter=8)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=11)
    cell_center = ParagraphStyle("CellCenter", parent=styles["Normal"], fontSize=8, alignment=1, leading=11)

    story.append(Paragraph("TORASERA NURJA BERKAH", company_style))
    story.append(Paragraph("Jl. Raya Nurul Jadid, Paiton, Probolinggo - Jawa Timur", subtitle_style))
    story.append(Spacer(1, 5))

    story.append(Paragraph("SURAT PEMBERITAHUAN RETUR / DELIST BARANG DISKONTINU", title_style))

    tgl_surat = datetime.datetime.now().strftime("%d %B %Y")
    info_surat = [
        [Paragraph(f"<b>Tanggal:</b> {tgl_surat}", body_style)],
        [Paragraph(f"<b>Kepada Yth:</b> Pimpinan / Sales Manager {supplier_label}", body_style)],
        [Paragraph("<b>Perihal:</b> Pemberitahuan Penarikan / Retur Barang Diskontinu", body_style)],
    ]
    story.append(Table(info_surat, colWidths=[186 * mm]))
    story.append(Spacer(1, 8))

    salam_text = (
        "<b>Assalamu'alaikum Wr. Wb.</b><br/><br/>"
        "Dengan hormat,<br/>"
        "Bersama surat ini, kami dari pihak manajemen <b>Torasera Nurja Berkah</b> memberitahukan "
        "bahwa daftar item di bawah ini telah dikategorikan sebagai <b>Barang Diskontinu</b> (tidak dijual/dipasok lagi). "
        "Oleh karena itu, kami mengajukan penarikan/retur barang atau pembersihan data persediaan (delist) untuk daftar produk berikut:"
    )
    story.append(Paragraph(salam_text, body_style))
    story.append(Spacer(1, 8))

    data_tabel = [[
        Paragraph("<b>No</b>", cell_center),
        Paragraph("<b>Kode / Barcode</b>", cell_center),
        Paragraph("<b>Nama Barang</b>", cell_style),
        Paragraph("<b>Kategori</b>", cell_center),
        Paragraph("<b>Supplier</b>", cell_style),
        Paragraph("<b>Alasan Diskontinu</b>", cell_style),
        Paragraph("<b>Tgl Diskontinu</b>", cell_center),
    ]]

    no = 1
    for _, r in df_data.iterrows():
        data_tabel.append([
            Paragraph(str(no), cell_center),
            Paragraph(str(r["kode"]), cell_center),
            Paragraph(str(r["nama"]), cell_style),
            Paragraph(str(r["kategori"]), cell_center),
            Paragraph(str(r["supplier"]), cell_style),
            Paragraph(str(r["alasan"]), cell_style),
            Paragraph(str(r["tgl_diskontinu"]), cell_center),
        ])
        no += 1

    tabel_b = Table(data_tabel, colWidths=[8 * mm, 28 * mm, 48 * mm, 22 * mm, 38 * mm, 25 * mm, 17 * mm])
    tabel_b.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C53030")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FFF5F5")),
    ]))
    story.append(tabel_b)
    story.append(Spacer(1, 10))

    penutup_text = (
        "Demikian surat pemberitahuan ini kami sampaikan agar dapat ditindaklanjuti sesuai dengan kesepakatan retur "
        "maupun penyelesaian administrasi bersama. Atas perhatian dan kerja samanya, kami ucapkan terima kasih.<br/><br/>"
        "<b>Wassalamu'alaikum Wr. Wb.</b>"
    )
    story.append(Paragraph(penutup_text, body_style))
    story.append(Spacer(1, 15))

    data_ttd = [
        [Paragraph("<b>Hormat Kami,</b><br/>Torasera Nurja Berkah", body_style), Paragraph(f"<b>Menerima & Mengetahui,</b><br/>{supplier_label}", body_style)],
        ["\n\n\n________________________", "\n\n\n________________________"],
        [Paragraph("<b>( Tim Management / Admin )</b>", body_style), Paragraph("<b>( Sales / Distributor )</b>", body_style)],
    ]
    tabel_ttd = Table(data_ttd, colWidths=[93 * mm, 93 * mm])
    story.append(tabel_ttd)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_pdf_rekap_ed(df_rekap, bulan_label):
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
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=12, alignment=1, spaceAfter=10, textColor=colors.HexColor("#DD6B20"), fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Text", parent=styles["Normal"], fontSize=9)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)
    cell_center = ParagraphStyle("CellCenter", parent=styles["Normal"], fontSize=8, alignment=1, leading=10)

    story.append(Paragraph("TORASERA NURJA BERKAH", company_style))
    story.append(Paragraph(f"LAPORAN REKAP RETUR ED BULANAN ({bulan_label})", title_style))

    tgl = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"<b>Tanggal Cetak:</b> {tgl}", normal_style))
    story.append(Spacer(1, 8))

    data_tabel = [[
        Paragraph("<b>Kode</b>", cell_center),
        Paragraph("<b>Nama Barang</b>", cell_style),
        Paragraph("<b>Supplier</b>", cell_style),
        Paragraph("<b>Frekuensi Retur ED</b>", cell_center),
        Paragraph("<b>Total Qty ED</b>", cell_center),
        Paragraph("<b>Rekomendasi Evaluasi</b>", cell_center),
    ]]

    for _, r in df_rekap.iterrows():
        rekom = "Rekomendasi Diskontinu" if r["rekomendasi_dis"] else "Normal / Pantau"
        data_tabel.append([
            Paragraph(str(r["kode"]), cell_center),
            Paragraph(str(r["nama"]), cell_style),
            Paragraph(str(r["supplier"]), cell_style),
            Paragraph(f"{r['frekuensi_ed']}x", cell_center),
            Paragraph(str(r["total_qty_ed"]), cell_center),
            Paragraph(rekom, cell_center),
        ])

    tabel_b = Table(data_tabel, colWidths=[28 * mm, 60 * mm, 45 * mm, 22 * mm, 15 * mm, 20 * mm])
    tabel_b.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DD6B20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(tabel_b)
    story.append(Spacer(1, 20))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_pdf_pesanan(df_data):
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
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=12, alignment=1, spaceAfter=10, textColor=colors.HexColor("#2D3748"), fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("Text", parent=styles["Normal"], fontSize=9)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)
    cell_center = ParagraphStyle("CellCenter", parent=styles["Normal"], fontSize=8, alignment=1, leading=10)
    cell_right = ParagraphStyle("CellRight", parent=styles["Normal"], fontSize=8, alignment=2, leading=10)

    story.append(Paragraph("TORASERA NURJA BERKAH", company_style))
    story.append(Paragraph("NOTA PESANAN CUSTOMER / PRE-ORDER", title_style))

    tgl = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    info_data = [[Paragraph(f"<b>Tgl Cetak:</b> {tgl}", normal_style)]]
    story.append(Table(info_data, colWidths=[190 * mm]))
    story.append(Spacer(1, 8))

    data_tabel = [[
        Paragraph("<b>No</b>", cell_center),
        Paragraph("<b>Customer</b>", cell_style),
        Paragraph("<b>No HP</b>", cell_center),
        Paragraph("<b>Barang</b>", cell_style),
        Paragraph("<b>Qty</b>", cell_center),
        Paragraph("<b>Total (Rp)</b>", cell_right),
        Paragraph("<b>Status</b>", cell_center),
    ]]

    no = 1
    grand_total = 0
    for _, r in df_data.iterrows():
        data_tabel.append([
            Paragraph(str(no), cell_center),
            Paragraph(str(r["nama_customer"]), cell_style),
            Paragraph(str(r["no_hp"]), cell_center),
            Paragraph(str(r["nama_barang"]), cell_style),
            Paragraph(str(r["qty"]), cell_center),
            Paragraph(f"{r['total']:,.0f}", cell_right),
            Paragraph(str(r["status"]), cell_center),
        ])
        grand_total += r["total"]
        no += 1

    data_tabel.append([
        "", "", "",
        Paragraph("<b>TOTAL</b>", cell_center),
        "",
        Paragraph(f"<b>{grand_total:,.0f}</b>", cell_right),
        "",
    ])

    tabel_b = Table(data_tabel, colWidths=[10 * mm, 35 * mm, 25 * mm, 55 * mm, 15 * mm, 28 * mm, 22 * mm])
    tabel_b.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#319795")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#CBD5E0")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E6FFFA")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#319795")),
    ]))
    story.append(tabel_b)
    story.append(Spacer(1, 20))

    doc.build(story)
    buffer.seek(0)
    return buffer


# --- DIALOG POPUP KONFIRMASI PERSETUJUAN ---
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
                    supabase.table("barang_retur").update({"status": status_baru, "qty": 0, "total": 0}).eq("id", item_id).execute()
                else:
                    supabase.table("barang_retur").update({"status": status_baru}).eq("id", item_id).execute()

            st.session_state.select_all = False
            st.success(f"Berhasil memperbarui status barang menjadi '{status_baru}'!")
            st.rerun()

    with col2:
        if st.button("❌ Batal", use_container_width=True):
            st.rerun()


# --- NAVIGASI SIDEBAR ---
st.sidebar.title("📌 Menu Utama")
menu = st.sidebar.radio(
    "Pilih Halaman:",
    [
        "📈 Analisis PO & Produk Terlaris",
        "📦 Retur Barang",
        "📊 Rekap Retur Bulanan & ED",
        "🚫 Barang Diskontinu",
        "🛒 Pesanan Customer"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Torasera Nurja Berkah © 2026")


# ==========================================
# HALAMAN 1: ANALISIS PO & PRODUK TERLARIS
# ==========================================
if menu == "📈 Analisis PO & Produk Terlaris":
    st.title("📈 Analisis Pembelian PO & Produk Terlaris")
    st.markdown("Paste tabel nota PO pembelian supplier Anda di bawah ini untuk analisis otomatis bulanan & item paling sering dibeli.")

    tab_input, tab_analisis = st.tabs(["📋 Paste & Input PO Baru", "📊 Analisis & Grafik Terlaris"])

    with tab_input:
        st.subheader("📥 Input Nota PO Baru (Copy-Paste)")

        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            po_supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER, key="po_sup")
        with c_p2:
            po_number = st.text_input("No. PO / Nota Pembelian", value=f"PO-{datetime.datetime.now().strftime('%Y%m%d%H%M')}")
        with c_p3:
            po_date = st.date_input("Tanggal Transaksi PO", datetime.date.today())

        raw_paste = st.text_area(
            "📋 Paste Tabel Nota PO di sini (Blok tabel dari PDF/Excel lalu CTRL+V):",
            height=200,
            placeholder="Contoh format:\n1   sudah   8991038766100   8991038766100   -   CINDERELIA CT BUDS 100s   3.544   2030-12-11   3.258   0   24   24   78.192..."
        )

        if raw_paste:
            df_parsed = parse_pasted_po_data(raw_paste)
            if not df_parsed.empty:
                st.subheader("🔍 Preview Data Hasil Ekstraksi Otomatis:")
                st.dataframe(df_parsed, use_container_width=True)

                if st.button("💾 Simpan Transaksi PO Ini Ke Database", type="primary"):
                    records = []
                    for _, r in df_parsed.iterrows():
                        records.append({
                            "no_po": po_number,
                            "supplier": po_supplier,
                            "kode_barang": str(r["Kode"]),
                            "nama_barang": str(r["Nama Barang"]),
                            "qty": int(r["Qty"]),
                            "hpp": float(r["HPP"]),
                            "harga_order": float(r["Harga Order"]),
                            "subtotal": float(r["Subtotal"]),
                            "tgl_po": str(po_date)
                        })
                    supabase.table("pembelian_po").insert(records).execute()
                    st.success("Data PO berhasil disimpan & masuk ke grafik analisis bulanan!")
                    st.rerun()
            else:
                st.error("Gagal membaca struktur tabel. Pastikan baris data memiliki kolom Kode, Nama Barang, Qty, dan Subtotal!")

    with tab_analisis:
        st.subheader("📊 Analisis Produk Sering Dibeli / Fast Moving")

        response = supabase.table("pembelian_po").select("*").execute()
        df_po_all = pd.DataFrame(response.data)

        if not df_po_all.empty:
            df_po_all["tgl_po"] = pd.to_datetime(df_po_all["tgl_po"], errors="coerce")
            df_po_all["bulan_tahun"] = df_po_all["tgl_po"].dt.strftime("%Y-%m")

            f_col1, f_col2 = st.columns(2)
            with f_col1:
                pilihan_bulan = st.selectbox(
                    "Pilih Periode Bulan:",
                    ["SEMUA PERIODE"] + sorted(df_po_all["bulan_tahun"].dropna().unique().tolist(), reverse=True),
                    key="filter_po_bulan"
                )
            with f_col2:
                pilihan_sup = st.selectbox(
                    "Filter Supplier:",
                    ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER,
                    key="filter_po_sup"
                )

            df_filtered = df_po_all.copy()
            if pilihan_bulan != "SEMUA PERIODE":
                df_filtered = df_filtered[df_filtered["bulan_tahun"] == pilihan_bulan]
            if pilihan_sup != "SEMUA SUPPLIER":
                df_filtered = df_filtered[df_filtered["supplier"] == pilihan_sup]

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Item PO Dibelanjakan", int(df_filtered["qty"].sum()))
            m2.metric("Total Nominal PO", f"Rp {df_filtered['subtotal'].sum():,.0f}")
            m3.metric("Frekuensi PO Ditransaksikan", df_filtered["no_po"].nunique())

            st.divider()

            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("### 🔥 Top 10 Produk Paling Sering / Banyak Dibeli (Qty)")
                top_qty = df_filtered.groupby("nama_barang")["qty"].sum().reset_index().sort_values(by="qty", ascending=False).head(10)
                st.bar_chart(top_qty.set_index("nama_barang"))

            with col_g2:
                st.markdown("### 💰 Top 10 Produk Nominal PO Terbesar (Rp)")
                top_subtotal = df_filtered.groupby("nama_barang")["subtotal"].sum().reset_index().sort_values(by="subtotal", ascending=False).head(10)
                st.bar_chart(top_subtotal.set_index("nama_barang"))

            st.divider()
            st.markdown("### 📅 Trend Pembelian PO per Bulan")
            df_trend = df_po_all.groupby("bulan_tahun")["subtotal"].sum().reset_index()
            st.line_chart(df_trend.set_index("bulan_tahun"))

            st.divider()
            st.markdown("### 📜 Detail Riwayat Pembelian PO")
            st.dataframe(
                df_filtered,
                column_config={
                    "hpp": st.column_config.NumberColumn("HPP", format="Rp %'d"),
                    "harga_order": st.column_config.NumberColumn("Harga Order", format="Rp %'d"),
                    "subtotal": st.column_config.NumberColumn("Subtotal", format="Rp %'d"),
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Belum ada data PO yang disimpan. Silakan paste nota PO Anda di tab 'Paste & Input PO Baru'.")


# ==========================================
# HALAMAN 2: RETUR BARANG
# ==========================================
elif menu == "📦 Retur Barang":
    st.title("📦 Manajemen Retur Barang")

    df_semua = ambil_data_retur()

    if not df_semua.empty:
        st.subheader("📊 Analisis & Grafik Retur Overall")
        g_col1, g_col2 = st.columns(2)

        with g_col1:
            st.markdown("### 🔝 Top Supplier Nominal Retur Terbesar")
            top_sup_retur = df_semua.groupby("supplier")["total"].sum().reset_index().sort_values(by="total", ascending=False).head(7)
            st.bar_chart(top_sup_retur.set_index("supplier"))

        with g_col2:
            st.markdown("### 📈 Status Distribusi Retur")
            status_dist = df_semua.groupby("status")["id"].count().reset_index().rename(columns={"id": "jumlah"})
            st.bar_chart(status_dist.set_index("status"))

    st.divider()

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        f_sup = st.selectbox("Filter Supplier Retur:", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER)
    with col_f2:
        f_stat = st.selectbox("Filter Status Retur:", ["SEMUA STATUS"] + DAFTAR_STATUS)
    with col_f3:
        f_cari = st.text_input("Cari Kode / Nama / Ket Retur:")

    df_retur = ambil_data_retur(f_sup, f_stat, f_cari)

    st.subheader("📋 Daftar Barang Retur")
    st.dataframe(df_retur, use_container_width=True, hide_index=True)
