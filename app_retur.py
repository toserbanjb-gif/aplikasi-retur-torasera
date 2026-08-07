import datetime
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import streamlit as st
from supabase import create_client

# ==========================================
# KONFIGURASI & KONEKSI
# ==========================================
st.set_page_config(page_title="NURJA BERKAH - Admin Gudang", page_icon="🏢", layout="wide")

SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

DAFTAR_SUPPLIER = [
    "PT ARTABOGA (Hanif)", "PT ARTA DWITUNGGAL ABADI (Febri)", "PT CIPTA NIAGA SEMESTA",
    "UD KENCONO WUNGGU (Opium)", "CV PUMA UTAMA MAKMUR ARTARIA", "PT Dinamika Daya Segara",
    "PT INDOMARCO ADI PRIMA", "CV KARTIKA JAYA MAKMUR", "PT Borwita Citra Prima (Listin)",
    "Yakult", "PT SUMBER BARU NIAGA (Tomi)", "PT Unirama Duta Niaga (Amru)",
    "PT SEMESTANUSTRA DISTRINDO (Imron)", "PT Eka Artha Buana Darmawan (Nestle)",
    "Jaya Subur", "CV SINAR TERANG (Gontor)"
]

# ==========================================
# FUNGSI DATA
# ==========================================
def ambil_data_retur(filter_supplier="SEMUA SUPPLIER", filter_status="SEMUA STATUS", cari=""):
    try:
        response = supabase.table("barang_retur").select("*").execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty and filter_supplier != "SEMUA SUPPLIER":
            df = df[df["supplier"] == filter_supplier]
        if not df.empty and filter_status != "SEMUA STATUS":
            df = df[df["status"] == filter_status]
        return df
    except Exception:
        return pd.DataFrame()

def ambil_data_supplier():
    try:
        response = supabase.table("data_supplier").select("*").execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        if not df.empty:
            # KONVERSI TIPE DATA UNTUK MENGHINDARI ERROR STREAMLIT
            df['tagihan'] = pd.to_numeric(df['tagihan'], errors='coerce').fillna(0.0)
            df['no_urut'] = pd.to_numeric(df['no_urut'], errors='coerce').fillna(1).astype(int)
            df['jatuh_tempo'] = pd.to_datetime(df['jatuh_tempo'], errors='coerce').dt.date
        return df
    except Exception:
        return pd.DataFrame()

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown("## 🏢 **NURJA BERKAH**")
menu = st.sidebar.radio("Menu Utama", ["🏠 Home", "📦 Input Retur", "📋 List Retur", "🏢 Data Supplier", "📊 Laporan", "⚙️ Pengaturan"])

# ==========================================
# HALAMAN
# ==========================================
if menu == "🏠 Home":
    st.markdown("## Selamat Datang")
    df_r = ambil_data_retur()
    df_s = ambil_data_supplier()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Retur", len(df_r))
    c2.metric("Supplier", len(df_s))
    c3.metric("Pending", len(df_r[df_r['status'] == 'Pengajuan']) if not df_r.empty else 0)

elif menu == "🏢 Data Supplier":
    st.markdown("## 🏢 Manajemen Data Supplier")
    df_supplier = ambil_data_supplier()
    
    if not df_supplier.empty:
        edited_df = st.data_editor(
            df_supplier,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "no_urut": st.column_config.NumberColumn("No Urut", min_value=1),
                "tagihan": st.column_config.NumberColumn("Tagihan", format="Rp %d"),
                "jatuh_tempo": st.column_config.DateColumn("Jatuh Tempo"),
                "jenis_pendaftaran": st.column_config.SelectboxColumn(options=["PKP", "Non-PKP"]),
                "sistem_pembayaran": st.column_config.SelectboxColumn(options=["Transfer", "Kredit", "Tunai"]),
            },
            hide_index=True, use_container_width=True, key="ed_supp"
        )
        
        if st.button("💾 Simpan Perubahan Supplier"):
            for _, row in edited_df.iterrows():
                supabase.table("data_supplier").update({
                    "no_urut": int(row["no_urut"]),
                    "tagihan": float(row["tagihan"]),
                    "jenis_pendaftaran": row["jenis_pendaftaran"],
                    "sistem_pembayaran": row["sistem_pembayaran"],
                    "jatuh_tempo": str(row["jatuh_tempo"])
                }).eq("id", int(row["id"])).execute()
            st.success("Data diperbarui!")
            st.rerun()

elif menu == "📦 Input Retur":
    st.markdown("## 📦 Input Retur")
    with st.form("f_retur"):
        k = st.text_input("Kode")
        n = st.text_input("Nama Barang")
        q = st.number_input("Qty", 1)
        s = st.selectbox("Supplier", DAFTAR_SUPPLIER)
        if st.form_submit_button("Simpan"):
            supabase.table("barang_retur").insert({"kode":k, "nama":n, "qty":q, "supplier":s, "status":"Pengajuan"}).execute()
            st.success("Tersimpan!")

elif menu == "📋 List Retur":
    st.markdown("## 📋 List Retur")
    df = ambil_data_retur()
    if not df.empty:
        st.data_editor(df, hide_index=True, use_container_width=True)

elif menu == "⚙️ Pengaturan":
    st.markdown("## ⚙️ Pengaturan")
    st.write("Sistem Admin Gudang Terhubung ke Database.")
