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
    "Belum Tau"
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
            # Lewati baris header jika ikut tersalin
            if any(h in cols[0].lower() or h in cols[1].lower() for h in ["no", "kode", "status", "barang"]):
                continue

            # Mengekstrak angka & pembersihan string
            def clean_num(val):
                v = re.sub(r"[^\d.]", "", str(val).replace(",", "."))
                try:
                    return float(v) if "." in v else int(v) if v else 0
                except:
                    return 0

            # Fleksibilitas parsing kolom berdasarkan layout standar nota PO
            kode = cols[2] if len(cols) > 2 else cols[0]
            nama = cols[5] if len(cols) > 5 else cols[1]
            
            # Pengambilan variabel numerik
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
            st.markdown("**Total Nominal Retur per Supplier**")
            df_chart_sup = df_semua.groupby("supplier")["total"].sum().reset_index()
            st.bar_chart(df_chart_sup.set_index("supplier"))

        with g_col2:
            st.markdown("**Status Pengajuan Retur**")
            df_chart_st = df_semua.groupby("status")["id"].count().reset_index()
            df_chart_st.columns = ["Status", "Jumlah Item"]
            st.bar_chart(df_chart_st.set_index("Status"))

    st.divider()

    with st.form("form_barang", clear_on_submit=True):
        st.subheader("➕ Tambah Barang Retur Baru")
        c1, c2 = st.columns(2)
        with c1:
            supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER)
            kode = st.text_input("Kode / Barcode")
            nama = st.text_input("Nama Barang")
        with c2:
            qty = st.number_input("Qty", min_value=1, step=1)
            hpp = st.number_input("HPP (Rp)", min_value=0.0, step=500.0)
            c2_1, c2_2, c2_3 = st.columns(3)
            with c2_1:
                ket = st.text_input("Keterangan (misal: ED / Rusak)", value="ED")
            with c2_2:
                ed = st.text_input("Tgl ED", value="-")
            with c2_3:
                status_input = st.selectbox("Status", DAFTAR_STATUS, index=0)

        submit = st.form_submit_button("Simpan Barang")

        if submit:
            if kode and nama and hpp > 0:
                final_qty = 0 if status_input == "Sukses" else qty
                final_total = 0.0 if status_input == "Sukses" else (qty * hpp)
                tgl_sekarang = datetime.datetime.now().strftime("%Y-%m-%d")

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO barang_retur (kode, nama, qty, hpp, total, ket, ed, supplier, status, tgl_input)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (kode, nama, final_qty, hpp, final_total, ket, ed, supplier, status_input, tgl_sekarang),
                )
                conn.commit()
                conn.close()
                st.success(f"Barang {nama} berhasil disimpan dengan status: {status_input}!")
                st.rerun()
            else:
                st.error("Harap isi Kode, Nama, dan HPP dengan benar!")

    st.divider()

    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        filter_sup = st.selectbox("Filter Supplier", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER, key="filter_retur_sup")
    with f_col2:
        filter_st = st.selectbox("Filter Status", ["SEMUA STATUS"] + DAFTAR_STATUS, key="filter_retur_st")
    with f_col3:
        cari_txt = st.text_input("🔍 Cari Barang (Kode / Nama / Ket / Supplier / Status)", key="cari_retur")

    df_tampil = ambil_data_retur(filter_sup, filter_st, cari_txt)

    st.subheader("📋 Daftar Barang Retur")

    if not df_tampil.empty:
        if "select_all" not in st.session_state:
            st.session_state.select_all = False

        df_tampil.insert(0, "Pilih", st.session_state.select_all)

        b_col1, b_col2, _ = st.columns([1, 1, 4])
        with b_col1:
            if st.button("☑️ Pilih Semua", key="btn_pilih_semua"):
                st.session_state.select_all = True
                st.rerun()
        with b_col2:
            if st.button("☐ Batal Semua", key="btn_batal_semua"):
                st.session_state.select_all = False
                st.rerun()

        edited_df = st.data_editor(
            df_tampil,
            width="stretch",
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                "id": "ID",
                "kode": "Kode",
                "nama": "Nama Barang",
                "qty": "Qty",
                "hpp": st.column_config.NumberColumn("HPP", format="Rp %'d"),
                "total": st.column_config.NumberColumn("Total", format="Rp %'d"),
                "ket": "Keterangan",
                "ed": "ED",
                "supplier": "Supplier",
                "status": "Status Pengajuan",
                "tgl_input": "Tgl Input",
            },
            disabled=["id", "kode", "nama", "qty", "hpp", "total", "ket", "ed", "supplier", "status", "tgl_input"],
            hide_index=True,
            key="editor_retur",
        )

        total_semua = df_tampil["total"].sum()
        st.markdown(f"### **Grand Total: Rp {total_semua:,.0f}**")

        st.divider()

        st.subheader("⚡ Ubah Status Pengajuan (Pilih Massal / Satu-satu)")
        
        terpilih_df = edited_df[edited_df["Pilih"] == True]
        st.write(f"Jumlah barang dicentang: **{len(terpilih_df)} barang**")

        act_col1, _ = st.columns([2, 2])

        with act_col1:
            status_massal = st.selectbox("Pilih Status Baru:", DAFTAR_STATUS, key="sb_status_massal")
            if st.button("⚡ Ubah Status Barang Terpilih", type="primary", key="btn_update_massal"):
                if not terpilih_df.empty:
                    id_list = terpilih_df["id"].tolist()
                    
                    if status_massal == "Sukses":
                        dialog_konfirmasi_setujui(id_list, status_massal)
                    else:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute(
                            f"UPDATE barang_retur SET status=? WHERE id IN ({','.join(['?']*len(id_list))})",
                            [status_massal] + id_list,
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Berhasil memperbarui status {len(id_list)} barang menjadi '{status_massal}'!")
                        st.session_state.select_all = False
                        st.rerun()
                else:
                    st.warning("Pilih / centang minimal 1 barang pada tabel di atas!")

        st.divider()
        col_edit, col_hapus = st.columns(2)

        with col_edit:
            with st.expander("✏️ Update Detail Item Manual"):
                id_edit = st.selectbox("Pilih ID Barang", df_tampil["id"].tolist(), key="sb_edit_retur")
                data_edit = df_tampil[df_tampil["id"] == id_edit].iloc[0]

                with st.form("form_edit_item"):
                    edit_sup_idx = DAFTAR_SUPPLIER.index(data_edit["supplier"]) if data_edit["supplier"] in DAFTAR_SUPPLIER else 0
                    e_supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER, index=edit_sup_idx)
                    e_kode = st.text_input("Kode / Barcode", value=data_edit["kode"])
                    e_nama = st.text_input("Nama Barang", value=data_edit["nama"])
                    e_qty = st.number_input("Qty", min_value=0, value=int(data_edit["qty"]), step=1)
                    e_hpp = st.number_input("HPP (Rp)", min_value=0.0, value=float(data_edit["hpp"]), step=500.0)
                    e_ket = st.text_input("Keterangan", value=data_edit["ket"])
                    e_ed = st.text_input("Tgl ED", value=data_edit["ed"])
                    
                    e_st_idx = DAFTAR_STATUS.index(data_edit["status"]) if data_edit["status"] in DAFTAR_STATUS else 0
                    e_status = st.selectbox("Status Pengajuan", DAFTAR_STATUS, index=e_st_idx)

                    btn_update = st.form_submit_button("Update Data Barang")

                    if btn_update:
                        final_qty = 0 if e_status == "Sukses" else e_qty
                        final_total = 0.0 if e_status == "Sukses" else (e_qty * e_hpp)

                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            UPDATE barang_retur 
                            SET kode=?, nama=?, qty=?, hpp=?, total=?, ket=?, ed=?, supplier=?, status=?
                            WHERE id=?
                        """,
                            (e_kode, e_nama, final_qty, e_hpp, final_total, e_ket, e_ed, e_supplier, e_status, id_edit),
                        )
                        conn.commit()
                        conn.close()
                        st.success("Data barang berhasil di-update!")
                        st.rerun()

        with col_hapus:
            with st.expander("🗑️ Hapus Data Barang"):
                id_hapus = st.selectbox("Pilih ID Barang untuk Dihapus", df_tampil["id"].tolist(), key="sb_hapus_retur")
                if st.button("🗑️ Hapus Permanen", type="primary"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM barang_retur WHERE id=?", (id_hapus,))
                    conn.commit()
                    conn.close()
                    st.success("Data retur berhasil dihapus!")
                    st.rerun()

        st.divider()
        st.subheader("🖨️ Cetak Nota Retur (PDF)")
        p_col1, p_col2 = st.columns([2, 1])
        with p_col1:
            print_sup = st.selectbox("Pilih Supplier untuk Cetak Nota:", DAFTAR_SUPPLIER, key="sb_print_retur")
        with p_col2:
            df_print = df_tampil[df_tampil["supplier"] == print_sup]
            if not df_print.empty:
                pdf_bytes = generate_pdf(df_print, print_sup)
                st.download_button(
                    label="📄 Download PDF Nota Retur",
                    data=pdf_bytes,
                    file_name=f"Nota_Retur_{print_sup}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.info("Tidak ada data retur untuk supplier ini.")
    else:
        st.info("Belum ada data barang retur yang cocok dengan filter.")


# ==========================================
# HALAMAN 2: REKAP RETUR BULANAN & ED
# ==========================================
elif menu == "📊 Rekap Retur Bulanan & ED":
    st.title("📊 Rekap Retur Bulanan & ED")
    
    conn = sqlite3.connect(DB_NAME)
    df_all = pd.read_sql_query("SELECT * FROM barang_retur", conn)
    conn.close()

    if not df_all.empty:
        df_all["tgl_input"] = pd.to_datetime(df_all["tgl_input"], errors="coerce")
        df_all["bulan_tahun"] = df_all["tgl_input"].dt.strftime("%Y-%m")
        
        daftar_bulan = sorted(df_all["bulan_tahun"].dropna().unique().tolist(), reverse=True)
        
        c1, c2 = st.columns(2)
        with c1:
            pilih_bulan = st.selectbox("Pilih Periode Bulan:", daftar_bulan if daftar_bulan else [datetime.datetime.now().strftime("%Y-%m")])
        with c2:
            ambang_freq = st.number_input("Ambang Frekuensi ED Retur untuk Rekomendasi Diskontinu:", min_value=1, value=2, step=1)

        df_bulan = df_all[df_all["bulan_tahun"] == pilih_bulan]
        df_ed = df_bulan[df_bulan["ket"].str.contains("ED", case=False, na=False)]

        st.subheader(f"📈 Ringkasan Periode {pilih_bulan}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pengajuan Retur", len(df_bulan))
        m2.metric("Total Item Retur ED", len(df_ed))
        m3.metric("Total Nominal Retur ED", f"Rp {df_ed['total'].sum():,.0f}")

        st.divider()
        st.subheader("🔍 Evaluasi Retur ED Berulang")
        
        if not df_ed.empty:
            rekap_ed = df_ed.groupby(["kode", "nama", "supplier"]).agg(
                frekuensi_ed=("id", "count"),
                total_qty_ed=("qty", "sum")
            ).reset_index()

            rekap_ed["rekomendasi_dis"] = rekap_ed["frekuensi_ed"] >= ambang_freq

            st.dataframe(
                rekap_ed,
                column_config={
                    "kode": "Kode",
                    "nama": "Nama Barang",
                    "supplier": "Supplier",
                    "frekuensi_ed": "Frekuensi Retur ED",
                    "total_qty_ed": "Total Qty ED",
                    "rekomendasi_dis": "Rekomendasi Diskontinu?",
                },
                hide_index=True,
                use_container_width=True,
            )

            pdf_rekap = generate_pdf_rekap_ed(rekap_ed, pilih_bulan)
            st.download_button(
                label="📄 Download Laporan Rekap ED (PDF)",
                data=pdf_rekap,
                file_name=f"Rekap_ED_{pilih_bulan}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Tidak ditemukan retur keterangan ED pada periode ini.")
    else:
        st.info("Belum ada data retur tersimpan di database.")


# ==========================================
# HALAMAN 3: BARANG DISKONTINU
# ==========================================
elif menu == "🚫 Barang Diskontinu":
    st.title("🚫 Barang Diskontinu - Torasera Nurja Berkah")

    with st.form("form_diskontinu", clear_on_submit=True):
        st.subheader("➕ Tambah Barang Diskontinu Baru")
        c1, c2 = st.columns(2)
        with c1:
            supplier = st.selectbox("Supplier", DAFTAR_SUPPLIER, key="dis_sup")
            kode = st.text_input("Kode / Barcode", key="dis_kode")
            nama = st.text_input("Nama Barang", key="dis_nama")
        with c2:
            kategori = st.text_input("Kategori", value="General", key="dis_kat")
            alasan = st.text_input("Alasan Diskontinu", value="Penjualan Lambat / ED Berulang", key="dis_alasan")
            tgl_dis = st.date_input("Tanggal Diskontinu", datetime.date.today())

        submit_dis = st.form_submit_button("Simpan Barang Diskontinu")

        if submit_dis:
            if kode and nama:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO barang_diskontinu (kode, nama, kategori, supplier, alasan, tgl_diskontinu)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (kode, nama, kategori, supplier, alasan, str(tgl_dis)),
                )
                conn.commit()
                conn.close()
                st.success(f"Barang {nama} dikategorikan sebagai Diskontinu!")
                st.rerun()
            else:
                st.error("Isi Kode dan Nama Barang!")

    st.divider()

    f1, f2 = st.columns(2)
    with f1:
        f_sup = st.selectbox("Filter Supplier", ["SEMUA SUPPLIER"] + DAFTAR_SUPPLIER, key="f_dis_sup")
    with f2:
        c_txt = st.text_input("🔍 Cari Barang Diskontinu", key="f_dis_txt")

    df_dis = ambil_data_diskontinu(f_sup, c_txt)

    st.subheader("📋 Daftar Barang Diskontinu")
    if not df_dis.empty:
        st.dataframe(df_dis, hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("🖨️ Cetak Surat Pemberitahuan Delist / Retur Diskontinu")
        p_sup = st.selectbox("Pilih Supplier Surat:", DAFTAR_SUPPLIER, key="sb_surat_dis")
        df_surat = df_dis[df_dis["supplier"] == p_sup]

        if not df_surat.empty:
            pdf_dis = generate_pdf_diskontinu(df_surat, p_sup)
            st.download_button(
                label="📄 Download Surat Delist (PDF)",
                data=pdf_dis,
                file_name=f"Surat_Diskontinu_{p_sup}.pdf",
                mime="application/pdf",
            )
        else:
            st.info("Tidak ada data barang diskontinu untuk supplier ini.")
    else:
        st.info("Belum ada data barang diskontinu.")


# ==========================================
# HALAMAN 4: PESANAN CUSTOMER
# ==========================================
elif menu == "🛒 Pesanan Customer":
    st.title("🛒 Pesanan Customer / Pre-Order")

    with st.form("form_pesanan", clear_on_submit=True):
        st.subheader("➕ Input Pesanan Customer Baru")
        c1, c2 = st.columns(2)
        with c1:
            nama_cust = st.text_input("Nama Customer")
            no_hp = st.text_input("No HP / WA")
            kode_brg = st.text_input("Kode Barang (Opsional)")
            nama_brg = st.text_input("Nama Barang Pesanan")
        with c2:
            qty = st.number_input("Qty", min_value=1, value=1)
            harga = st.number_input("Harga Satuan (Rp)", min_value=0.0, step=1000.0)
            status_p = st.selectbox("Status Pesanan", DAFTAR_STATUS_PESANAN, index=0)
            catatan = st.text_input("Catatan Tambahan")

        submit_p = st.form_submit_button("Simpan Pesanan")

        if submit_p:
            if nama_cust and nama_brg and harga > 0:
                total_p = qty * harga
                tgl_p = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO pesanan_customer (nama_customer, no_hp, kode_barang, nama_barang, qty, harga, total, tgl_pesan, status, catatan)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (nama_cust, no_hp, kode_brg, nama_brg, qty, harga, total_p, tgl_p, status_p, catatan),
                )
                conn.commit()
                conn.close()
                st.success(f"Pesanan untuk {nama_cust} berhasil disimpan!")
                st.rerun()
            else:
                st.error("Isi Nama Customer, Nama Barang, dan Harga!")

    st.divider()

    f1, f2 = st.columns(2)
    with f1:
        f_st_p = st.selectbox("Filter Status Pesanan", ["SEMUA STATUS"] + DAFTAR_STATUS_PESANAN)
    with f2:
        c_txt_p = st.text_input("🔍 Cari Pesanan")

    df_pesan = ambil_data_pesanan(f_st_p, c_txt_p)

    st.subheader("📋 Daftar Pesanan Customer")
    if not df_pesan.empty:
        st.dataframe(
            df_pesan,
            column_config={
                "harga": st.column_config.NumberColumn("Harga Satuan", format="Rp %'d"),
                "total": st.column_config.NumberColumn("Total", format="Rp %'d"),
            },
            hide_index=True,
            use_container_width=True,
        )

        st.divider()
        st.subheader("🖨️ Cetak Nota Pesanan (PDF)")
        pdf_p = generate_pdf_pesanan(df_pesan)
        st.download_button(
            label="📄 Download Rekap Pesanan (PDF)",
            data=pdf_p,
            file_name="Nota_Pesanan_Customer.pdf",
            mime="application/pdf",
        )
    else:
        st.info("Belum ada data pesanan customer.")