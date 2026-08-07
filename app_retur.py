from datetime import datetime
from io import BytesIO
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# ==========================================
# KONFIGURASI HALAMAN & KONEKSI SUPABASE
# ==========================================
st.set_page_config(
    page_title="Sistem Manajemen Retur - Toserba Nurja Berkah",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inisialisasi Koneksi Supabase dari st.secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")


@st.cache_resource
def init_connection():
  if not SUPABASE_URL or not SUPABASE_KEY:
    return None
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

# ==========================================
# TEMA & KUSTOMISASI CSS
# ==========================================
st.sidebar.title("⚙️ Pengaturan & Navigasi")
theme_mode = st.sidebar.radio(
    "Pilih Tema Tampilan", ["Light Mode", "Dark Mode"], index=0
)

# Styling CSS dinamis
if theme_mode == "Dark Mode":
  bg_color = "#0e1117"
  text_color = "#fafafa"
  card_bg = "#262730"
  border_color = "#41424c"
else:
  bg_color = "#ffffff"
  text_color = "#31333f"
  card_bg = "#f0f2f6"
  border_color = "#d1d5db"

st.markdown(
    f"""
    <style>
    .main {{
        background-color: {bg_color};
        color: {text_color};
    }}
    .metric-card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# FUNGSI DATABASE (SUPABASE)
# ==========================================
def fetch_data(table_name):
  if not supabase:
    st.error("Koneksi Supabase belum dikonfigurasi di st.secrets!")
    return pd.DataFrame()
  try:
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)
  except Exception as e:
    st.error(f"Gagal mengambil data dari {table_name}: {e}")
    return pd.DataFrame()


def insert_data(table_name, data):
  try:
    response = supabase.table(table_name).insert(data).execute()
    return True, response.data
  except Exception as e:
    return False, str(e)


def update_data(table_name, record_id, data):
  try:
    response = (
        supabase.table(table_name).update(data).eq("id", record_id).execute()
    )
    return True, response.data
  except Exception as e:
    return False, str(e)


def delete_data(table_name, record_id):
  try:
    supabase.table(table_name).delete().eq("id", record_id).execute()
    return True, ""
  except Exception as e:
    return False, str(e)


# ==========================================
# SIDEBAR MENU
# ==========================================
menu = st.sidebar.selectbox(
    "Pilih Menu",
    [
        "Dashboard & Analitik",
        "Input Data Retur",
        "Manajemen Retur",
        "Manajemen Supplier",
    ],
)

# ==========================================
# MENU 1: DASHBOARD & ANALITIK
# ==========================================
if menu == "Dashboard & Analitik":
  st.title("📊 Dashboard Manajemen Retur")
  st.markdown("### Toserba Nurja Berkah - Probolinggo")

  df_retur = fetch_data("barang_retur")
  df_supplier = fetch_data("supplier")

  if not df_retur.empty:
    total_retur = len(df_retur)
    pending_retur = (
        len(df_retur[df_retur["status"] == "Pending"])
        if "status" in df_retur.columns
        else 0
    )
    selesai_retur = (
        len(df_retur[df_retur["status"] == "Selesai"])
        if "status" in df_retur.columns
        else total_retur
    )
    total_nominal = (
        df_retur["total_harga"].sum()
        if "total_harga" in df_retur.columns
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
      st.markdown(
          f"""<div class='metric-card'><h4>Total Retur</h4><h2>{total_retur}</h2></div>""",
          unsafe_allow_html=True,
      )
    with col2:
      st.markdown(
          f"""<div class='metric-card'><h4>Pending</h4><h2>{pending_retur}</h2></div>""",
          unsafe_allow_html=True,
      )
    with col3:
      st.markdown(
          f"""<div class='metric-card'><h4>Selesai</h4><h2>{selesai_retur}</h2></div>""",
          unsafe_allow_html=True,
      )
    with col4:
      st.markdown(
          f"""<div class='metric-card'><h4>Total Nominal</h4><h2>Rp {total_nominal:,.0f}</h2></div>""",
          unsafe_allow_html=True,
      )

    st.markdown("---")

    # Grafik Tren / Kategori Retur menggunakan Plotly
    if "tanggal" in df_retur.columns:
      df_retur["tanggal"] = pd.to_datetime(
          df_retur["tanggal"], errors="coerce"
      )
      df_grouped = (
          df_retur.groupby(df_retur["tanggal"].dt.date)
          .size()
          .reset_index(name="jumlah")
      )
      fig = px.line(
          df_grouped,
          x="tanggal",
          y="jumlah",
          title="Tren Jumlah Retur Barang Harian",
          markers=True,
      )
      fig.update_layout(
          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
      )
      st.plotly_chart(fig, use_container_width=True)
  else:
    st.info("Belum ada data retur yang tercatat dalam sistem.")

# ==========================================
# MENU 2: INPUT DATA RETUR
# ==========================================
elif menu == "Input Data Retur":
  st.title("📝 Input Data Retur Barang")

  df_supplier = fetch_data("supplier")
  supplier_list = (
      df_supplier["nama_supplier"].tolist() if not df_supplier.empty else []
  )

  with st.form("form_input_retur"):
    col1, col2 = st.columns(2)
    with col1:
      tanggal = st.date_input("Tanggal Retur", datetime.now())
      supplier = st.selectbox("Pilih Supplier", supplier_list)
      nama_barang = st.text_input("Nama Barang")
    with col2:
      variant = st.text_input("Varian / Ukuran")
      jumlah = st.number_input("Jumlah Retur", min_value=1, value=1)
      harga_satuan = st.number_input(
          "Harga Satuan (Rp)", min_value=0.0, value=0.0, step=1000.0
      )

    keterangan = st.text_area(
        "Keterangan / Alasan Retur (Contoh: Expired, Rusak)"
    )
    submit = st.form_submit_button("Simpan Data Retur")

    if submit:
      if not nama_barang or not supplier:
        st.warning("Nama barang dan supplier wajib diisi!")
      else:
        total_harga = jumlah * harga_satuan
        data_to_insert = {
            "tanggal": str(tanggal),
            "supplier": supplier,
            "nama_barang": nama_barang,
            "variant": variant,
            "jumlah": int(jumlah),
            "harga_satuan": float(harga_satuan),
            "total_harga": float(total_harga),
            "keterangan": keterangan,
            "status": "Pending",
        }
        success, res = insert_data("barang_retur", data_to_insert)
        if success:
          st.success("Data retur berhasil disimpan ke sistem!")
        else:
          st.error(f"Gagal menyimpan data: {res}")

# ==========================================
# MENU 3: MANAJEMEN RETUR
# ==========================================
elif menu == "Manajemen Retur":
  st.title("📋 Kelola Data Retur")

  df_retur = fetch_data("barang_retur")
  if not df_retur.empty:
    st.dataframe(df_retur, use_container_width=True)

    st.markdown("### Update atau Hapus Data Retur")
    selected_id = st.selectbox(
        "Pilih ID Retur yang akan dikelola", df_retur["id"].tolist()
    )

    selected_row = df_retur[df_retur["id"] == selected_id].iloc[0]

    with st.form("form_edit_retur"):
      new_status = st.selectbox(
          "Status Retur",
          ["Pending", "Proses", "Selesai"],
          index=["Pending", "Proses", "Selesai"].index(
              selected_row.get("status", "Pending")
          ),
      )
      col1, col2 = st.columns(2)
      with col1:
        btn_update = st.form_submit_button("Perbarui Status")
      with col2:
        btn_delete = st.form_submit_button("Hapus Data Ini")

      if btn_update:
        success, err = update_data(
            "barang_retur", selected_id, {"status": new_status}
        )
        if success:
          st.success("Status retur berhasil diperbarui!")
          st.rerun()
        else:
          st.error(f"Gagal memperbarui: {err}")

      if btn_delete:
        success, err = delete_data("barang_retur", selected_id)
        if success:
          st.success("Data retur berhasil dihapus!")
          st.rerun()
        else:
          st.error(f"Gagal menghapus: {err}")
  else:
    st.info("Belum ada data retur.")

# ==========================================
# MENU 4: MANAJEMEN SUPPLIER
# ==========================================
elif menu == "Manajemen Supplier":
  st.title("🏢 Manajemen Data Supplier")

  with st.form("form_supplier"):
    st.sub_header = "Tambah Supplier Baru"
    nama_supplier = st.text_input("Nama Supplier / PT")
    kontak = st.text_input("Nomor Telepon / Kontak")
    status_pkp = st.selectbox("Status Pajak", ["Non-PKP", "PKP"])
    submit_sup = st.form_submit_button("Simpan Supplier")

    if submit_sup:
      if not nama_supplier:
        st.warning("Nama supplier wajib diisi!")
      else:
        data_sup = {
            "nama_supplier": nama_supplier,
            "kontak": kontak,
            "status_pkp": status_pkp,
        }
        success, res = insert_data("supplier", data_sup)
        if success:
          st.success("Supplier berhasil ditambahkan!")
          st.rerun()
        else:
          st.error(f"Gagal menyimpan supplier: {res}")

  st.markdown("---")
  st.subheader("Daftar Supplier Terdaftar")
  df_supplier = fetch_data("supplier")
  if not df_supplier.empty:
    st.dataframe(df_supplier, use_container_width=True)
  else:
    st.info("Belum ada data supplier.")
