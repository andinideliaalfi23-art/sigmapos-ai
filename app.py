import streamlit as st
import pandas as pd
import datetime
import hashlib
import json
import plotly.express as px

# === AI ADDITION START ===
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch
# === AI ADDITION END ===


# ==========================================
# 1. KONFIGURASI SISTEM & SECURITY
# ==========================================
st.set_page_config(page_title="SIGMA ULTIMATE v7.2", layout="wide")

# Fitur Simulasi Waktu (Global)
if 'simulated_time' not in st.session_state:
    st.session_state.simulated_time = None

def get_current_time():
    """Mengambil waktu asli atau waktu simulasi jika diaktifkan"""
    if st.session_state.simulated_time:
        return st.session_state.simulated_time
    return datetime.datetime.now()

def generate_hash(data_dict):
    keys_to_exclude = ["Hash_ID", "New_Hash", "Verification", "Hash_Lama", "Analisis", "Fraud_Status"]
    clean_data = {k: str(v) for k, v in data_dict.items() if k not in keys_to_exclude}
    data_string = json.dumps(clean_data, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()


# === AI ADDITION START ===
@st.cache_resource
def load_ai_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

caption_processor, caption_model = load_ai_model()

def generate_caption(image):
    inputs = caption_processor(image, return_tensors="pt")
    out = caption_model.generate(**inputs)
    caption = caption_processor.decode(out[0], skip_special_tokens=True)
    return caption
# === AI ADDITION END ===


if 'products_db' not in st.session_state:
    st.session_state.products_db = [
        {"name": "Gula", "price": 18000, "stok": 50, "cat": "Sembako", "img": "https://www.bing.com/th?id=OIP.XRZ9FYP234Y4ewEKg3B_QQHaGG"},
        {"name": "Tepung", "price": 12000, "stok": 40, "cat": "Sembako", "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400"},
        {"name": "Beras", "price": 15000, "stok": 100, "cat": "Sembako", "img": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400"},
        {"name": "Kopi Susu", "price": 25000, "stok": 30, "cat": "Minuman", "img": "https://tse1.mm.bing.net/th/id/OIP.BvFh1O9kn4fpJXMiYY-ICgHaHa?rs=1&pid=ImgDetMain&o=7&rm=3"}
    ]

if 'logs' not in st.session_state: st.session_state.logs = []
if 'admin_logs' not in st.session_state: st.session_state.admin_logs = []
if 'login_logs' not in st.session_state: st.session_state.login_logs = []
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'cart' not in st.session_state: st.session_state.cart = {}

# ==========================================
# 2. LOGIN PAGE
# ==========================================
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .login-header {
            font-family: 'serif';
            font-size: 45px;
            color: #001f3f; 
            text-align: center;
            margin-bottom: 30px;
            font-weight: bold;
        }
        div.stButton > button {
            background-color: #001f3f !important;
            color: white !important;
            width: 100%;
            height: 45px;
            border-radius: 5px;
        }
        .block-container {
            padding-top: 10rem;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 4, 3])

    with col2:
        with st.container(border=True): 
            st.markdown('<h1 class="login-header">POS SYSTEM</h1>', unsafe_allow_html=True)
            
            role_choice = st.selectbox("PILIH ROLE", ["Owner", "Admin", "Kasir"])
            username = st.text_input("USERNAME", placeholder="Masukkan username")
            password = st.text_input("PASSWORD", placeholder="Masukkan password", type="password")
            
            st.write("") 
            
            if st.button("LOGIN"):
                if password == "123" and username != "": 
                    log_entry = {
                        "Waktu": get_current_time().strftime("%Y-%m-%d %H:%M:%S"),
                        "User": username,
                        "Role": role_choice,
                        "Status": "SUCCESS"
                    }
                    log_entry["Hash_Lama"] = generate_hash(log_entry)
                    st.session_state.login_logs.insert(0, log_entry)

                    st.session_state.authenticated = True
                    st.session_state.role = role_choice
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
    st.stop()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title(f"👤 {st.session_state.current_user}")
    st.caption(f"Role: {st.session_state.role}")
    
    # Indikator Waktu Aktif
    current_time_display = get_current_time()
    st.info(f"🕒 Waktu Sistem:\n{current_time_display.strftime('%H:%M:%S')}")
    if st.session_state.simulated_time:
        st.warning("⚠️ Mode Simulasi Aktif")

    st.markdown("---")
    menu_options = []
    if st.session_state.role == "Kasir": menu_options = ["🛒 Cashier Portal", "📑 Data Transaksi"]
    elif st.session_state.role == "Admin": menu_options = ["⚙️ Admin Portal"]
    elif st.session_state.role == "Owner":
        menu_options = ["📊 Dashboard Ringkasan", "📈 Laporan Penjualan", "👥 Pantau Aktivitas", "🔐 Audit Log Login", "🧪 Halaman Simulasi Manipulasi"]
    menu = st.radio("MENU UTAMA", menu_options)

    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.cart = {}
        st.rerun()

# ==========================================
# ADMIN PORTAL
# ==========================================
if menu == "⚙️ Admin Portal":
    st.title("⚙️ Manajemen Stok Produk")

    # === AI ADDITION START ===
    st.subheader("🤖 AI Deteksi Barang dari Kamera")
    img_file = st.camera_input("Ambil foto barang")

    if img_file:
        image = Image.open(img_file).convert("RGB")
        caption = generate_caption(image)
        caption_clean = caption.split(",")[0].split(" of ")[-1].strip()

        st.success(f"AI mendeteksi: {caption_clean}")

        if st.button("Tambahkan ke Produk"):
            st.session_state.products_db.append({
                "name": caption_clean.title(),
                "price": 0,
                "stok": 0,
                "cat": "Lainnya",
                "img": "https://via.placeholder.com/150"
            })
            st.session_state.admin_logs.insert(0,{
                "Waktu": get_current_time().strftime("%H:%M:%S"),
                "User": st.session_state.current_user,
                "Aksi": "AI ADD",
                "Detail": caption_clean
            })
            st.success("Produk berhasil ditambahkan dari AI!")
            st.rerun()
    # === AI ADDITION END ===

    with st.expander("➕ Tambah Produk Baru", expanded=False):
        with st.form("add_p", clear_on_submit=True):
            n = st.text_input("Nama Barang")
            c = st.selectbox("Kategori", ["Sembako", "Makanan", "Minuman", "Lainnya"])
            s = st.number_input("Stok", min_value=0, step=1)
            p = st.number_input("Harga", min_value=0, step=1000, format="%d")
            img = st.text_input("URL Gambar", "https://via.placeholder.com/150")
            if st.form_submit_button("Simpan Ke Database"):
                if n:
                    st.session_state.products_db.append({"name": n, "price": int(p), "stok": s, "cat": c, "img": img})
                    st.session_state.admin_logs.insert(0, {"Waktu": get_current_time().strftime("%Y-%m-%d %H:%M"), "User": st.session_state.current_user, "Aksi": "TAMBAH", "Detail": n})
                    st.rerun()

    st.markdown("---")
    st.subheader("Daftar Produk (Edit & Hapus)")
    
    for i, prod in enumerate(st.session_state.products_db):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                st.image(prod['img'], width=80)
            with c2:
                st.write(f"**{prod['name']}** - {prod['cat']}")
                st.write(f"Harga: Rp {prod['price']:,} | Stok: {prod['stok']}")
                with st.expander(f"✏️ Edit {prod['name']}"):
                    with st.form(key=f"edit_form_{i}"):
                        new_name = st.text_input("Nama", value=prod['name'])
                        new_price = st.number_input("Harga", value=prod['price'], step=1000)
                        new_stok = st.number_input("Stok", value=prod['stok'], step=1)
                        new_cat = st.selectbox("Kategori", ["Sembako", "Makanan", "Minuman", "Lainnya"], index=["Sembako", "Makanan", "Minuman", "Lainnya"].index(prod['cat']) if prod['cat'] in ["Sembako", "Makanan", "Minuman", "Lainnya"] else 3)
                        
                        if st.form_submit_button("Simpan Perubahan"):
                            st.session_state.products_db[i]['name'] = new_name
                            st.session_state.products_db[i]['price'] = int(new_price)
                            st.session_state.products_db[i]['stok'] = int(new_stok)
                            st.session_state.products_db[i]['cat'] = new_cat
                            
                            st.session_state.admin_logs.insert(0, {
                                "Waktu": get_current_time().strftime("%Y-%m-%d %H:%M"), 
                                "User": st.session_state.current_user, 
                                "Aksi": "EDIT", 
                                "Detail": f"{prod['name']} -> {new_name}"
                            })
                            st.success("Data berhasil diupdate!")
                            st.rerun()
            with c3:
                st.write("") 
                if st.button("🗑️ Hapus", key=f"del_{i}", type="primary"):
                    deleted_name = prod['name']
                    del st.session_state.products_db[i]
                    st.session_state.admin_logs.insert(0, {
                        "Waktu": get_current_time().strftime("%Y-%m-%d %H:%M"), 
                        "User": st.session_state.current_user, 
                        "Aksi": "HAPUS", 
                        "Detail": deleted_name
                    })
                    st.rerun()

# ==========================================
# KASIR PORTAL
# ==========================================
elif menu == "🛒 Cashier Portal":
    l_col, r_col = st.columns([7, 3])
    with l_col:
        st.title("🛒 POS SIGMA")
        search = st.text_input("🔍 Cari produk...")
        tabs = st.tabs(["Semua", "Makanan", "Minuman", "Sembako"])
        for i, tab_name in enumerate(["Semua", "Makanan", "Minuman", "Sembako"]):
            with tabs[i]:
                items = st.session_state.products_db
                if tab_name != "Semua": items = [p for p in items if p.get('cat') == tab_name]
                if search: items = [p for p in items if search.lower() in p['name'].lower()]
                cols = st.columns(3)
                for idx, item in enumerate(items):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.image(item['img'], use_container_width=True)
                            st.write(f"**{item['name']}**")
                            st.caption(f"Rp {item['price']:,} | Stok: {item['stok']}")
                            if item['stok'] > 0:
                                if st.button("Pilih", key=f"sel_{tab_name}_{idx}", use_container_width=True):
                                    if item['name'] in st.session_state.cart:
                                        st.session_state.cart[item['name']]['qty'] += 1
                                    else:
                                        st.session_state.cart[item['name']] = {'price': item['price'], 'qty': 1}
                                    st.rerun()
                            else:
                                st.button("Habis", disabled=True, key=f"out_{tab_name}_{idx}", use_container_width=True)

    with r_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("🛒 Keranjang")
            total_pay = 0
            for name, info in list(st.session_state.cart.items()):
                st.write(f"**{name}**")
                st.write(f"Subtotal: Rp {info['price'] * info['qty']:,}")
                q1, q2, q3 = st.columns([1,1,1])
                if q1.button("➖", key=f"m_{name}"):
                    st.session_state.cart[name]['qty'] -= 1
                    if st.session_state.cart[name]['qty'] <= 0: del st.session_state.cart[name]
                    st.rerun()
                q2.write(f" {info['qty']} ")
                if q3.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
                total_pay += info['price'] * info['qty']
                st.divider()
            
            st.write(f"### Total: Rp {total_pay:,}")
            if st.button("💳 BAYAR", type="primary", use_container_width=True, disabled=not st.session_state.cart):
                now = get_current_time()
                trx_id = f"TRX-{now.strftime('%f%S%M%H%d')}"
                items_str = ", ".join([f"{n}({q['qty']}x)" for n, q in st.session_state.cart.items()])
                
                for cart_name, cart_info in st.session_state.cart.items():
                    qty_bought = cart_info['qty']
                    for db_prod in st.session_state.products_db:
                        if db_prod['name'] == cart_name:
                            db_prod['stok'] = max(0, db_prod['stok'] - qty_bought)
                            break

                payload = {
                    "ID": trx_id, 
                    "Waktu": now.strftime("%d/%m/%Y, %H:%M:%S"), 
                    "Timestamp": now.timestamp(), 
                    "Tanggal": now.strftime("%Y-%m-%d"), 
                    "Bulan": now.strftime("%Y-%m"),
                    "User": st.session_state.current_user, 
                    "Item": items_str, 
                    "Total": total_pay, 
                    "Status": "SUCCESS", 
                    "Security": "Normal",
                    "Fraud_Status": "Clear"
                }
                payload["Hash_ID"] = generate_hash(payload)
                st.session_state.logs.insert(0, payload)
                st.session_state.cart = {}
                st.success("Pembayaran Berhasil & Stok Berkurang!")
                st.rerun()

# ==========================================
# DATA TRANSAKSI (DENGAN LOGIKA SECURITY DINAMIS)
# ==========================================
elif menu == "📑 Data Transaksi":
    st.title("📑 Riwayat Transaksi")
    if st.session_state.logs:
        h1, h2, h3, h4, h5 = st.columns([2, 3, 1, 1, 1])
        h1.write("**ID**")
        h2.write("**Waktu**")
        h3.write("**Total**")
        h4.write("**Status**")
        h5.write("**Aksi**")
        st.divider()
        for idx, log in enumerate(st.session_state.logs):
            r1, r2, r3, r4, r5 = st.columns([2, 3, 1, 1, 1])
            r1.write(log['ID'])
            r2.write(log['Waktu'])
            r3.write(f"{log['Total']:,}")
            color = "green" if log['Status'] == "SUCCESS" else "red"
            r4.markdown(f":{color}[{log['Status']}]")
            
            if log['Status'] == "SUCCESS":
                if r5.button("Batalkan", key=f"void_{idx}"):
                    # Logika Fraud menggunakan Waktu Sistem Aktif (Simulasi)
                    now = get_current_time()
                    current_hour = now.hour
                    
                    if current_hour < 8 or current_hour >= 22:
                        fraud_score = "🚨 FRAUD TINGGI (Luar Jam Kerja)"
                        security_level = "High Alert"
                    elif log['Total'] >= 300000:
                        start_time = log.get('Timestamp', now.timestamp())
                        diff_minutes = (now.timestamp() - start_time) / 60
                        if diff_minutes > 15:
                            fraud_score = "🚨 FRAUD TINGGI (Nominal Besar & Waktu Lama)"
                            security_level = "High Alert"
                        else:
                            fraud_score = "⚠️ FRAUD RENDAH (Nominal Besar & Segera)"
                            security_level = "Warning"
                    else:
                        fraud_score = "Clear"
                        security_level = "Normal"

                    st.session_state.logs[idx]['Status'] = "VOID"
                    st.session_state.logs[idx]['Fraud_Status'] = fraud_score
                    st.session_state.logs[idx]['Security'] = security_level
                    st.rerun()
            else: 
                f_status = log.get('Fraud_Status', "Clear")
                if f_status != "Clear":
                    r5.caption(f_status)
                else:
                    r5.write("-")
    else: st.info("Kosong")

# ==========================================
# OWNER: DASHBOARD
# ==========================================
elif menu == "📊 Dashboard Ringkasan":
    st.title("📊 Ringkasan Penjualan & Grafik")
    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
        success_df = df[df['Status'] == 'SUCCESS']
        c1, c2, c3 = st.columns(3)
        c1.metric("Omzet", f"Rp {success_df['Total'].sum():,}")
        c2.metric("Trx Sukses", len(success_df))
        c3.metric("Trx Void", len(df[df['Status'] == 'VOID']))
        
        st.subheader("📈 Tren Penjualan Bulanan")
        fig = px.line(success_df.groupby('Bulan')['Total'].sum().reset_index(), x='Bulan', y='Total', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Belum ada data.")

# ==========================================
# OWNER: LAPORAN PENJUALAN
# ==========================================
elif menu == "📈 Laporan Penjualan":
    st.title("📈 Laporan Penjualan & Audit Forensik")
    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
        df['New_Hash'] = df.apply(lambda row: generate_hash(row.to_dict()), axis=1)
        
        def verify_integrity(row):
            if row['Hash_ID'] == row['New_Hash']: return "✅ Valid"
            else: return "🚨 Manipulated"
        
        df['Verifikasi'] = df.apply(verify_integrity, axis=1)
        
        t1, t2 = st.tabs(["Harian", "Bulanan"])
        with t1:
            d = st.date_input("Pilih Tanggal")
            daily_data = df[df['Tanggal'] == str(d)]
            st.dataframe(daily_data, use_container_width=True)
            
        with t2:
            m = st.selectbox("Pilih Bulan", df['Bulan'].unique() if 'Bulan' in df.columns else [])
            monthly_data = df[df['Bulan'] == m]
            st.dataframe(monthly_data, use_container_width=True)
            
        manipulated_count = len(df[df['Verifikasi'] == "🚨 Manipulated"])
        if manipulated_count > 0:
            st.error(f"PERINGATAN: Ditemukan {manipulated_count} transaksi yang datanya tidak cocok dengan Hash asli!")
        else:
            st.success("Semua data laporan valid dan terverifikasi oleh sistem Hash.")
    else:
        st.info("Belum ada data transaksi untuk ditampilkan.")

elif menu == "👥 Pantau Aktivitas":
    st.title("👥 Pantau Staff")
    st.subheader("🛒 Kinerja Kasir (Hari Ini)")
    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
        st.table(df.groupby('User')['Status'].value_counts().unstack().fillna(0))
    st.subheader("⚙️ Log Admin (Stok)")
    st.dataframe(pd.DataFrame(st.session_state.admin_logs), use_container_width=True)

# ==========================================
# AUDIT LOG LOGIN
# ==========================================
elif menu == "🔐 Audit Log Login":
    st.title("🔐 Audit Keamanan Login")
    if st.session_state.login_logs:
        audit_list = []
        for log in st.session_state.login_logs:
            current_h = generate_hash(log)
            old_h = log.get("Hash_Lama", "NONE")
            status_audit = "✅ Normal" if current_h == old_h else "🚨 TERDETEKSI MANIPULASI"
            
            audit_list.append({
                "Waktu": log["Waktu"],
                "User": log["User"],
                "Role": log["Role"],
                "Hash Lama": old_h[:15] + "...",
                "Hash Baru": current_h[:15] + "...",
                "Analisis": status_audit
            })
        st.table(pd.DataFrame(audit_list))
    else:
        st.info("Belum ada riwayat login.")

# ==========================================
# 9. HALAMAN SIMULASI MANIPULASI (+ SIMULASI WAKTU)
# ==========================================
elif menu == "🧪 Halaman Simulasi Manipulasi":
    st.title("🧪 Simulasi Keamanan")
    
    # --- FITUR: SIMULASI WAKTU ---
    st.subheader("🕒 Pengaturan Waktu (Time Simulation)")
    with st.container(border=True):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            sim_date = st.date_input("Set Tanggal Simulasi", datetime.date.today())
        with col_t2:
            sim_time = st.time_input("Set Jam Simulasi (Contoh: 23:00 untuk tes Fraud)", datetime.time(23, 0))
        
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("🚀 Aktifkan Simulasi Waktu", use_container_width=True):
            st.session_state.simulated_time = datetime.datetime.combine(sim_date, sim_time)
            st.success(f"Waktu sistem sekarang disetel ke: {st.session_state.simulated_time}")
            st.rerun()
            
        if c_btn2.button("♻️ Reset ke Waktu Asli", use_container_width=True):
            st.session_state.simulated_time = None
            st.info("Waktu sistem kembali ke waktu real-time.")
            st.rerun()

    st.divider()

    st.subheader("Manipulasi Transaksi")
    if st.session_state.logs:
        idx = st.selectbox("Pilih Data Transaksi", range(len(st.session_state.logs)))
        if st.button("HACK HARGA TRANSAKSI"):
            st.session_state.logs[idx]['Total'] = 1
            st.error("Data Berhasil Dimanipulasi!")
            
    st.divider()
    
    st.subheader("Manipulasi Log Login")
    if st.session_state.login_logs:
        idx_log = st.selectbox("Pilih Log Login", range(len(st.session_state.login_logs)))
        if st.button("HACK NAMA USER LOGIN"):
            st.session_state.login_logs[idx_log]['User'] = "HACKER_SYSTEM"
            st.error("Log Login Berhasil Dimanipulasi!")