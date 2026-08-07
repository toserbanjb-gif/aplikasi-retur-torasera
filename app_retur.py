import datetime
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import streamlit as st
from supabase import create_client, Client

# ==========================================
# KONFIGURASI KONEKSI SUPABASE & HALAMAN
# ==========================================
st.set_page_config(
    page_title="Sistem Manajemen Retur & Supplier",
    page_icon="🏢",
    layout="wide"
)

# Ambil kredensial dari st.secrets (pastikan sudah diset di Streamlit Cloud)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "URL_SUPABASE_ANDA")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "KEY_SUPABASE_ANDA")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Daftar Supplier Statis/Default
DAFTAR_SUPPLIER = [
    "PT ARTABOGA (Hanif)",
    "PT ARTA DWITUNGGAL ABADI (Febri)",
    "PT CIPTA NIAGA SEMESTA",
    "UD KENCONO WUNGGU (Opium)",
    "CV PUMA UTAMA MAKMUR ARTARIA",
    "PT Dinamika Daya Segara",
    "PT INDOMARCO ADI PRIMA",
    "CV KARTIKA JAYA MAKMUR",
    "PT Borwita Citra Prima (Listin)",
    "Yakult",
    "PT SUMBER BARU NIAGA (Tomi)",
    "PT Unirama Duta Niaga (Amru)",
    "PT SEMESTANUSTRA DISTRINDO (Imron)",
    "PT Eka Artha Buana Darmawan (Nestle)",
    "Jaya Subur",
    "CV SINAR TERANG (Gontor)"
]

# ==========================================
# FUNGSI HELPER / DATABASE
# ==========================================
def ambil_data_retur(filter_supplier="SEMUA SUPPLIER", filter_status="SEMUA STATUS", cari=""):
    try:
        query = supabase.table("barang_retur").select("*")
        if filter_supplier != "SEMUA SUPPLIER":
            query = query.eq("supplier", filter_supplier)
        if filter_status != "SEMUA STATUS":
            query = query.eq("status", filter_status)
        
        response = query.execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if cari and not df.empty:
            mask = (
                df["kode"].astype(str).str.contains(cari, case=False, na=False) |
                df["nama"].astype(str).str.contains(cari, case=False, na=False) |
                df["ket"].astype(str).str.contains(cari, case=False, na=False)
            )
            df = df[mask]
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data retur: {e}")
        return pd.DataFrame()

def ambil_data_supplier():
    try:
        response = supabase.table("data_supplier").select("*").execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # Pastikan kolom tagihan bertipe numerik
        if 'tagihan' in df.columns:
            df['tagihan'] = pd.to_numeric(df['tagihan'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data supplier: {e}")
        return pd.DataFrame()

def generate_pdf_retur_custom(df, nama_supplier):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.HexColor('#1f2937')
    )
    
    elements.append(Paragraph(f"<b>LAPORAN RETUR BARANG</b>", title_style))
    elements.append(Paragraph(f"Supplier: <b>{nama_supplier}</b> | Tanggal Cetak: {datetime.date.today()}", ParagraphStyle('Sub', alignment=1, fontSize=10, textColor=colors.gray)))
    elements.append(Spacer(1, 15))
    
    table_data = [["No", "Kode / SKU", "Nama Barang", "Qty", "HPP", "Total", "Ket", "ED", "Status"]]
    for idx, row in enumerate(df.itertuples(), 1):
        table_data.append([
            str(idx),
            str(getattr(row, 'kode', '')),
            str(getattr(row, 'nama', '')),
            str(getattr(row, 'qty', 0)),
            f"Rp {getattr(row, 'hpp', 0):,.0f}",
            f"Rp {getattr(row, 'total', 0):,.0f}",
            str(getattr(row, 'ket', '')),
            str(getattr(row, 'ed', '')),
            str(getattr(row, 'status', ''))
        ])
        
    t = Table(table_data, colWidths=[30, 80, 150, 35, 60, 75, 45, 60, 55])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9fafb')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# SIDEBAR / NAVIGASI UTAMA
# ==========================================
st.sidebar.markdown("## 🏢 **NURJA BERKAH**")
st.sidebar.markdown("<p style='font-size: 12px; color: gray; margin-top:-10px;'>Belanja Lengkap, Keluarga Bahagia</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu_pilihan = st.sidebar.radio(
    "Menu Utama",
    ["🏠 Home", "📦 Input Retur", "📋 List Retur", "🏢 Data Supplier", "📊 Laporan", "⚙️ Pengaturan"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size: 11px; text-align: center; color: gray;'>Admin Gudang v3.2</p>", unsafe_allow_html=True)

# ==========================================
# KONTEN HALAMAN: HOME
# ==========================================
if menu_pilihan == "🏠 Home":
    st.markdown("## 🏠 Selamat Datang di Sistem Manajemen Retur & Supplier")
    st.markdown("Gunakan menu navigasi di sebelah kiri untuk mengelola input retur barang, memantau daftar status retur, mengatur data supplier, serta mencetak laporan PDF.")
    
    col_h1, col_h2, col_h3 = st.columns(3)
    df_r_home = ambil_data_retur()
    df_s_home = ambil_data_supplier()
    
    with col_h1:
        st.metric("Total Data Retur", len(df_r_home))
    with col_h2:
        st.metric("Total Supplier Terdaftar", len(df_s_home))
    with col_h3:
        pending_retur = len(df_r_home[df_r_home['status'] == 'Pengajuan']) if not df_r_home.empty else 0
        st.metric("Retur Pending (Pengajuan)", pending_retur)

# ==========================================
# KONTEN HALAMAN: INPUT RETUR
# ==========================================
elif menu_pilihan == "📦 Input Retur":
    st.markdown("## 📦 Input Data Retur Baru")
    st.markdown("<p style='margin-top: -10px;'>Formulir pencatatan barang retur gudang ke supplier.</p>", unsafe_allow_html=True)
    
    with st.form("form_input_retur"):
        c1, c2 = st.columns(2)
        with c1:
            inp_kode = st.text_input("Kode Barcode / SKU")
            inp_nama = st.text_input("Nama Barang")
            inp_qty = st.number_input("Qty Retur", min_value=1, value=1)
            inp_hpp = st.number_input("HPP (Rp)", min_value=0.0, format="%.2f")
        with c2:
            inp_ket = st.selectbox("Keterangan Retur", ["ED", "Rusak", "Salah PO", "Lebih Bayar", "Lainnya"])
            inp_ed = st.date_input("Tanggal ED (Expired Date)", value=datetime.date.today())
            inp_supplier = st.selectbox("Pilih Supplier", DAFTAR_SUPPLIER)
            inp_status = st.selectbox("Status Retur", ["Pengajuan", "Sedang Diproses", "Sukses"])
            
        submitted = st.form_submit_button("💾 Simpan Retur Baru", type="primary")
        if submitted:
            if not inp_kode or not inp_nama:
                st.warning("Kode Barcode dan Nama Barang wajib diisi!")
            else:
                total_val = inp_qty * inp_hpp
                try:
                    supabase.table("barang_retur").insert({
                        "kode": inp_kode,
                        "nama": inp_nama,
                        "qty": int(inp_qty),
                        "hpp": float(inp_hpp),
                        "total": float(total_val),
                        "ket": inp_ket,
                        "ed": str(inp_ed),
                        "supplier": inp_supplier,
                        "status": inp_status,
                        "tgl_input": str(datetime.date.today())
                    }).execute()
                    st.success("Data retur berhasil disimpan ke database!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data: {e}")

# ==========================================
# KONTEN HALAMAN: LIST RETUR & EDIT STATUS
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
        if "ed" in df_retur_view.columns:
            df_retur_view["ed"] = pd.to_datetime(df_retur_view["ed"], errors="coerce").dt.date

        pdf_bytes = generate_pdf_retur_custom(df_retur_view, pilih_sup_filter)
        st.download_button(
            label=f"📥 Download Laporan PDF ({pilih_sup_filter})",
            data=pdf_bytes,
            file_name=f"Laporan_Retur_{pilih_sup_filter.replace(' ', '_')}_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("### ✏️ Edit Data Retur")
        st.markdown("<p style='font-size: 13px; color: gray;'>Ubah data pada tabel di bawah. Jika mengubah status menjadi <b>Sukses</b>, Anda akan diminta mengonfirmasi kelengkapan Qty retur.</p>", unsafe_allow_html=True)

        edited_df_retur = st.data_editor(
            df_retur_view,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small", disabled=True),
                "kode": st.column_config.TextColumn("Kode Barcode/SKU", width="medium"),
                "nama": st.column_config.TextColumn("Nama Barang", width="large"),
                "qty": st.column_config.NumberColumn("Qty", min_value=1, width="small"),
                "hpp": st.column_config.NumberColumn("HPP (Rp)", format="Rp %d", width="medium"),
                "total": st.column_config.NumberColumn("Total (Rp)", format="Rp %d", width="medium", disabled=True),
                "ket": st.column_config.SelectboxColumn("Keterangan", options=["ED", "Rusak", "Salah PO", "Lebih Bayar", "Lainnya"], required=True, width="small"),
                "ed": st.column_config.DateColumn("Tanggal ED", format="YYYY-MM-DD", width="small"),
                "supplier": st.column_config.SelectboxColumn("Supplier", options=DAFTAR_SUPPLIER, required=True, width="large"),
                "status": st.column_config.SelectboxColumn("Status", options=["Pengajuan", "Sedang Diproses", "Sukses"], required=True, width="medium"),
                "tgl_input": st.column_config.TextColumn("Tanggal Input", width="small", disabled=True),
            },
            disabled=["id", "total", "tgl_input"],
            hide_index=True,
            use_container_width=True,
            key="editor_tabel_retur_v4"
        )

        # Deteksi item yang statusnya diubah menjadi 'Sukses'
        item_proses_sukses = []
        for _, row in edited_df_retur.iterrows():
            orig_row = df_retur_view.loc[df_retur_view["id"] == row["id"]]
            if not orig_row.empty:
                orig_status = str(orig_row.iloc[0]["status"])
                if str(row["status"]) == "Sukses" and orig_status != "Sukses":
                    item_proses_sukses.append(row)

        detail_retur_parsial = {}
        if item_proses_sukses:
            st.warning("⚠️ **Konfirmasi Retur Sukses** Terdeteksi perubahan status ke 'Sukses'. Silakan isi rincian penerimaan retur di bawah ini:")
            
            for item in item_proses_sukses:
                st.write(f"**[{item['kode']}] {item['nama']}** — Total Qty Diretur: **{int(item['qty'])}**")
                c_opt, c_qty = st.columns([2, 2])
                with c_opt:
                    pilihan_retur = st.radio(
                        f"Status Pelunasan Retur (ID: {item['id']})",
                        options=["Sepenuhnya Berhasil", "Belum Sepenuhnya"],
                        key=f"radio_sukses_{item['id']}"
                    )
                
                qty_diterima = int(item['qty'])
                if pilihan_retur == "Belum Sepenuhnya":
                    with c_qty:
                        qty_diterima = st.number_input(
                            f"Qty Berhasil Diretur (Maks {int(item['qty'])-1})",
                            min_value=1,
                            max_value=int(item['qty']) - 1,
                            value=1,
                            key=f"qty_diterima_{item['id']}"
                        )
                
                detail_retur_parsial[item['id']] = {
                    "tipe": pilihan_retur,
                    "qty_berhasil": qty_diterima,
                    "qty_sisa": int(item['qty']) - qty_diterima
                }
            st.markdown("---")

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
                        rid = int(row["id"])
                        new_qty = float(row["qty"])
                        new_hpp = float(row["hpp"])
                        
                        orig_ed = str(orig["ed"]) if pd.notna(orig["ed"]) else ""
                        new_ed = str(row["ed"]) if pd.notna(row["ed"]) else ""

                        is_changed = (
                            str(row["kode"]) != str(orig["kode"]) or
                            str(row["nama"]) != str(orig["nama"]) or
                            new_qty != float(orig["qty"]) or
                            new_hpp != float(orig["hpp"]) or
                            str(row["ket"]) != str(orig["ket"]) or
                            new_ed != orig_ed or
                            str(row["supplier"]) != str(orig["supplier"]) or
                            str(row["status"]) != str(orig["status"])
                        )

                        if is_changed:
                            if rid in detail_retur_parsial:
                                info_parsial = detail_retur_parsial[rid]
                                
                                if info_parsial["tipe"] == "Belum Sepenuhnya":
                                    qty_sukses = info_parsial["qty_berhasil"]
                                    qty_sisa = info_parsial["qty_sisa"]
                                    
                                    # Update baris lama menjadi sukses dengan qty yang berhasil
                                    supabase.table("barang_retur").update({
                                        "kode": str(row["kode"]),
                                        "nama": str(row["nama"]),
                                        "qty": qty_sukses,
                                        "hpp": new_hpp,
                                        "total": qty_sukses * new_hpp,
                                        "ket": str(row["ket"]),
                                        "ed": new_ed,
                                        "supplier": str(row["supplier"]),
                                        "status": "Sukses"
                                    }).eq("id", rid).execute()
                                    
                                    # Buat baris baru otomatis untuk sisa retur (status: Pengajuan)
                                    supabase.table("barang_retur").insert({
                                        "kode": str(row["kode"]),
                                        "nama": str(row["nama"]),
                                        "qty": qty_sisa,
                                        "hpp": new_hpp,
                                        "total": qty_sisa * new_hpp,
                                        "ket": str(row["ket"]),
                                        "ed": new_ed,
                                        "supplier": str(row["supplier"]),
                                        "status": "Pengajuan",
                                        "tgl_input": str(datetime.date.today())
                                    }).execute()

                                else:
                                    supabase.table("barang_retur").update({
                                        "kode": str(row["kode"]),
                                        "nama": str(row["nama"]),
                                        "qty": int(new_qty),
                                        "hpp": new_hpp,
                                        "total": new_qty * new_hpp,
                                        "ket": str(row["ket"]),
                                        "ed": new_ed,
                                        "supplier": str(row["supplier"]),
                                        "status": "Sukses"
                                    }).eq("id", rid).execute()
                            else:
                                supabase.table("barang_retur").update({
                                    "kode": str(row["kode"]),
                                    "nama": str(row["nama"]),
                                    "qty": int(new_qty),
                                    "hpp": new_hpp,
                                    "total": new_qty * new_hpp,
                                    "ket": str(row["ket"]),
                                    "ed": new_ed,
                                    "supplier": str(row["supplier"]),
                                    "status": str(row["status"])
                                }).eq("id", rid).execute()

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

# ==========================================
# KONTEN HALAMAN: DATA SUPPLIER
# ==========================================
elif menu_pilihan == "🏢 Data Supplier":
    st.markdown("## 🏢 Manajemen Data Supplier")
    st.markdown("<p style='margin-top: -10px;'>Kelola informasi supplier, tagihan, jenis pendaftaran, dan sistem pembayaran.</p>", unsafe_allow_html=True)
    
    df_supplier = ambil_data_supplier()
    
    if not df_supplier.empty:
        edited_df_supplier = st.data_editor(
            df_supplier,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small", disabled=True),
                "no_urut": st.column_config.NumberColumn("No Urut", width="small"),
                "nama_supplier": st.column_config.TextColumn("Nama Supplier", width="large"),
                "tagihan": st.column_config.NumberColumn("Tagihan", format="Rp %d", width="medium"),
                "jenis_pendaftaran": st.column_config.SelectboxColumn("Jenis Pendaftaran", options=["PKP", "Non-PKP"], width="medium"),
                "sistem_pembayaran": st.column_config.SelectboxColumn("Sistem Pembayaran", options=["Transfer", "Kredit", "Tunai"], width="medium"),
                "jatuh_tempo": st.column_config.DateColumn("Jatuh Tempo", width="medium"),
            },
            disabled=["id"],
            hide_index=True,
            use_container_width=True,
            key="editor_tabel_supplier"
        )
        
        st.markdown("### 🛠️ Aksi Data Supplier")
        list_sup_ids = df_supplier["id"].tolist()
        selected_sup_ids = st.multiselect("Pilih ID Supplier (untuk Simpan Perubahan / Hapus):", options=list_sup_ids, key="multiselect_sup_id")
        
        cs1, cs2 = st.columns(2)
        with cs1:
            if st.button("💾 Simpan Perubahan Data Supplier", type="primary", use_container_width=True):
                count_upd_supp = 0
                for _, row in edited_df_supplier.iterrows():
                    if row["id"] in selected_sup_ids:
                        try:
                            supabase.table("data_supplier").update({
                                "no_urut": int(row["no_urut"]) if pd.notna(row["no_urut"]) else 0,
                                "nama_supplier": str(row["nama_supplier"]),
                                "tagihan": float(row["tagihan"]) if pd.notna(row["tagihan"]) else 0.0,
                                "jenis_pendaftaran": str(row["jenis_pendaftaran"]),
                                "sistem_pembayaran": str(row["sistem_pembayaran"]),
                                "jatuh_tempo": str(row["jatuh_tempo"]) if pd.notna(row["jatuh_tempo"]) else None
                            }).eq("id", int(row["id"])).execute()
                            count_upd_supp += 1
                        except Exception as e:
                            st.error(f"Error pada ID {row['id']}: {e}")
                if count_upd_supp > 0:
                    st.success(f"Berhasil memperbarui {count_upd_supp} data supplier!")
                    st.rerun()
                else:
                    st.warning("Pilih minimal satu ID supplier di multiselect di atas untuk disimpan.")
        with cs2:
            if st.button("🗑️ Hapus Supplier Terpilih", type="secondary", use_container_width=True):
                if not selected_sup_ids:
                    st.warning("Pilih minimal satu ID supplier yang ingin dihapus!")
                else:
                    for sid in selected_sup_ids:
                        try:
                            supabase.table("data_supplier").delete().eq("id", int(sid)).execute()
                        except Exception as e:
                            st.error(f"Error hapus ID {sid}: {e}")
                    st.success("Data supplier terpilih berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada data supplier di database.")
        
    st.markdown("---")
    with st.expander("➕ Tambah Supplier Baru"):
        with st.form("form_tambah_supplier"):
            t_nourut = st.number_input("No Urut", value=1, min_value=1)
            t_nama = st.text_input("Nama Supplier")
            t_tagihan = st.number_input("Tagihan (Rp)", min_value=0.0, format="%.2f")
            t_jenis = st.selectbox("Jenis Pendaftaran", ["PKP", "Non-PKP"])
            t_sistem = st.selectbox("Sistem Pembayaran", ["Transfer", "Kredit", "Tunai"])
            t_jtp = st.date_input("Jatuh Tempo", value=datetime.date.today())
            
            submit_sup = st.form_submit_button("Tambah Supplier")
            if submit_sup:
                if not t_nama:
                    st.warning("Nama supplier wajib diisi!")
                else:
                    try:
                        supabase.table("data_supplier").insert({
                            "no_urut": int(t_nourut),
                            "nama_supplier": t_nama,
                            "tagihan": float(t_tagihan),
                            "jenis_pendaftaran": t_jenis,
                            "sistem_pembayaran": t_sistem,
                            "jatuh_tempo": str(t_jtp)
                        }).execute()
                        st.success("Supplier baru berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah supplier: {e}")

# ==========================================
# KONTEN HALAMAN: LAPORAN & PENGATURAN
# ==========================================
elif menu_pilihan == "📊 Laporan":
    st.markdown("## 📊 Laporan Keseluruhan Retur")
    df_lap = ambil_data_retur()
    if not df_lap.empty:
        st.dataframe(df_lap, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data laporan.")

elif menu_pilihan == "⚙️ Pengaturan":
    st.markdown("## ⚙️ Pengaturan Sistem")
    st.write("Konfigurasi koneksi database Supabase dan preferensi aplikasi gudang.")
    st.text(f"Supabase URL Terhubung: {SUPABASE_URL[:25]}...")
