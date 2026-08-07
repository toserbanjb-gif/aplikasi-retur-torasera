import datetime
from io import BytesIO
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
        if cari:
            kw = cari.lower()
            df = df[
                df["nama_supplier"].astype(str).str.lower().str.contains(kw) |
                df["jenis_pajak"].astype(str).str.lower().str.contains(kw) |
                df["sistem_bayar"].astype(str).str.lower().str.contains(kw)
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
        tgl_jt_str = str(row.get("jatuh_tempo", ""))
        try:
            tgl_jt = datetime.datetime.strptime(tgl_jt_str, "%Y-%m-%d").date()
            selisih = (tgl_jt - hari_ini).days
            if selisih < 0:
                notif_jatuh_tempo.append(f"🔴 **{row['nama_supplier']}** sudah **JATUH TEMPO** sejak {abs(selisih)} hari lalu!")
            elif selisih <= 3:
                notif_jatuh_tempo.append(f"🟡 **{row['nama_supplier']}** jatuh tempo dalam **{selisih} hari** ({tgl_jt_str}).")
        except ValueError:
            pass

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
        .stApp { background-color: #0F172A; color: #F8FAFC; }
        [data-testid="stSidebar"] { background-color: #1E293B; padding-top: 1rem; }
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label { color: #F8FAFC !important; }
        h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; }
        p, span, label { color: #E2E8F0; }
        .stButton button[kind="primary"] { background-color: #2563EB; color: white; border-radius: 8px; font-weight: 600; border: none; }
        .stButton button[kind="primary"]:hover { background-color: #1D4ED8; }
        </style>
    """, unsafe_allow_html=True)
    plotly_template = "plotly_dark"
else:
    st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; color: #0F172A; }
        [data-testid="stSidebar"] { background-color: #0F172A; padding-top: 1rem; }
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label { color: #E2E8F0 !important; }
        h1, h2, h3, h4, h5, h6 { color: #0F172A !important; }
        p, span, label { color: #334155; }
        .stButton button[kind="primary"] { background-color: #2563EB; color: white; border-radius: 8px; font-weight: 600; border: none; }
        .stButton button[kind="primary"]:hover { background-color: #1D4ED8; }
        </style>
    """, unsafe_allow_html=True)
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
    "EGIZ UMKM (Ibu Riz)", "UD Mentari Jaya Putra", "AIRA", "PT KIAN RAGAM DISTRIBUTOR", "OPIK PUTRA SNACK",
    "PT PRAKARSA JAYA SENTOSA", "HELLO (Memenuhi Selera Anda)", "HASAN MEJA", "PT CAMPINA ICE CREAM INDUSTRY",
    "Yakult", "PT LUKINDARI PERMATA", "PT PARIMAS BOGA RAYA", "CV NUGRAHENI KARTIKA SARI DRINGU", "AZKA BAROKAH",
    "REJEKI JAYA", "DWIKARYA INDONESIA MANDIRI", "PT GOLDEN AICE", "BERKAH HS", "PT Mitra Pharmasi Jaya",
    "INDOWANGI PARFUM", "CV Argo Bentar Gemilang", "UD ANUGERAH JAYA PROBOLINGGO", "PT SUKANDA DJAYA",
    "PT ULTRAJAYA MILK INDUSTRI & TRADING CO. TBK", "Bulog Indonesia", "UD HARIS JAYA PROBOLINGGO", "Jaya Subur",
    "PADMATIRTA", "PT PABRIK MINYAK PERNIAGA DAN INDUSTRI IKAN DORANG", "MARGA NUSARAYA"
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
# MENU 4: DATA SUPPLIER
# ==========================================
if menu_pilihan == "🏢 Data Supplier":
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
                        "no_urut": s_nourut,
                        "nama_supplier": s_nama,
                        "tagihan": s_tagihan,
                        "jenis_pajak": s_pajak,
                        "sistem_bayar": s_bayar,
                        "jatuh_tempo": str(s_jatuhtempo)
                    }
                    supabase.table("data_supplier").insert(payload_sup).execute()
                    st.success("Data supplier berhasil disimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan ke database: {e}")

    st.divider()
    cari_sup = st.text_input("🔍 Cari Supplier (Nama / Pajak / Sistem Bayar)")
    df_supplier_view = ambil_data_supplier(cari_sup)

    if not df_supplier_view.empty:
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
                    st.info("Tidak ada perubahan data yang terdeteksi.")
        with col_s2:
            if st.button("🗑️ Hapus Supplier Terpilih", type="secondary", use_container_width=True):
                if not selected_sup_ids:
                    st.warning("Pilih minimal satu ID supplier yang ingin dihapus!")
                else:
                    for sid in selected_sup_ids:
                        try:
                            supabase.table("data_supplier").delete().eq("id", int(float(str(sid)))).execute()
                        except (ValueError, TypeError):
                            continue
                    st.success("Supplier terpilih berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada data supplier yang tersimpan.")

# ==========================================
# MENU LAINNYA (HOME, INPUT RETUR, LIST RETUR, LAPORAN, PENGATURAN)
# ==========================================
elif menu_pilihan == "🏠 Home":
    st.markdown("## 🏠 Halaman Utama Dashboard")
    st.markdown("Selamat datang di sistem manajemen retur dan supplier Toserba Nurja Berkah.")
    
    df_home = ambil_data_retur()
    col_h1, col_h2, col_h3 = st.columns(3)
    col_h1.metric("Total Barang Retur", f"{len(df_home)} Item")
    col_h2.metric("Total Supplier Terdaftar", f"{len(df_sup_notif)} Supplier")
    col_h3.metric("Total Nilai Retur", f"Rp {df_home['total'].sum() if not df_home.empty else 0:,.0f}")

elif menu_pilihan in ["📦 Input Retur", "📋 List Retur"]:
    st.markdown(f"## {menu_pilihan}")
    st.info("Menu retur barang aktif dan terintegrasi dengan database utama.")
    df_retur_all = ambil_data_retur()
    st.dataframe(df_retur_all, use_container_width=True)

elif menu_pilihan == "📊 Laporan":
    st.markdown("## 📊 Laporan Analitik")
    df_lap = ambil_data_retur()
    if not df_lap.empty and "tgl_input" in df_lap.columns:
        df_chart = df_lap.groupby("tgl_input")["total"].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_chart['tgl_input'], y=df_chart['total'], mode='lines+markers', line=dict(color="#2563EB", width=3)))
        fig.update_layout(title="Grafik Total Nilai Retur", xaxis_title="Tanggal", yaxis_title="Total (Rp)", template=plotly_template)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data untuk laporan.")

elif menu_pilihan == "⚙️ Pengaturan":
    st.markdown("## ⚙️ Pengaturan Sistem")
    st.write("Kelola konfigurasi aplikasi dan koneksi Supabase Anda di sini.")
