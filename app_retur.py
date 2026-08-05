import datetime
import io
import re
import sqlite3
from io import BytesIO
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# --- CONFIG PAGE ---
st.set_page_config(
    page_title="Sistem Manajemen Barang - Torasera Nurja Berkah",
    page_icon="📦",
    layout="wide",
)

DB_NAME = "retur_barang.db"

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


def init_db():
    """Membuat tabel jika belum ada, atau memperbarui kolom tanpa menghapus data SQLite lama."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Tabel Barang Retur
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barang_retur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode TEXT,
            nama TEXT,
            qty INTEGER,
            hpp REAL,
            total REAL,
            ket TEXT,
            ed TEXT,
            supplier TEXT,
            status TEXT DEFAULT 'Pengajuan',
            tgl_input TEXT
        )
    """)

    # 2. Tabel Barang Diskontinu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barang_diskontinu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode TEXT,
            nama TEXT,
            kategori TEXT,
            supplier TEXT,
            alasan TEXT,
            tgl_diskontinu TEXT
        )
    """)

    # 3. Tabel Pesanan Customer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pesanan_customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_customer TEXT,
            no_hp TEXT,
            kode_barang TEXT,
            nama_barang TEXT,
            qty INTEGER,
            harga REAL,
            total REAL,
            tgl_pesan TEXT,
            status TEXT DEFAULT 'Pending',
            catatan TEXT
        )
    """)

    # 4. Tabel Transaksi Pembelian PO (Fitur Baru)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pembelian_po (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no_po TEXT,
            supplier TEXT,
            kode_barang TEXT,
            nama_barang TEXT,
            qty INTEGER,
            hpp REAL,
            harga_order REAL,
            subtotal REAL,
            tgl_po TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


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


def ambil_data_retur(filter_supplier="SEMUA SUPPLIER", filter_status="SEMUA STATUS", cari=""):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, kode, nama, qty, hpp, total, ket, ed, supplier, status, tgl_input FROM barang_retur WHERE 1=1"
    params = []
    if filter_supplier and filter_supplier != "SEMUA SUPPLIER":
        query += " AND supplier = ?"
        params.append(filter_supplier)
    if filter_status and filter_status != "SEMUA STATUS":
        query += " AND status = ?"
        params.append(filter_status)
    if cari:
        query += " AND (kode LIKE ? OR nama LIKE ? OR ket LIKE ? OR supplier LIKE ? OR status LIKE ?)"
        kw = f"%{cari}%"
        params.extend([kw, kw, kw, kw, kw])
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def ambil_data_diskontinu(filter_supplier="SEMUA SUPPLIER", cari=""):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, kode, nama, kategori, supplier, alasan, tgl_diskontinu FROM barang_diskontinu WHERE 1=1"
    params = []
    if filter_supplier and filter_supplier != "SEMUA SUPPLIER":
        query += " AND supplier = ?"
        params.append(filter_supplier)
    if cari:
        query += " AND (kode LIKE ? OR nama LIKE ? OR kategori LIKE ? OR supplier LIKE ? OR alasan LIKE ?)"
        kw = f"%{cari}%"
        params.extend([kw, kw, kw, kw, kw])
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def ambil_data_pesanan(filter_status="SEMUA STATUS", cari=""):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, nama_customer, no_hp, kode_barang, nama_barang, qty, harga, total, tgl_pesan, status, catatan FROM pesanan_customer WHERE 1=1"
    params = []
    if filter_status and filter_status != "SEMUA STATUS":
        query += " AND status = ?"
        params.append(filter_status)
    if cari:
        query += " AND (nama_customer LIKE ? OR no_hp LIKE ? OR kode_barang LIKE ? OR nama_barang LIKE ? OR status LIKE ?)"
        kw = f"%{cari}%"
        params.extend([kw, kw, kw, kw, kw])
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


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
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            if status_baru == "Sukses":
                cursor.execute(
                    f"UPDATE barang_retur SET status=?, qty=0, total=0 WHERE id IN ({','.join(['?']*len(id_list))})",
                    [status_baru] + id_list,
                )
            else:
                cursor.execute(
                    f"UPDATE barang_retur SET status=? WHERE id IN ({','.join(['?']*len(id_list))})",
                    [status_baru] + id_list,
                )

            conn.commit()
            conn.close()
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
# HALAMAN BARU: ANALISIS PO & PRODUK TERLARIS
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
            placeholder="Contoh format:\n1  sudah  8991038766100  8991038766100  -  CINDERELIA CT BUDS 100s  3.544  2030-12-11  3.258  0  24  24  78.192..."
        )

        if raw_paste:
            df_parsed = parse_pasted_po_data(raw_paste)
            if not df_parsed.empty:
                st.subheader("🔍 Preview Data Hasil Ekstraksi Otomatis:")
                st.dataframe(df_parsed, use_container_width=True)

                if st.button("💾 Simpan Transaksi PO Ini Ke Database", type="primary"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    for _, r in df_parsed.iterrows():
                        cursor.execute("""
                            INSERT INTO pembelian_po (no_po, supplier, kode_barang, nama_barang, qty, hpp, harga_order, subtotal, tgl_po)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (po_number, po_supplier, r["Kode"], r["Nama Barang"], r["Qty"], r["HPP"], r["Harga Order"], r["Subtotal"], str(po_date)))
                    conn.commit()
                    conn.close()
                    st.success("Data PO berhasil disimpan & masuk ke grafik analisis bulanan!")
                    st.rerun()
            else:
                st.error("Gagal membaca struktur tabel. Pastikan baris data memiliki kolom Kode, Nama Barang, Qty, dan Subtotal!")

    with tab_analisis:
        st.subheader("📊 Analisis Produk Sering Dibeli / Fast Moving")

        conn = sqlite3.connect(DB_NAME)
        df_po_all = pd.read_sql_query("SELECT * FROM pembelian_po", conn)
        conn.close()

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

            # Filtering
            df_filtered = df_po_all.copy()
            if pilihan_bulan != "SEMUA PERIODE":
                df_filtered = df_filtered[df_filtered["bulan_tahun"] == pilihan_bulan]
            if pilihan_sup != "SEMUA SUPPLIER":
                df_filtered = df_filtered[df_filtered["supplier"] == pilihan_sup]

            # Metric Cards
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
# HALAMAN 1: RETUR BARANG
# ==========================================
elif menu == "📦 Retur Barang":
    st.title("📦 Retur Barang - Torasera Nurja Berkah")

    df_semua = ambil_data_retur()

    if not df_semua.empty:
        st.subheader("📊 Analisis & Grafik Retur Overall")
        g_col1, g_col2 = st.columns(2)

        with g_col1:
            st.markdown("### 🔝 Top Supplier Nominal Retur Terbesar")
            top_sup_retur = df_semua.groupby("supplier")["total"].sum().reset_index().sort_values(by="total", ascending=False).head(7)
            st.bar_chart(top_sup_retur.set_index("supplier"))

        with g_col2:
            st.markdown("### 📌 Distribusi Status Retur Barang")
            status_counts = df_semua["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Jumlah Item"]
            st.bar_chart(status_counts.set_index("Status"))

        st.divider()

    tab_input_retur, tab_data_retur = st.tabs(["📥 Input Retur Baru", "📋 Data & Kelola Retur"])

    with tab_input_retur:
        st.subheader("📝 Form Input Barang Retur")
        with st.form("form_retur", clear_on_submit=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                r_kode = st.text_input("Kode / Barcode Barang")
                r_nama = st.text_input("Nama Barang")
                r_qty = st.number_input("Qty Retur", min_value=1, value=1, step=1)
                r_hpp = st.number_input("HPP / Harga Beli Satuan (Rp)", min_value=0.0, value=0.0, step=100.0)

            with col_r2:
                r_ket = st.text_input("Keterangan Retur", placeholder="Contoh: ED Dekat, Rusak, Segel Terbuka")
                r_ed = st.text_input("Expired Date (ED)", placeholder="YYYY-MM-DD / MM-YY")
                r_supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER, key="retur_sup_input")
                r_status = st.selectbox("Status Retur", DAFTAR_STATUS, index=0)

            btn_simpan_retur = st.form_submit_button("💾 Simpan Barang Retur", type="primary")

            if btn_simpan_retur:
                if not r_nama:
                    st.error("Nama barang wajib diisi!")
                else:
                    r_total = r_qty * r_hpp
                    r_tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO barang_retur (kode, nama, qty, hpp, total, ket, ed, supplier, status, tgl_input)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (r_kode, r_nama, r_qty, r_hpp, r_total, r_ket, r_ed, r_supplier, r_status, r_tgl))
                    conn.commit()
                    conn.close()
                    st.success("Data retur barang berhasil disimpan!")
                    st.rerun()

    with tab_data_retur:
        st.subheader("📋 Daftar & Pembaruan Status Retur")

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_sup = st.selectbox("Filter Supplier:", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER, key="f_sup_retur")
        with fc2:
            f_stat = st.selectbox("Filter Status:", ["SEMUA STATUS"] + DAFTAR_STATUS, key="f_stat_retur")
        with fc3:
            f_cari = st.text_input("🔍 Cari Data Retur:", placeholder="Kode, nama, ket...", key="f_cari_retur")

        df_retur = ambil_data_retur(filter_supplier=f_sup, filter_status=f_stat, cari=f_cari)

        if not df_retur.empty:
            m_r1, m_r2, m_r3 = st.columns(3)
            m_r1.metric("Total Item Retur", len(df_retur))
            m_r2.metric("Total Qty Retur", int(df_retur["qty"].sum()))
            m_r3.metric("Total Nominal Retur", f"Rp {df_retur['total'].sum():,.0f}")

            st.divider()

            if "select_all" not in st.session_state:
                st.session_state.select_all = False

            col_a1, col_a2, _ = st.columns([1, 2, 3])
            with col_a1:
                if st.checkbox("Pilih Semua Baris", value=st.session_state.select_all):
                    st.session_state.select_all = True
                else:
                    st.session_state.select_all = False

            # Render Table / Selection Form
            selected_ids = []
            for idx, row in df_retur.iterrows():
                cols = st.columns([0.5, 2, 4, 1, 2, 2, 2, 2, 2])
                checked = cols[0].checkbox("", value=st.session_state.select_all, key=f"chk_{row['id']}")
                if checked:
                    selected_ids.append(row["id"])

                cols[1].write(row["kode"])
                cols[2].write(row["nama"])
                cols[3].write(row["qty"])
                cols[4].write(f"Rp {row['total']:,.0f}")
                cols[5].write(row["ket"])
                cols[6].write(row["ed"])
                cols[7].write(row["supplier"])
                cols[8].write(row["status"])

            st.divider()

            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                status_update_pilihan = st.selectbox("Ubah Status Terpilih Ke:", DAFTAR_STATUS, key="stat_bulk")
                if st.button("🔄 Perbarui Status Item Terpilih", type="primary"):
                    if not selected_ids:
                        st.warning("Pilih minimal satu barang terlebih dahulu!")
                    else:
                        if status_update_pilihan == "Sukses":
                            dialog_konfirmasi_setujui(selected_ids, status_update_pilihan)
                        else:
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute(
                                f"UPDATE barang_retur SET status=? WHERE id IN ({','.join(['?']*len(selected_ids))})",
                                [status_update_pilihan] + selected_ids
                            )
                            conn.commit()
                            conn.close()
                            st.success("Status barang berhasil diperbarui!")
                            st.rerun()

            with col_b2:
                if st.button("🗑️ Hapus Item Terpilih"):
                    if not selected_ids:
                        st.warning("Pilih minimal satu barang yang akan dihapus!")
                    else:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute(
                            f"DELETE FROM barang_retur WHERE id IN ({','.join(['?']*len(selected_ids))})",
                            selected_ids
                        )
                        conn.commit()
                        conn.close()
                        st.success("Item terpilih berhasil dihapus!")
                        st.rerun()

            with col_b3:
                st.markdown("### 📄 Cetak Nota Retur PDF")
                target_supplier = f_sup if f_sup != "SEMUA SUPPLIER" else "SEMUA SUPPLIER"
                pdf_bytes = generate_pdf(df_retur, target_supplier)
                st.download_button(
                    label="📥 Download PDF Nota Retur",
                    data=pdf_bytes,
                    file_name=f"Nota_Retur_{target_supplier}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("Tidak ada data retur barang yang ditemukan.")


# ==========================================
# HALAMAN 2: REKAP RETUR BULANAN & ED
# ==========================================
elif menu == "📊 Rekap Retur Bulanan & ED":
    st.title("📊 Rekap Retur Bulanan & Analysis ED")
    st.markdown("Halaman ini merangkum data retur barang berdasarkan kriteria ED / Expired Date untuk evaluasi perulangan produk retur.")

    conn = sqlite3.connect(DB_NAME)
    df_all_retur = pd.read_sql_query("SELECT * FROM barang_retur", conn)
    conn.close()

    if not df_all_retur.empty:
        df_all_retur["tgl_input_dt"] = pd.to_datetime(df_all_retur["tgl_input"], errors="coerce")
        df_all_retur["bulan_tahun"] = df_all_retur["tgl_input_dt"].dt.strftime("%Y-%m")

        col_rk1, col_rk2 = st.columns(2)
        with col_rk1:
            pilihan_bulan_rekap = st.selectbox(
                "Pilih Periode Bulan Retur:",
                ["SEMUA PERIODE"] + sorted(df_all_retur["bulan_tahun"].dropna().unique().tolist(), reverse=True)
            )
        with col_rk2:
            threshold_ed = st.number_input("Batas Frekuensi Retur ED untuk Rekomendasi Diskontinu:", min_value=1, value=2, step=1)

        df_filtered_rekap = df_all_retur.copy()
        if pilihan_bulan_rekap != "SEMUA PERIODE":
            df_filtered_rekap = df_filtered_rekap[df_filtered_rekap["bulan_tahun"] == pilihan_bulan_rekap]

        # Filter khusus retur ED
        df_ed = df_filtered_rekap[df_filtered_rekap["ket"].str.contains("ED|expired|kadaluarsa|exp", case=False, na=False)]

        st.divider()

        if not df_ed.empty:
            rekap_ed = df_ed.groupby(["kode", "nama", "supplier"]).agg(
                frekuensi_ed=("id", "count"),
                total_qty_ed=("qty", "sum"),
                total_nominal_ed=("total", "sum")
            ).reset_index()

            rekap_ed["rekomendasi_dis"] = rekap_ed["frekuensi_ed"] >= threshold_ed

            st.subheader("⚠️ Produk Berulang Retur ED & Rekomendasi Diskontinu")
            st.dataframe(
                rekap_ed,
                column_config={
                    "rekomendasi_dis": st.column_config.CheckboxColumn("Rekomendasi Diskontinu?"),
                    "total_nominal_ed": st.column_config.NumberColumn("Total Nominal ED", format="Rp %'d")
                },
                use_container_width=True,
                hide_index=True
            )

            # Opsi otomatis masukkan ke diskontinu
            item_dis_rekomendasi = rekap_ed[rekap_ed["rekomendasi_dis"] == True]
            if not item_dis_rekomendasi.empty:
                st.warning(f"Ditemukan {len(item_dis_rekomendasi)} produk yang telah melebihi batas frekuensi retur ED ({threshold_ed}x)!")
                if st.button("🚀 Pindahkan Semua Produk Rekomendasi Ini Ke List Diskontinu", type="primary"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    tgl_now = datetime.datetime.now().strftime("%Y-%m-%d")
                    for _, item in item_dis_rekomendasi.iterrows():
                        cursor.execute("""
                            INSERT INTO barang_diskontinu (kode, nama, kategori, supplier, alasan, tgl_diskontinu)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (item["kode"], item["nama"], "Automated ED", item["supplier"], f"Retur ED Berulang ({item['frekuensi_ed']}x)", tgl_now))
                    conn.commit()
                    conn.close()
                    st.success("Produk berhasil ditambahkan ke daftar Barang Diskontinu!")
                    st.rerun()

            st.divider()
            pdf_bytes_rekap = generate_pdf_rekap_ed(rekap_ed, pilihan_bulan_rekap)
            st.download_button(
                label="📥 Download Laporan Rekap Retur ED (PDF)",
                data=pdf_bytes_rekap,
                file_name=f"Rekap_Retur_ED_{pilihan_bulan_rekap}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Tidak ada data retur dengan keterangan ED/Expired pada periode ini.")
    else:
        st.info("Belum ada data retur barang.")


# ==========================================
# HALAMAN 3: BARANG DISKONTINU
# ==========================================
elif menu == "🚫 Barang Diskontinu":
    st.title("🚫 Kelola Barang Diskontinu")
    st.markdown("Pencatatan item yang sudah tidak dijual/dipasok lagi beserta penerbitan Surat Pemberitahuan Retur / Delist.")

    tab_in_dis, tab_data_dis = st.tabs(["📥 Tambah Item Diskontinu", "📋 Daftar & Surat Delist"])

    with tab_in_dis:
        st.subheader("📝 Tambah Barang Diskontinu Baru")
        with st.form("form_diskontinu", clear_on_submit=True):
            cd1, cd2 = st.columns(2)
            with cd1:
                d_kode = st.text_input("Kode / Barcode Barang")
                d_nama = st.text_input("Nama Barang")
                d_kategori = st.text_input("Kategori Produk", placeholder="Contoh: Snack, Sembako, Kosmetik")
            with cd2:
                d_supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER, key="dis_sup_input")
                d_alasan = st.text_input("Alasan Diskontinu", placeholder="Contoh: Penjualan Lambat, Pabrik Stop Produksi, ED Berulang")
                d_tgl = st.date_input("Tanggal Diskontinu", datetime.date.today())

            btn_simpan_dis = st.form_submit_button("💾 Simpan Barang Diskontinu", type="primary")

            if btn_simpan_dis:
                if not d_nama:
                    st.error("Nama barang wajib diisi!")
                else:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO barang_diskontinu (kode, nama, kategori, supplier, alasan, tgl_diskontinu)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (d_kode, d_nama, d_kategori, d_supplier, d_alasan, str(d_tgl)))
                    conn.commit()
                    conn.close()
                    st.success("Barang diskontinu berhasil ditambahkan!")
                    st.rerun()

    with tab_data_dis:
        st.subheader("📋 Daftar Barang Diskontinu")

        fd1, fd2 = st.columns(2)
        with fd1:
            f_sup_dis = st.selectbox("Filter Supplier:", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER, key="f_sup_dis")
        with fd2:
            f_cari_dis = st.text_input("🔍 Cari Barang Diskontinu:", placeholder="Kode, nama, alasan...", key="f_cari_dis")

        df_dis = ambil_data_diskontinu(filter_supplier=f_sup_dis, cari=f_cari_dis)

        if not df_dis.empty:
            st.dataframe(df_dis, use_container_width=True, hide_index=True)

            st.divider()
            col_dis_pdf1, col_dis_pdf2 = st.columns(2)

            with col_dis_pdf1:
                st.markdown("### 📄 Cetak Surat Delist / Retur Diskontinu")
                target_supplier_dis = f_sup_dis if f_sup_dis != "SEMUA SUPPLIER" else "SEMUA SUPPLIER"
                pdf_dis_bytes = generate_pdf_diskontinu(df_dis, target_supplier_dis)
                st.download_button(
                    label="📥 Download Surat Pemberitahuan Delist PDF",
                    data=pdf_dis_bytes,
                    file_name=f"Surat_Delist_{target_supplier_dis}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )

            with col_dis_pdf2:
                st.markdown("### 🗑️ Hapus Data Diskontinu")
                del_id = st.number_input("Masukkan ID Item yang Akan Dihapus:", min_value=1, step=1)
                if st.button("Hapus Item Diskontinu"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM barang_diskontinu WHERE id=?", (del_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Item dengan ID {del_id} berhasil dihapus!")
                    st.rerun()
        else:
            st.info("Tidak ada data barang diskontinu.")


# ==========================================
# HALAMAN 4: PESANAN CUSTOMER
# ==========================================
elif menu == "🛒 Pesanan Customer":
    st.title("🛒 Management Pesanan Customer / Pre-Order")
    st.markdown("Pencatatan pesanan khusus/indent customer dan pemantauan status pemrosesannya.")

    tab_in_psn, tab_data_psn = st.tabs(["📥 Input Pesanan Baru", "📋 Daftar & Status Pesanan"])

    with tab_in_psn:
        st.subheader("📝 Form Input Pesanan Customer")
        with st.form("form_pesanan", clear_on_submit=True):
            cp1, cp2 = st.columns(2)
            with cp1:
                p_nama_cust = st.text_input("Nama Customer / Pelanggan")
                p_hp = st.text_input("No. HP / WhatsApp")
                p_kode_brg = st.text_input("Kode Barang (Opsional)")
                p_nama_brg = st.text_input("Nama Barang Pesanan")
            with cp2:
                p_qty = st.number_input("Qty Pesanan", min_value=1, value=1, step=1)
                p_harga = st.number_input("Harga Satuan (Rp)", min_value=0.0, value=0.0, step=500.0)
                p_catatan = st.text_area("Catatan Khusus", placeholder="Contoh: Titip saat promo, Merk khusus, DP Rp 50.000")
                p_status = st.selectbox("Status Pesanan", DAFTAR_STATUS_PESANAN, index=0)

            btn_simpan_psn = st.form_submit_button("💾 Simpan Pesanan Customer", type="primary")

            if btn_simpan_psn:
                if not p_nama_cust or not p_nama_brg:
                    st.error("Nama customer dan nama barang wajib diisi!")
                else:
                    p_total = p_qty * p_harga
                    p_tgl = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO pesanan_customer (nama_customer, no_hp, kode_barang, nama_barang, qty, harga, total, tgl_pesan, status, catatan)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_nama_cust, p_hp, p_kode_brg, p_nama_brg, p_qty, p_harga, p_total, p_tgl, p_status, p_catatan))
                    conn.commit()
                    conn.close()
                    st.success("Pesanan customer berhasil disimpan!")
                    st.rerun()

    with tab_data_psn:
        st.subheader("📋 Daftar Pesanan Customer")

        fp1, fp2 = st.columns(2)
        with fp1:
            f_stat_psn = st.selectbox("Filter Status Pesanan:", ["SEMUA STATUS"] + DAFTAR_STATUS_PESANAN, key="f_stat_psn")
        with fp2:
            f_cari_psn = st.text_input("🔍 Cari Pesanan:", placeholder="Nama customer, HP, barang...", key="f_cari_psn")

        df_psn = ambil_data_pesanan(filter_status=f_stat_psn, cari=f_cari_psn)

        if not df_psn.empty:
            st.dataframe(
                df_psn,
                column_config={
                    "harga": st.column_config.NumberColumn("Harga Satuan", format="Rp %'d"),
                    "total": st.column_config.NumberColumn("Total", format="Rp %'d"),
                },
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            col_psn_up1, col_psn_up2, col_psn_up3 = st.columns(3)

            with col_psn_up1:
                st.markdown("### 🔄 Ubah Status Pesanan")
                target_psn_id = st.number_input("ID Pesanan:", min_value=1, step=1, key="id_psn_up")
                new_psn_stat = st.selectbox("Status Baru:", DAFTAR_STATUS_PESANAN, key="stat_psn_up")
                if st.button("Update Status Pesanan"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE pesanan_customer SET status=? WHERE id=?", (new_psn_stat, target_psn_id))
                    conn.commit()
                    conn.close()
                    st.success("Status pesanan berhasil diperbarui!")
                    st.rerun()

            with col_psn_up2:
                st.markdown("### 🗑️ Hapus Pesanan")
                del_psn_id = st.number_input("ID Pesanan yang Dihapus:", min_value=1, step=1, key="id_psn_del")
                if st.button("Hapus Pesanan"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM pesanan_customer WHERE id=?", (del_psn_id,))
                    conn.commit()
                    conn.close()
                    st.success("Data pesanan berhasil dihapus!")
                    st.rerun()

            with col_psn_up3:
                st.markdown("### 📄 Cetak Nota Pesanan PDF")
                pdf_psn_bytes = generate_pdf_pesanan(df_psn)
                st.download_button(
                    label="📥 Download Nota Pesanan Customer PDF",
                    data=pdf_psn_bytes,
                    file_name=f"Nota_Pesanan_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("Tidak ada data pesanan customer.")
